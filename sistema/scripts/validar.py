#!/usr/bin/env python
"""
Valida o calculo local (mesma logica do add-in RF_Calc) contra a API B3.
Seleciona 5 ativos de cada tipo (IPCA, PRE, %CDI/DI-PERC, CDI+spread) e
compara PU local vs PU da API em varias datas.

Uso:
  python validar.py            -> classifica, seleciona e testa 5x4 tipos x 4 datas
  python validar.py EGIEA6     -> testa um ticker especifico
"""
import sys
import math
from datetime import date as dt_date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.paths import fluxos_dir
FLUXOS_DIR = fluxos_dir()
SEP = "\t"

from importar_fluxos import gerar_feriados, importar_ticker, _iso
from src.api_client import calc_pu_api

_FER = set(gerar_feriados())

# Fatores diarios do IPCA (_ipca.csv) — usados para escalar VNA entre datas
_IPCA_FAT = None

def _ipca_fatores():
    global _IPCA_FAT
    if _IPCA_FAT is not None:
        return _IPCA_FAT
    _IPCA_FAT = {}
    p = FLUXOS_DIR / "_ipca.csv"
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            a = ln.split(SEP)
            if len(a) >= 2:
                try:
                    _IPCA_FAT[a[0]] = float(a[1])
                except ValueError:
                    pass
    return _IPCA_FAT


_CDI = None
def cdi_dia(data: dt_date) -> float:
    """CDI diario (fracao) da data, ou o ultimo disponivel antes dela."""
    global _CDI
    if _CDI is None:
        _CDI = {}
        p = FLUXOS_DIR / "_cdi.csv"
        if p.exists():
            for ln in p.read_text(encoding="utf-8").splitlines():
                a = ln.split(SEP)
                if len(a) >= 2:
                    _CDI[a[0]] = float(a[1])
    di = data.isoformat()
    if di in _CDI:
        return _CDI[di]
    ant = [k for k in _CDI if k <= di]
    return _CDI[max(ant)] if ant else 0.0


def conta_du(d0: dt_date, d1: dt_date) -> int:
    if d1 <= d0:
        return 0
    n, d = 0, d0
    while d < d1:
        d += timedelta(days=1)
        if d.weekday() < 5 and d not in _FER:
            n += 1
    return n


def ler_csv(ticker: str) -> dict | None:
    path = FLUXOS_DIR / f"{ticker}.csv"
    if not path.exists():
        return None
    meta, fluxo, vna, cdi = {}, [], {}, {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        p = ln.split(SEP)
        if p[0] == "META" and len(p) >= 3:
            meta[p[1]] = p[2]
        elif p[0] == "FLUXO" and len(p) >= 7:
            fluxo.append((datetime.fromisoformat(p[1]).date(), float(p[6])))  # data, FC%
        elif p[0] == "VNA" and len(p) >= 3:
            vna[p[1]] = float(p[2])
        elif p[0] == "FLUXOD" and len(p) >= 7:
            cdi.setdefault(p[1], []).append((float(p[4]), float(p[5]), int(p[6])))  # vf, pv, du
    return {"meta": meta, "fluxo": fluxo, "vna": vna, "cdi": cdi}


def _vna_por_ipca(ancora_data: dt_date, ancora_val: float, data: dt_date) -> float:
    """Escala VNA usando os fatores diarios de _ipca.csv: VNA(t) = VNA_ancora * f(t)/f(ancora)."""
    fat = _ipca_fatores()
    fa = fat.get(ancora_data.isoformat())
    fd = fat.get(data.isoformat())
    if fa and fd and fa != 0:
        return ancora_val * fd / fa
    return ancora_val  # fallback: sem dado no _ipca.csv


def vna_data(vna: dict, data: dt_date, indexador: str = "") -> float:
    di = data.isoformat()
    if di in vna:
        return vna[di]
    pts = sorted((datetime.fromisoformat(k).date(), v) for k, v in vna.items())
    if not pts:
        return 0.0
    if len(pts) == 1:
        # Para IPCA: usa _ipca.csv para escalar corretamente para qualquer data
        if indexador == "IPCA":
            return _vna_por_ipca(pts[0][0], pts[0][1], data)
        return pts[0][1]
    # Multiplos pontos: interpolacao geometrica por dias uteis
    if data <= pts[0][0]:
        # Extrapolacao para tras: usa _ipca.csv se IPCA, senao usa primeiros 2 pontos
        if indexador == "IPCA":
            return _vna_por_ipca(pts[0][0], pts[0][1], data)
        a, b = pts[0], pts[1]
    elif data >= pts[-1][0]:
        if indexador == "IPCA":
            return _vna_por_ipca(pts[-1][0], pts[-1][1], data)
        a, b = pts[-2], pts[-1]
    else:
        a, b = pts[0], pts[1]
        for i in range(len(pts) - 1):
            if pts[i][0] <= data <= pts[i + 1][0]:
                a, b = pts[i], pts[i + 1]
                break
    duab = conta_du(a[0], b[0])
    if duab == 0:
        return a[1]
    frac = (conta_du(a[0], data) / duab) if data >= a[0] else (-conta_du(data, a[0]) / duab)
    return a[1] * (b[1] / a[1]) ** frac


def _pu_perc_curva(bloco: list, p0: float, p1: float) -> float:
    """DI-PERC: reconstroi a curva DI implicita (FD_i=vf/pv) e reprecifica a p1%.
    Deriva o CDI forward por segmento entre vertices e reaplica o percentual p1."""
    pu = 0.0
    prev_du = 0
    ln_prev_fd0 = 0.0
    ln_fdp1 = 0.0
    for vf, pv, du in bloco:
        ln_fd0 = math.log(vf / pv)
        dseg = du - prev_du
        if dseg > 0:
            g = (math.exp((ln_fd0 - ln_prev_fd0) / dseg) - 1) * 100 / p0
            ln_fdp1 += math.log(1 + g * p1 / 100) * dseg
            prev_du = du
            ln_prev_fd0 = ln_fd0
        pu += vf / math.exp(ln_fdp1)
    return pu


def calc_pu_local(d: dict, taxa: float, data: dt_date) -> float | None:
    idx = d["meta"].get("INDEXADOR", "")
    if idx == "CDI":
        di = data.isoformat()
        if di not in d["cdi"]:
            return None
        y0 = float(d["meta"]["TAXA_REF"])
        bloco = sorted(d["cdi"][di], key=lambda x: x[2])  # por du
        if y0 >= 50:  # DI-PERC (% do CDI): curva DI implicita (FD=vf/pv)
            pu = _pu_perc_curva(bloco, y0, taxa)
        else:         # DI-SPREAD (spread aditivo)
            pu = sum(pv * ((1 + y0 / 100) / (1 + taxa / 100)) ** (du / 252) for vf, pv, du in bloco)
        return math.floor(pu * 1e6) / 1e6
    # IPCA/PRE
    cot = 0.0
    for dt, fc in d["fluxo"]:
        du = conta_du(data, dt)
        if du > 0:
            cot += fc / (1 + taxa / 100) ** (du / 252)
    v = vna_data(d["vna"], data, idx)
    return math.floor(cot * v * 1e6) / 1e6


def classificar() -> dict:
    """Varre os CSV e agrupa por tipo: IPCA, PRE, PERC (%CDI), SPREAD (CDI+spread)."""
    grupos = {"IPCA": [], "PRE": [], "PERC": [], "SPREAD": []}
    for f in FLUXOS_DIR.glob("*.csv"):
        if f.name.startswith("_"):
            continue
        d = ler_csv(f.stem)
        if not d:
            continue
        idx = d["meta"].get("INDEXADOR", "")
        method = d["meta"].get("METHOD", "").upper()
        if idx == "IPCA":
            grupos["IPCA"].append(f.stem)
        elif idx == "PRE":
            grupos["PRE"].append(f.stem)
        elif idx == "CDI":
            if "PERC" in method:
                grupos["PERC"].append(f.stem)
            else:
                grupos["SPREAD"].append(f.stem)
    return grupos


def datas_teste(n=4) -> list[str]:
    d = dt_date(2026, 6, 12)
    out = []
    while len(out) < n:
        if d.weekday() < 5 and d not in _FER:
            out.append(d.isoformat())
        d -= timedelta(days=1)
    return out


def testar_ativo(ticker: str, datas: list[str]) -> list:
    res = []
    d0 = ler_csv(ticker)
    if not d0:
        return [(ticker, "-", "SEM CSV", None, None)]
    idx = d0["meta"].get("INDEXADOR", "")
    taxa_ref = float(d0["meta"].get("TAXA_REF", 0) or 0)
    # taxa de teste: exercita sensibilidade (CDI precisa taxa != ref)
    taxa_t = taxa_ref * 0.98 if idx == "CDI" and taxa_ref else (taxa_ref if taxa_ref else 5.0)
    if idx != "CDI":
        taxa_t = taxa_ref if taxa_ref else 5.0
    for data in datas:
        di = datetime.fromisoformat(data).date()
        try:
            # garante dados locais p/ a data (importa se faltar)
            d = ler_csv(ticker)
            precisa = (idx == "CDI" and data not in d["cdi"]) or (idx != "CDI" and data not in d["vna"])
            if precisa:
                importar_ticker(ticker, data)
                d = ler_csv(ticker)
            pu_local = calc_pu_local(d, taxa_t, di)
            pu_api = calc_pu_api(ticker, data, taxa_t).get("PU")
            dif = abs(pu_local - pu_api) if (pu_local and pu_api) else None
            res.append((ticker, data, f"{taxa_t:.4f}", pu_local, pu_api, dif))
        except Exception as e:
            res.append((ticker, data, "ERRO", None, str(e)[:40], None))
    return res


def main(tickers=None):
    datas = datas_teste(4)
    print(f"Datas de teste: {datas}\n")
    if tickers:
        sel = {"manual": tickers}
    else:
        grupos = classificar()
        print("Universo classificado:")
        for k, v in grupos.items():
            print(f"  {k}: {len(v)} ativos")
        sel = {k: v[:5] for k, v in grupos.items()}
        print()

    tot_ok = tot = 0
    for grupo, lst in sel.items():
        print(f"===== {grupo} =====")
        for tk in lst:
            for row in testar_ativo(tk, datas):
                if len(row) == 6 and row[5] is not None:
                    tk_, data, taxa, pl, pa, dif = row
                    ok = dif < 0.01
                    tot += 1; tot_ok += ok
                    flag = "OK " if ok else "XX "
                    print(f"  {flag}{tk_} {data} t={taxa} local={pl:.4f} api={pa:.4f} dif={dif:.6f}")
                else:
                    print(f"  ?? {row}")
    print(f"\n=== {tot_ok}/{tot} dentro de 0.01 ===")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args if args else None)
