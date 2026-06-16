"""
Motor de sincronização principal — FI Analytics como fonte primária.

Pipeline diário:
  1. Lista todos os bonds do usuário no FI Analytics (getuserbonds)
  2. Para cada bond, busca fluxo de caixa completo via deb/cr/bondbuilder
  3. Calcula VNA localmente (IPCA, CDI, PRE)
  4. Enriquece com ANBIMA Data (características, amortizações)
  5. Salva no formato CSV otimizado (com % Tai por evento)
  6. Atualiza banco SQLite para consultas rápidas

Novo formato CSV (separador = ;, decimal = virgula — padrao brasileiro):
  META;CHAVE;VALOR
  FLUXO;data;evento;vf;pv;du;tai_pct;amort_pct
  VNA;data;vna
  AMORT;data;pct_vne

Diferenciais vs. B3:
  - % Tai (juros) e % Amortização separados por evento
  - Juros incorporados (accrued interest) considerados (FI Analytics já inclui)
  - VNA calculado localmente (sem dependência da API)
  - Dados enriquecidos com ANBIMA
"""
import sys
import time
import json
from datetime import date as dt_date, datetime, timedelta
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import get_required, get_token, get_fluxos_dir
from src.fi_client import get_user_bonds, calc_corporate, calc_gov_bond
from src.vna_calc import get_ipca_index, calc_vna_cdi
from src.db import get_conn, init_db
from src.fmt_br import SEP, fmt, fmt_pct, csv_row, csv_header, csv_write
from src import sync_bacen

DELAY = 0.5  # segundos entre chamadas à API


# ═══════════════════════════════════════════════════════════════
# Feriados para contagem de DU
# ═══════════════════════════════════════════════════════════════

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


def _feriados_set(ano_ini=2001, ano_fim=2050) -> set[dt_date]:
    fer = set()
    for y in range(ano_ini, ano_fim + 1):
        pascoa = _easter(y)
        fer |= {
            dt_date(y, 1, 1), pascoa - timedelta(days=48),
            pascoa - timedelta(days=47), pascoa - timedelta(days=2),
            dt_date(y, 4, 21), dt_date(y, 5, 1),
            pascoa + timedelta(days=60), dt_date(y, 9, 7),
            dt_date(y, 10, 12), dt_date(y, 11, 2),
            dt_date(y, 11, 15), dt_date(y, 12, 25),
        }
        if y >= 2024:
            fer.add(dt_date(y, 11, 20))
    return fer


FERIADOS = _feriados_set()


def _count_du(start: dt_date, end: dt_date) -> int:
    """Dias úteis entre start (exclusive) e end (inclusive)."""
    count = 0
    d = start + timedelta(days=1)
    while d <= end:
        if d.weekday() < 5 and d not in FERIADOS:
            count += 1
        d += timedelta(days=1)
    return max(1, count)


# ═══════════════════════════════════════════════════════════════
# Classificação de indexador
# ═══════════════════════════════════════════════════════════════

def _classificar_indexador(method: str, rate: float | None = None) -> str:
    """Determina o indexador com base no method e na taxa."""
    m = (method or "").upper()
    if "IPCA" in m or "IGP" in m:
        return "IPCA"
    if "DI" in m or "CDI" in m:
        if rate is not None and rate >= 50:
            return "%CDI"
        return "CDI+"
    return "PRE"


# ═══════════════════════════════════════════════════════════════
# Sincronização de um ticker (FI Analytics → CSV + DB)
# ═══════════════════════════════════════════════════════════════

def sync_ticker(ticker: str, data_calc: str | None = None,
                yield_ref: float | None = None) -> dict:
    """
    Sincroniza UM ticker: busca na FI Analytics, calcula VNA local, salva CSV e DB.

    Args:
        ticker: código do ativo
        data_calc: data base (default=hoje)
        yield_ref: taxa de referência (default=busca do cadastro)

    Returns:
        dict com status, n_flows, vna, indexador, fonte
    """
    if data_calc is None:
        data_calc = dt_date.today().isoformat()

    ticker = ticker.upper().strip()
    fluxos_dir = get_fluxos_dir()
    fluxos_dir.mkdir(parents=True, exist_ok=True)
    csv_path = fluxos_dir / f"{ticker}.csv"

    # Determina a taxa de referência
    if yield_ref is None:
        with get_conn() as conn:
            row = conn.execute(
                "SELECT yield_contract FROM bonds WHERE ticker=?", (ticker,)
            ).fetchone()
        if row and row["yield_contract"]:
            yield_ref = float(row["yield_contract"])

    # ── Etapa 1a: Buscar metadados do ativo (DB ou B3 API) ──────────────
    issuer = ""
    vne = 1000.0
    inicio_rent = data_calc
    vencimento = ""
    method = ""
    idx = "PRE"

    with get_conn() as conn:
        row = conn.execute("SELECT * FROM bonds WHERE ticker=?", (ticker,)).fetchone()
        if row:
            issuer = row["issuer"] or ""
            vne = float(row["vne"] or 1000.0)
            inicio_rent = row["startingdate"] or data_calc
            vencimento = row["expiredate"] or ""

    # Se nao tem no DB, busca na B3 (getbonddetails)
    if not inicio_rent or inicio_rent == data_calc:
        try:
            from src.api_client import get_bond_details
            det = get_bond_details(ticker)
            if det:
                issuer = issuer or (det.get("issuer") or "").replace(";", " ")
                vne = float(det.get("vne") or vne)
                inicio_rent = (det.get("startingdate") or inicio_rent)
                vencimento = vencimento or (det.get("expiredate") or "")
                method = det.get("method") or ""
                if yield_ref is None and det.get("yield"):
                    yield_ref = float(det["yield"])
                # Salva no DB
                with get_conn() as conn:
                    conn.execute("""INSERT OR REPLACE INTO bonds
                        (ticker, tipo, method, issuer, startingdate, expiredate,
                         vne, yield_contract, status, last_sync)
                        VALUES (?,?,?,?,?,?,?,?,?,?)""",
                        (ticker, "", method, issuer, inicio_rent, vencimento,
                         vne, yield_ref, "A", data_calc))
        except Exception:
            pass

    # ── Etapa 1b: Buscar fluxos (FI Analytics → B3 fallback) ──────────────
    result = None
    fonte = None
    flows_raw = []

    # 1) FI Analytics (primario)
    try:
        result = calc_corporate(ticker, data_calc, rate=yield_ref)
        fonte = "FI_Analytics"
        flows_raw = result.get("cashFlowList") or result.get("cashFlow") or []
        method = result.get("method") or method
    except Exception:
        pass

    # 2) B3 API (fallback)
    if result is None:
        try:
            from src.api_client import calc_pu_api
            b3_result = calc_pu_api(ticker, data_calc, yield_ref)
            result = b3_result
            fonte = "B3"
            flows_raw = b3_result.get("cashFlowList") or []
            method = b3_result.get("method") or method
        except Exception:
            pass

    if result is None or not flows_raw:
        return {"ticker": ticker, "status": "ERRO",
                "msg": "Nao encontrado em FI Analytics nem B3"}

    # Se yield_ref ainda nao foi definido, usar fallback 5.0
    if yield_ref is None:
        yield_ref = 5.0

    # Extrair metadados do resultado
    m2m = result.get("m2m") or result.get("PU")
    m2m_rate = result.get("m2mRate") or result.get("yield")
    duration = result.get("maculayDuration") or result.get("duration")
    if not issuer:
        issuer = str(result.get("issuer") or result.get("companyName") or "")

    # Classificar indexador (method do calcPU, nao do getbonddetails)
    idx = _classificar_indexador(method, yield_ref)

    # ── Etapa 2: Calcular VNA LOCALMENTE (NAO confia no VNA da API) ─────
    # O VNA da B3 frequentemente vem como 1.0 (quebrado). O da FI Analytics
    # e' confiavel. Para IPCA: SEMPRE recalcula localmente.
    vna_api = float(result.get("VNA") or result.get("vna") or 0.0)
    vna_local = vne
    vna_factor = 1.0

    if fonte == "FI_Analytics" and vna_api > 1.01:
        # FI Analytics: confia no VNA se razoavel (> 1.01 = nao eh 1.0 quebrado)
        vna_local = vna_api
    elif idx == "IPCA":
        # IPCA: calcula localmente com IPCA do BACEN (nao confia no VNA da API)
        try:
            from src.sync_bacen import sync_ipca
            vna_factor = get_ipca_index(inicio_rent, data_calc)
            vna_local = vne * vna_factor
        except Exception:
            if vna_api > 1.01:
                vna_local = vna_api  # fallback: usa API se razoavel
    elif idx == "CDI+":
        pct = 100.0
        try:
            cdi_result = calc_vna_cdi(vne, inicio_rent, data_calc, pct_cdi=pct)
            vna_local = cdi_result["vna"]
        except Exception:
            if vna_api > 1.01:
                vna_local = vna_api
    elif "%CDI" in idx:
        pct = yield_ref if yield_ref >= 50 else 100.0
        try:
            cdi_result = calc_vna_cdi(vne, inicio_rent, data_calc, pct_cdi=pct)
            vna_local = cdi_result["vna"]
        except Exception:
            if vna_api > 1.01:
                vna_local = vna_api
    else:  # PRE: VNA constante
        vna_local = vne

    # Etapa 3: Construir CSV no padrao brasileiro (; e virgula decimal)
    lines = [
        csv_row("ticker", ticker),
        csv_row("tipo", str(result.get("bondType", ""))),
        csv_row("indexador", idx),
        csv_row("emissor", issuer),
        csv_row("method", method),
        csv_row("inicio_rentabilidade", inicio_rent),
        csv_row("vencimento", vencimento),
        csv_row("vne", vne),
        csv_row("taxa_ref", yield_ref),
        csv_row("data_fluxo", data_calc),
        csv_row("vna", vna_local),
        csv_row("vna_factor", vna_factor),
        csv_row("fonte", fonte),
        csv_row("m2m", float(m2m) if m2m else 0.0),
        csv_row("duration", float(duration) if duration else 0.0),
        csv_row("di_equiv_add", float(result.get("diEquivalentAdditiveRate") or 0)),
        csv_row("di_equiv_mult", float(result.get("diEquivalentMultiplicativeRate") or 0)),
        csv_row("taxed_rate", float(result.get("taxedM2MRate") or 0)),
        "",
    ]

    # Cabecalho dos fluxos
    lines.append(csv_header("DATA", "EVENTO", "VF", "PV", "DU", "TAI_PCT", "AMORT_PCT"))

    n_flows = 0
    if flows_raw:
        # Agrupar fluxos por data
        from collections import defaultdict
        grupos: dict = defaultdict(lambda: {"juros_vf": 0.0, "juros_pv": 0.0,
                                              "amort_vf": 0.0, "amort_pv": 0.0,
                                              "du": 0})

        for f in flows_raw:
            d = str(f.get("date") or f.get("eventDate") or "")[:10]
            ev = str(f.get("eventType") or f.get("event") or "J")
            vf = float(f.get("finalValue") or f.get("value") or 0.0)
            pv = float(f.get("presentValue") or f.get("present_value") or 0.0)
            du = int(f.get("workingDays") or f.get("du") or 0)

            if du == 0 and d:
                du = _count_du(dt_date.today(), datetime.fromisoformat(d).date())

            if ev == "A":
                grupos[d]["amort_vf"] += vf
                grupos[d]["amort_pv"] += pv
            else:
                grupos[d]["juros_vf"] += vf
                grupos[d]["juros_pv"] += pv
            grupos[d]["du"] = du

        for d in sorted(grupos):
            g = grupos[d]
            vna_ref = vna_local if vna_local > 0 else 1.0
            juros_pct = (g["juros_vf"] / vna_ref) * 100.0
            amort_pct = (g["amort_vf"] / vna_ref) * 100.0
            ev_label = ("J" if g["juros_vf"] > 0 and g["amort_vf"] == 0 else
                       "A" if g["amort_vf"] > 0 and g["juros_vf"] == 0 else "JA")
            lines.append(csv_row(
                d,
                ev_label,
                g["juros_vf"] + g["amort_vf"],
                g["juros_pv"] + g["amort_pv"],
                g["du"],
                juros_pct,
                amort_pct,
            ))
            n_flows += 1

    csv_write(csv_path, lines)

    # Etapa 4: Se fonte B3, atualiza metadados (yield pode estar desatualizado no DB)
    if fonte == "B3" and yield_ref:
        try:
            from src.api_client import get_bond_details
            det = get_bond_details(ticker)
            if det and det.get("yield"):
                yield_ref = float(det["yield"])
                inicio_rent = det.get("startingdate") or inicio_rent
                vencimento = det.get("expiredate") or vencimento
                vne = float(det.get("vne") or vne)
                issuer = issuer or (det.get("issuer") or "").replace(";", " ")
        except Exception:
            pass

    # Etapa 5: Atualizar DB
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO bonds
                (ticker, tipo, method, issuer, startingdate, expiredate,
                 vne, yield_contract, status, last_sync)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            ticker, idx, method, issuer, inicio_rent, vencimento,
            vne, yield_ref, "A", data_calc,
        ))

    return {
        "ticker": ticker,
        "status": "OK",
        "indexador": idx,
        "n_flows": n_flows,
        "vna": round(vna_local, 4),
        "vna_factor": round(vna_factor, 8),
        "fonte": fonte,
        "data": data_calc,
    }


# ═══════════════════════════════════════════════════════════════
# Sincronização em massa (todos os bonds do FI Analytics)
# ═══════════════════════════════════════════════════════════════

def sync_all(data_calc: str | None = None, *,
             tipos: list[str] | None = None,
             resume: bool = True,
             max_ativos: int | None = None) -> dict:
    """
    Sincroniza TODOS os ativos do FI Analytics.

    Args:
        data_calc: data base (default=hoje)
        tipos: ["deb", "cr"] ou None para todos
        resume: pular ativos já sincronizados hoje
        max_ativos: limitar número de ativos (para testes)

    Returns:
        dict com {ok, skip, err, total, elapsed_min}
    """
    if data_calc is None:
        data_calc = dt_date.today().isoformat()

    init_db()

    print(f"\n{'='*60}")
    print(f"  SINCRONIZAÇÃO FI ANALYTICS — {data_calc}")
    print(f"{'='*60}\n")

    # Garantir dados BACEN atualizados
    print("[1/4] Atualizando dados BACEN...")
    try:
        sync_bacen.sync_cdi()
        sync_bacen.sync_ipca()
        sync_bacen.sync_anbima_ipca_projection()
    except Exception as e:
        print(f"  ⚠ BACEN parcial: {e}")

    # Listar bonds do usuário
    print("\n[2/4] Listando bonds do FI Analytics...")
    bonds = get_user_bonds()
    print(f"  {len(bonds)} ativos encontrados na carteira FI Analytics")

    if not bonds:
        print("  ⚠ Nenhum ativo encontrado. Verifique FI_USER_EMAIL no tokens.txt")
        return {"ok": 0, "skip": 0, "err": 0, "total": 0, "elapsed_min": 0}

    # Filtrar por tipo se solicitado
    tickers = []
    for b in bonds:
        ticker = b.get("bond_name", "").strip()
        if ticker:
            tickers.append(ticker)

    if max_ativos:
        tickers = tickers[:max_ativos]

    print(f"\n[3/4] Sincronizando {len(tickers)} ativos...\n")
    t0 = time.time()
    ok = skip = err = 0

    fluxos_dir = get_fluxos_dir()

    for i, tk in enumerate(tickers, 1):
        # Resume: pular se já sincronizado hoje
        if resume:
            csv_path = fluxos_dir / f"{tk}.csv"
            if csv_path.exists():
                try:
                    first_lines = csv_path.read_text(encoding="utf-8").splitlines()[:15]
                    for ln in first_lines:
                        p = ln.split(SEP)
                        if len(p) >= 3 and p[0] == "META" and p[1] == "DATA_FLUXO":
                            if p[2] == data_calc:
                                skip += 1
                                break
                    else:
                        pass  # não encontrou DATA_FLUXO, prossegue
                except Exception:
                    pass
                else:
                    if csv_path.exists():
                        # Já verificado no loop acima
                        if i % 100 == 0:
                            print(f"  [{i}/{len(tickers)}] ok={ok} skip={skip} err={err}")
                        continue

        try:
            result = sync_ticker(tk, data_calc)
            if result["status"] == "OK":
                ok += 1
                if ok % 20 == 0:
                    print(f"  ✓ {tk} | {result['n_flows']} fluxos | VNA={result['vna']:.2f} | {result['indexador']}")
            else:
                err += 1
                print(f"  ✗ {tk}: {result.get('msg', 'erro desconhecido')}")
        except Exception as e:
            err += 1
            print(f"  ✗ {tk}: {e}")
            time.sleep(1)  # espera extra em caso de erro

        time.sleep(DELAY)

        if i % 50 == 0:
            elapsed = (time.time() - t0) / 60
            remaining = (len(tickers) - i) * elapsed / max(1, i)
            print(f"  [{i}/{len(tickers)}] ok={ok} skip={skip} err={err} | ~{remaining:.0f}min restantes")

    elapsed = (time.time() - t0) / 60

    # Resumo final
    print(f"\n[4/4] {'='*50}")
    print(f"  TOTAL: {len(tickers)} ativos")
    print(f"  OK:    {ok}")
    print(f"  PULO:  {skip}")
    print(f"  ERRO:  {err}")
    print(f"  TEMPO: {elapsed:.1f} min")
    print(f"{'='*50}\n")

    # Salvar log
    log_path = ROOT / "data" / "sync_fi.log"
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"[{datetime.now().isoformat()}] "
                  f"total={len(tickers)} ok={ok} skip={skip} err={err} "
                  f"tempo={elapsed:.1f}min data={data_calc}\n")

    # Atualizar _feriados.csv
    _write_feriados_csv(fluxos_dir)

    return {
        "ok": ok, "skip": skip, "err": err,
        "total": len(tickers),
        "elapsed_min": round(elapsed, 1),
    }


def _write_feriados_csv(fluxos_dir: Path):
    """Escreve arquivo de feriados no formato esperado pelo add-in."""
    path = fluxos_dir / "_feriados.csv"
    linhas = sorted(d.isoformat() for d in FERIADOS)
    path.write_text("\n".join(linhas), encoding="utf-8")
    print(f"  _feriados.csv: {len(linhas)} datas")


# ═══════════════════════════════════════════════════════════════
# Atualização incremental (apenas ativos que mudaram)
# ═══════════════════════════════════════════════════════════════

def sync_incremental(data_calc: str | None = None) -> dict:
    """
    Atualização incremental: apenas ativos não sincronizados na data atual.
    Mais rápido que sync_all — ideal para rotina diária.
    """
    return sync_all(data_calc, resume=True)


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]

    if not args:
        sync_incremental()
    elif args[0] == "--all" or args[0] == "-a":
        sync_all(resume=False if "--force" in args else True)
    elif args[0] == "--ticker" or args[0] == "-t":
        tk = args[1] if len(args) > 1 else input("Ticker: ")
        r = sync_ticker(tk)
        print(f"\n{r['status']}: {r['ticker']} | {r['n_flows']} fluxos | VNA={r['vna']}")
    else:
        # Ticker específico
        r = sync_ticker(args[0], args[1] if len(args) > 1 else None)
        print(f"\n{r['status']}: {r['ticker']} | {r['n_flows']} fluxos | VNA={r['vna']} | {r['indexador']}")
