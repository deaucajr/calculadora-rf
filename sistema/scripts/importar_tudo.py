#!/usr/bin/env python
"""
IMPORTADOR COMPLETO — FI Analytics como fonte unica.

Faz TUDO:
  1. Sincroniza BACEN (CDI + IPCA + projecoes)
  2. Lista TODOS os bonds do FI Analytics
  3. Importa fluxo de caixa de cada bond
  4. Calcula VNA PROPRIO desde a data de emissao
  5. Salva CSV no padrao brasileiro (; e virgula)
  6. Valida PU contra FI Analytics
  7. Gera relatorio de erros

Uso:
  python importar_tudo.py               # importa TUDO (todos os bonds)
  python importar_tudo.py --max 50      # importa so 50 (teste)
  python importar_tudo.py --ticker EGIEA6  # importa 1 ticker
  python importar_tudo.py --validar     # valida os que ja existem
"""
import sys
import time
import json
from datetime import date as dt_date, datetime, timedelta
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import get_required
from src.db import init_db, get_conn
from src.fi_client import get_user_bonds, calc_corporate
from src.vna_calc import calcular_vna
from src.fmt_br import SEP, fmt, fmt_pct, csv_row, csv_header, csv_write, parse_br
from src.paths import fluxos_dir, fluxos_antigo_dir
from src import sync_bacen

DELAY = 0.35  # segundos entre chamadas API


# ─── Feriados ──────────────────────────────────────────────────

def _easter(y: int) -> dt_date:
    a = y % 19; b = y // 100; c = y % 100
    d = b // 4; e = b % 4; f = (b + 8) // 25
    g = (b - f + 1) // 3; h = (19 * a + b - d - g + 15) % 30
    i = c // 4; k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return dt_date(y, month, day)

def _feriados() -> set[dt_date]:
    fer = set()
    for y in range(2001, 2051):
        p = _easter(y)
        fer |= {dt_date(y,1,1), p-timedelta(days=48), p-timedelta(days=47),
                p-timedelta(days=2), dt_date(y,4,21), dt_date(y,5,1),
                p+timedelta(days=60), dt_date(y,9,7), dt_date(y,10,12),
                dt_date(y,11,2), dt_date(y,11,15), dt_date(y,12,25)}
        if y >= 2024: fer.add(dt_date(y,11,20))
    return fer

FERIADOS = _feriados()

def _du(d0: dt_date, d1: dt_date) -> int:
    n = 0; cur = d0 + timedelta(days=1)
    while cur <= d1:
        if cur.weekday() < 5 and cur not in FERIADOS: n += 1
        cur += timedelta(days=1)
    return max(1, n)


# ─── Classificacao ─────────────────────────────────────────────

def _idx(method: str, rate: float = 0) -> str:
    m = (method or "").upper()
    if "IPCA" in m or "IGP" in m: return "IPCA"
    if "DI" in m or "CDI" in m:
        return "%CDI" if rate >= 50 else "CDI+"
    return "PRE"


# ─── Importar UM ticker ────────────────────────────────────────

def importar_ticker(ticker: str, data_calc: str | None = None,
                    yield_ref: float = 5.0) -> dict:
    """Importa 1 ticker do FI Analytics e salva CSV."""
    if data_calc is None:
        data_calc = dt_date.today().isoformat()

    tk = ticker.upper().strip()
    fluxos = fluxos_dir(criar=True)
    path = fluxos / f"{tk}.csv"
    today = dt_date.today()

    # 1. Buscar no FI Analytics
    result = None
    try:
        result = calc_corporate(tk, data_calc, rate=yield_ref)
    except Exception as e:
        pass

    if result is None:
        return {"ticker": tk, "status": "ERRO", "msg": "Nao encontrado no FI Analytics"}

    # 2. Extrair dados
    flows_raw = result.get("cashFlowList") or result.get("cashFlow") or []
    m2m = result.get("m2m") or result.get("PU", 0)
    m2m_rate = result.get("m2mRate") or result.get("yield", 0)
    method = result.get("method", "")
    duration = result.get("maculayDuration") or result.get("duration", 0)
    issuer = str(result.get("issuer") or result.get("companyName", ""))
    vne = float(result.get("vne") or result.get("VNE", 1000))
    inicio = result.get("startingDate") or result.get("startDate", "")
    vencimento = result.get("maturityDate") or result.get("expiredate", "")
    taxed_rate = result.get("taxedM2MRate", 0)
    di_add = result.get("diEquivalentAdditiveRate", 0)
    di_mult = result.get("diEquivalentMultiplicativeRate", 0)

    # Tenta dados complementares do DB
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM bonds WHERE ticker=?", (tk,)).fetchone()
        if row:
            if not issuer: issuer = row["issuer"] or ""
            if vne <= 0: vne = float(row["vne"] or 1000)
            if not inicio: inicio = row["startingdate"] or ""
            if not vencimento: vencimento = row["expiredate"] or ""
            if yield_ref == 5.0 and row["yield_contract"]:
                yield_ref = float(row["yield_contract"])

    # Se nao tem inicio, tenta API B3
    if not inicio:
        try:
            from src.api_client import get_bond_details
            det = get_bond_details(tk)
            if det:
                inicio = det.get("startingdate", "")
                vencimento = vencimento or det.get("expiredate", "")
                vne = float(det.get("vne", vne))
                issuer = issuer or (det.get("issuer", "")).replace(";", " ")
                if det.get("yield"): yield_ref = float(det["yield"])
        except Exception:
            pass

    if not inicio:
        inicio = data_calc

    idx = _idx(method, yield_ref)

    # 3. Amortizacoes (da API ou DB)
    amort_schedule = []
    events_raw = result.get("events") or result.get("amortizationSchedule") or []
    for e in events_raw:
        ev_type = str(e.get("eventType") or e.get("type", ""))
        if ev_type == "A":
            amort_schedule.append({
                "date": (e.get("date") or "")[:10],
                "pct": float(e.get("yield") or e.get("pct", 0))
            })

    # 4. Calcular VNA proprio
    vna_info = {"vne": vne, "indexador": idx,
                "inicio_rentabilidade": inicio,
                "amort_schedule": amort_schedule}
    if "%CDI" in idx:
        vna_info["pct_cdi"] = yield_ref
    vna_result = calcular_vna(vna_info, data_calc)
    vna_local = vna_result["vna"]

    # 5. Construir CSV
    lines = [
        csv_row("ticker", tk),
        csv_row("tipo", str(result.get("bondType", ""))),
        csv_row("indexador", idx),
        csv_row("emissor", issuer),
        csv_row("method", method),
        csv_row("inicio_rentabilidade", inicio),
        csv_row("vencimento", vencimento),
        csv_row("vne", vne),
        csv_row("taxa_ref", yield_ref),
        csv_row("data_fluxo", data_calc),
        csv_row("vna", vna_local),
        csv_row("vna_ipca_factor", vna_result.get("ipca_factor",
                 vna_result.get("cdi_factor", 0))),
        csv_row("vna_amort_factor", vna_result.get("amort_factor", 1.0)),
        csv_row("fonte", "FI_Analytics"),
        csv_row("m2m", float(m2m) if m2m else 0),
        csv_row("m2m_rate", float(m2m_rate) if m2m_rate else 0),
        csv_row("duration", float(duration) if duration else 0),
        csv_row("di_equiv_add", float(di_add) if di_add else 0),
        csv_row("di_equiv_mult", float(di_mult) if di_mult else 0),
        csv_row("taxed_rate", float(taxed_rate) if taxed_rate else 0),
        "",
    ]

    # Fluxos
    if flows_raw:
        lines.append(csv_header("DATA", "EVENTO", "VF", "PV", "DU", "TAI_PCT", "AMORT_PCT"))
        grupos = defaultdict(lambda: {"jvf": 0.0, "jpv": 0.0, "avf": 0.0, "apv": 0.0, "du": 0})

        for f in flows_raw:
            d = str(f.get("date") or f.get("eventDate", ""))[:10]
            ev = str(f.get("eventType") or f.get("event", "J"))
            vf = float(f.get("finalValue") or f.get("value", 0))
            pv = float(f.get("presentValue") or f.get("present_value", 0))
            du = int(f.get("workingDays") or f.get("du", 0))
            if du == 0 and d:
                try:
                    du = _du(today, datetime.fromisoformat(d).date())
                except: pass

            if ev == "A":
                grupos[d]["avf"] += vf; grupos[d]["apv"] += pv
            else:
                grupos[d]["jvf"] += vf; grupos[d]["jpv"] += pv
            grupos[d]["du"] = du

        vna_ref = vna_local if vna_local > 0 else 1.0
        for d in sorted(grupos):
            g = grupos[d]
            vf_total = g["jvf"] + g["avf"]
            pv_total = g["jpv"] + g["apv"]
            j_pct = (g["jvf"] / vna_ref) * 100 if vna_ref > 0 else 0
            a_pct = (g["avf"] / vna_ref) * 100 if vna_ref > 0 else 0
            ev_label = "J" if g["jvf"] > 0 and g["avf"] == 0 else \
                       "A" if g["avf"] > 0 and g["jvf"] == 0 else "JA"
            lines.append(csv_row(d, ev_label, vf_total, pv_total, g["du"], j_pct, a_pct))

    # Amortizacoes
    if amort_schedule:
        lines.append("")
        for a in amort_schedule:
            lines.append(csv_row("AMORT", a["date"], a["pct"]))

    csv_write(path, lines)

    # 6. Salvar no DB
    with get_conn() as conn:
        conn.execute("""INSERT OR REPLACE INTO bonds
            (ticker, tipo, method, issuer, startingdate, expiredate,
             vne, yield_contract, status, last_sync)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (tk, idx, method, issuer, inicio, vencimento, vne, yield_ref, "A", data_calc))

    return {
        "ticker": tk, "status": "OK", "indexador": idx,
        "n_flows": len(flows_raw), "vna": round(vna_local, 4),
        "fonte": "FI_Analytics", "data": data_calc,
    }


# ─── Importar TODOS ────────────────────────────────────────────

def importar_todos(max_n: int | None = None, resume: bool = True):
    """Importa TODOS os bonds do FI Analytics."""
    init_db()
    data_calc = dt_date.today().isoformat()

    print("=" * 60)
    print("  RF_CALC — IMPORTACAO COMPLETA (FI Analytics)")
    print(f"  Data: {data_calc}")
    print("=" * 60)

    # 1. BACEN
    print("\n[1/4] Atualizando BACEN (CDI + IPCA + projecoes)...")
    try:
        sync_bacen.sync_cdi()
        sync_bacen.sync_ipca()
        sync_bacen.sync_anbima_ipca_projection()
        print("  OK")
    except Exception as e:
        print(f"  ERRO: {e}")
        print("  Continuando mesmo sem BACEN atualizado...")

    # 2. Listar bonds
    print("\n[2/4] Listando bonds do FI Analytics...")
    bonds = get_user_bonds()
    tickers = [b.get("bond_name", "").strip() for b in bonds if b.get("bond_name")]
    print(f"  {len(tickers)} ativos encontrados")

    if max_n:
        tickers = tickers[:max_n]
        print(f"  Limitado a {max_n}")

    # 3. Importar
    fluxos = fluxos_dir(criar=True)
    print(f"\n[3/4] Importando {len(tickers)} ativos...")
    ok = skip = err = 0
    t0 = time.time()

    for i, tk in enumerate(tickers, 1):
        # Resume
        if resume:
            p = fluxos / f"{tk}.csv"
            if p.exists():
                try:
                    for ln in p.read_text(encoding="utf-8").splitlines()[:5]:
                        if ln.startswith(f"data_fluxo{SEP}{data_calc}"):
                            skip += 1; break
                    else:
                        pass
                except: pass
                else:
                    if i % 100 == 0:
                        print(f"  [{i}/{len(tickers)}] ok={ok} skip={skip} err={err}")
                    continue

        try:
            r = importar_ticker(tk, data_calc)
            if r["status"] == "OK": ok += 1
            else: err += 1; print(f"  [ERRO] {tk}: {r.get('msg','?')}", flush=True)
        except Exception as e:
            err += 1; print(f"  [EXC] {tk}: {e}", flush=True)

        time.sleep(DELAY)

        if i % 50 == 0:
            elapsed = (time.time() - t0) / 60
            rem = (len(tickers) - i) * elapsed / max(1, i)
            print(f"  [{i}/{len(tickers)}] ok={ok} skip={skip} err={err} | ~{rem:.0f}min")

    elapsed = (time.time() - t0) / 60
    print(f"\n[4/4] CONCLUIDO: ok={ok} skip={skip} err={err} | {elapsed:.1f} min")

    # Feriados
    fer_path = fluxos / "_feriados.csv"
    fer_path.write_text("\n".join(sorted(d.isoformat() for d in FERIADOS)), encoding="utf-8")

    return {"ok": ok, "skip": skip, "err": err, "total": len(tickers)}


# ─── Validar ───────────────────────────────────────────────────

def validar_amostra(n: int = 20):
    """Valida PU local vs FI Analytics para amostra de N ativos."""
    fluxos = fluxos_dir(criar=False)
    csvs = [f for f in sorted(fluxos.glob("*.csv")) if not f.name.startswith("_")]

    if not csvs:
        print("Nenhum CSV encontrado. Rode importar_tudo primeiro.")
        return

    import random
    sample = random.sample(csvs, min(n, len(csvs)))

    print(f"Validando {len(sample)} ativos contra FI Analytics...\n")
    print(f"{'TICKER':<14} {'PU_LOCAL':>12} {'PU_FI':>12} {'ERRO':>12} {'STATUS'}")
    print("-" * 65)

    erros = []
    for path in sample:
        tk = path.stem
        try:
            # Le VNA e taxa do CSV
            txt = path.read_text(encoding="utf-8")
            vna_line = [l for l in txt.splitlines() if l.startswith(f"vna{SEP}")][0]
            vna = parse_br(vna_line.split(SEP)[1])
            taxa_line = [l for l in txt.splitlines() if l.startswith(f"taxa_ref{SEP}")][0]
            taxa = parse_br(taxa_line.split(SEP)[1])

            # PU local (aproximado: Σ FC%/(1+taxa)^(du/252) × VNA)
            # Le fluxos
            pu_local = 0
            in_flows = False
            for ln in txt.splitlines():
                if ln.startswith("DATA;"):
                    in_flows = True; continue
                if in_flows and ln.startswith("AMORT;"):
                    break
                if in_flows and ln:
                    p = ln.split(SEP)
                    if len(p) >= 6:
                        tai = parse_br(p[5]) / 100  # % → fracao
                        du = int(p[4]) if p[4].isdigit() else 0
                        if du > 0:
                            pu_local += tai / ((1 + taxa/100) ** (du/252))

            pu_local *= vna

            # PU FI Analytics
            result = calc_corporate(tk, dt_date.today().isoformat(), rate=taxa)
            pu_fi = float(result.get("m2m") or result.get("PU", 0))

            erro = abs(pu_local - pu_fi)
            status = "OK" if erro < 0.01 else "ERRO"
            if erro >= 0.01: erros.append((tk, erro))

            print(f"{tk:<14} {pu_local:>12.6f} {pu_fi:>12.6f} {erro:>12.8f} {status}")

        except Exception as e:
            print(f"{tk:<14} {'--':>12} {'--':>12} {'--':>12} ERRO: {e}")

    print(f"\nErros > 0.01: {len(erros)}")
    for tk, e in erros[:5]:
        print(f"  {tk}: erro={e:.6f}")


# ─── CLI ───────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        importar_todos()
    elif args[0] == "--max":
        importar_todos(max_n=int(args[1]) if len(args) > 1 else 50)
    elif args[0] == "--ticker":
        tk = args[1] if len(args) > 1 else input("Ticker: ")
        r = importar_ticker(tk)
        print(json.dumps(r, indent=2, ensure_ascii=False))
    elif args[0] == "--validar":
        validar_amostra(int(args[1]) if len(args) > 1 else 20)
    else:
        print(__doc__)
