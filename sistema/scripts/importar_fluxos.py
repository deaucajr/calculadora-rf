#!/usr/bin/env python
"""
Importa fluxos da calculadora B3 e grava em fluxos/<TICKER>.csv (leve, lazy-load).

Uso:
  python importar_fluxos.py                    -> processa fluxos/_importar.txt (1 ticker por linha)
  python importar_fluxos.py EGIEA6             -> importa um ticker (data = hoje)
  python importar_fluxos.py EGIEA6 2026-06-11  -> importa com data especifica
  python importar_fluxos.py --feriados         -> (re)gera fluxos/_feriados.csv

Formato do CSV (separador = ;, decimal = virgula — padrao brasileiro):
  META;CHAVE;VALOR          (cabecalho: TICKER, INDEXADOR, EMISSOR, ...)
  FLUXO;data;evento;vf;pv;du;fc_pct
  VNA;data;vna             (1 ponto por data importada, acumula)

Modelo de calculo (ver wiki projeto-addin-fluxos):
  IPCA/PRE: PU(data,taxa) = [Sum FC% / (1+taxa/100)^(du/252)] * VNA(data)
            FC% = VF/VNA e' data-independente -> 1 download serve p/ qualquer taxa.
  CDI/%CDI: exato na DATA_FLUXO; outras datas dependem da curva DI (ver curva_di).

API: 2 chamadas na 1a importacao do ticker; 1 (calcPU) p/ cada nova data. Token cacheado.
"""
import sys
from datetime import date as dt_date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.paths import fluxos_dir
from src.fmt_br import SEP, fmt, fmt_pct, csv_row, csv_header, csv_write
FLUXOS_DIR = fluxos_dir()


# â”€â”€ Feriados nacionais (ANBIMA) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


def gerar_feriados(ano_ini=2001, ano_fim=2045) -> list[dt_date]:
    fer = []
    for y in range(ano_ini, ano_fim + 1):
        pascoa = _easter(y)
        fer += [
            dt_date(y, 1, 1), pascoa - timedelta(days=48), pascoa - timedelta(days=47),
            pascoa - timedelta(days=2), dt_date(y, 4, 21), dt_date(y, 5, 1),
            pascoa + timedelta(days=60), dt_date(y, 9, 7), dt_date(y, 10, 12),
            dt_date(y, 11, 2), dt_date(y, 11, 15), dt_date(y, 12, 25),
        ]
        if y >= 2024:
            fer.append(dt_date(y, 11, 20))  # Consciencia Negra (nacional desde 2024)
    return sorted(fer)


def gerar_feriados_csv():
    FLUXOS_DIR.mkdir(exist_ok=True)
    path = FLUXOS_DIR / "_feriados.csv"
    linhas = [d.isoformat() for d in gerar_feriados()]
    path.write_text("\n".join(linhas), encoding="utf-8")
    print(f"OK {path.name} ({len(linhas)} feriados)")


def _indexador(method: str | None) -> str:
    m = (method or "").upper()
    if "IPCA" in m or "IGP" in m:
        return "IPCA"
    if "DI" in m or "CDI" in m:
        return "CDI"
    return "PRE"


def _iso(s):
    if not s:
        return ""
    if isinstance(s, (datetime, dt_date)):
        return s.isoformat()[:10]
    try:
        return datetime.fromisoformat(str(s)[:10]).date().isoformat()
    except ValueError:
        return ""


def _ler_blocos_cdi(path: Path) -> dict:
    """Le blocos CDI acumulados -> {data_calc: [linhas]}.
    Suporta formato novo (CDI ...) e legado (FLUXOD ...)."""
    blocos = {}
    if not path.exists():
        return blocos
    for ln in path.read_text(encoding="utf-8").splitlines():
        p = ln.split(SEP)
        if not p:
            continue
        if p[0] == "CDI" and len(p) >= 6:           # novo formato
            blocos.setdefault(p[1], []).append(ln)
        elif p[0] == "FLUXOD" and len(p) >= 7:      # legado — converte
            new_ln = SEP.join(["CDI", p[1], p[2], p[4], p[5], p[6]])
            blocos.setdefault(p[1], []).append(new_ln)
    return blocos


def importar_ticker(ticker: str, data_calc: str | None = None) -> str:
    """Busca o ativo na B3 e grava/atualiza fluxos/<TICKER>.csv."""
    from collections import defaultdict
    from src.api_client import get_bond_details, calc_pu_api

    ticker = ticker.upper().strip()
    if data_calc is None:
        data_calc = dt_date.today().isoformat()
    FLUXOS_DIR.mkdir(exist_ok=True)
    path = FLUXOS_DIR / f"{ticker}.csv"

    det = get_bond_details(ticker)
    taxa_ref = float(det.get("yield") or 0.0)
    r = calc_pu_api(ticker, data_calc, taxa_ref)

    flows = r.get("cashFlowList", [])
    if not flows:
        return f"ERRO: sem fluxos para {ticker}"
    vna = float(r.get("VNA") or 0.0)
    if vna <= 0:
        return f"ERRO: VNA invalido p/ {ticker}"

    tipo = "DEB"
    t = det.get("tipoIF")
    if isinstance(t, dict):
        tipo = t.get("codigoAsString", "DEB")
    # IMPORTANTE: o method do calcPU define a metodologia de precificacao (DI-SPREAD,
    # DI-PERC, IPCA, PRE). O getbonddetails.method e' o indice de correcao do VNA e
    # pode divergir (ex: VNA corrige por IPCA mas precifica como DI-SPREAD).
    method_calc = r.get("method") or det.get("method") or ""
    indexador = _indexador(method_calc)
    dc = _iso(data_calc)
    emissor = (det.get("issuer") or "").replace(SEP, " ")

    if indexador == "CDI":
        # CDI/%CDI: fluxos dependem da data -> acumula 1 bloco CDI por data_calc.
        blocos = _ler_blocos_cdi(path)
        bloco = []
        for f in flows:
            bloco.append(csv_row(
                "CDI", dc, _iso(f["date"]),
                float(f["finalValue"]), float(f["presentValue"]),
                int(f["workingDays"]),
            ))
        blocos[dc] = bloco
        out = [
            csv_row("ticker", ticker),
            csv_row("tipo", tipo),
            csv_row("indexador", indexador),
            csv_row("emissor", emissor),
            csv_row("method", method_calc),
            csv_row("inicio_rentabilidade", _iso(det.get("startingdate"))),
            csv_row("vencimento", _iso(det.get("expiredate"))),
            csv_row("vne", float(det.get("vne") or 0)),
            csv_row("taxa_emissao", taxa_ref),
            csv_row("taxa_ref", taxa_ref),
            csv_row("data_fluxo", dc),
            csv_row("fonte", "B3"),
            "",
        ]
        for d in sorted(blocos):
            out.extend(blocos[d])
        csv_write(path, out)
        return f"OK {ticker}: {len(flows)} fluxos CDI, datas={len(blocos)}, {indexador}"

    # IPCA/PRE: FC% data-independente; separa J e A em colunas distintas
    grupos: dict[str, dict] = defaultdict(lambda: {"juros": 0.0, "amort": 0.0})
    for f in flows:
        d = _iso(f["date"])
        vf_f = float(f["finalValue"])
        ev = str(f["eventType"])
        if ev == "J":
            grupos[d]["juros"] += vf_f
        elif ev == "A":
            grupos[d]["amort"] += vf_f
        else:
            grupos[d]["juros"] += vf_f  # outros eventos tratados como juros

    out = [
        csv_row("ticker", ticker),
        csv_row("tipo", tipo),
        csv_row("indexador", indexador),
        csv_row("emissor", emissor),
        csv_row("method", method_calc),
        csv_row("inicio_rentabilidade", _iso(det.get("startingdate"))),
        csv_row("vencimento", _iso(det.get("expiredate"))),
        csv_row("vne", float(det.get("vne") or 0)),
        csv_row("taxa_emissao", taxa_ref),
        csv_row("taxa_ref", taxa_ref),
        csv_row("data_fluxo", dc),
        csv_row("vna", vna),
        csv_row("fonte", "B3"),
        "",
        csv_header("DATA", "JUROS_TAI", "AMORT_TAI"),
    ]
    for d in sorted(grupos):
        g = grupos[d]
        juros_pct = g["juros"] / vna
        amort_pct = g["amort"] / vna
        out.append(csv_row(d, juros_pct, amort_pct))

    # IPCA amortizante: cronograma de amortizacao (% de VNE, soma=100%)
    if indexador == "IPCA":
        amort_evs = sorted(
            (e["date"][:10], e["yield"])
            for e in det.get("events", [])
            if e.get("eventType") == "A"
        )
        if amort_evs:
            out.append("")
            for d_iso, pct in amort_evs:
                out.append(csv_row("AMORT", d_iso, pct))

    csv_write(path, out)
    return f"OK {ticker}: {len(grupos)} datas, VNA({dc})={vna:.4f}, {indexador}"


def processar_lista():
    path = FLUXOS_DIR / "_importar.txt"
    if not path.exists():
        FLUXOS_DIR.mkdir(exist_ok=True)
        path.write_text("# 1 ticker por linha; opcional 2a coluna com data YYYY-MM-DD (tab)\n",
                        encoding="utf-8")
        print(f"Criado {path.name}. Liste os tickers e rode de novo.")
        return
    n = 0
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        parts = ln.split()
        tk = parts[0]
        dt = parts[1] if len(parts) > 1 else None
        try:
            print(" ", importar_ticker(tk, dt))
        except Exception as e:
            print(f"  ERRO {tk}: {e}")
        n += 1
    print(f"\n{n} tickers processados.")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--feriados":
        gerar_feriados_csv()
    elif args:
        print(importar_ticker(args[0], args[1] if len(args) > 1 else None))
    else:
        processar_lista()
