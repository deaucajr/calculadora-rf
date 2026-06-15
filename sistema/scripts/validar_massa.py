"""
Valida PU local vs API B3 para 50 tickers de cada tipo (DEB, CRI, CRA)
em 5 datas uteis recentes. Reporta todos os casos fora de tolerancia.

Uso:
  python validar_massa.py              -- 50 de cada tipo, 5 datas
  python validar_massa.py --n 10       -- 10 de cada tipo
  python validar_massa.py --datas 3    -- 3 datas
"""
import sys, math, random, argparse
from datetime import date as dt_date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.paths import fluxos_dir
FLUXOS_DIR = fluxos_dir()
SEP = "\t"

from importar_fluxos import gerar_feriados
from src.api_client import calc_pu_api

_FER = set(gerar_feriados())

_IPCA_FAT = None

def _ipca_fatores():
    global _IPCA_FAT
    if _IPCA_FAT is not None:
        return _IPCA_FAT
    _IPCA_FAT = {}
    p = FLUXOS_DIR / "_ipca.csv"
    if p.exists():
        for ln in p.read_text(encoding="utf-8").splitlines():
            a = ln.split("\t")
            if len(a) >= 2:
                try:
                    _IPCA_FAT[a[0]] = float(a[1])
                except ValueError:
                    pass
    return _IPCA_FAT


def _vna_por_ipca(ancora_data, ancora_val, data):
    fat = _ipca_fatores()
    fa = fat.get(ancora_data.isoformat())
    fd = fat.get(data.isoformat())
    if fa and fd and fa != 0:
        return ancora_val * fd / fa
    return ancora_val


# ── helpers ────────────────────────────────────────────────────────────────────

def conta_du(d0, d1):
    if d1 <= d0:
        return 0
    n, d = 0, d0
    while d < d1:
        d += timedelta(days=1)
        if d.weekday() < 5 and d not in _FER:
            n += 1
    return n


def ler_csv(ticker):
    path = FLUXOS_DIR / f"{ticker}.csv"
    if not path.exists():
        return None
    meta, fluxo, vna, cdi = {}, [], {}, {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        p = ln.split(SEP)
        if p[0] == "META" and len(p) >= 3:
            meta[p[1]] = p[2]
        elif p[0] == "FLUXO" and len(p) >= 7:
            fluxo.append((datetime.fromisoformat(p[1]).date(), float(p[6])))
        elif p[0] == "VNA" and len(p) >= 3:
            vna[p[1]] = float(p[2])
        elif p[0] == "FLUXOD" and len(p) >= 7:
            cdi.setdefault(p[1], []).append((float(p[4]), float(p[5]), int(p[6])))
    return {"meta": meta, "fluxo": fluxo, "vna": vna, "cdi": cdi}


def vna_data(vna, data, indexador=""):
    di = data.isoformat()
    if di in vna:
        return vna[di]
    pts = sorted((datetime.fromisoformat(k).date(), v) for k, v in vna.items())
    if not pts:
        return None
    if len(pts) == 1:
        if indexador == "IPCA":
            return _vna_por_ipca(pts[0][0], pts[0][1], data)
        return pts[0][1]
    if data <= pts[0][0]:
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
    frac = conta_du(a[0], data) / duab if data >= a[0] else -conta_du(data, a[0]) / duab
    return a[1] * (b[1] / a[1]) ** frac


def _pu_perc_curva(bloco, p0, p1):
    pu, prev_du, ln_prev_fd0, ln_fdp1 = 0.0, 0, 0.0, 0.0
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


def calc_pu_local(d, taxa, data):
    idx = d["meta"].get("INDEXADOR", "")
    if idx == "CDI":
        di = data.isoformat()
        if di not in d["cdi"]:
            return None
        y0 = float(d["meta"]["TAXA_REF"])
        bloco = sorted(d["cdi"][di], key=lambda x: x[2])
        if y0 >= 50:
            pu = _pu_perc_curva(bloco, y0, taxa)
        else:
            pu = sum(pv * ((1 + y0 / 100) / (1 + taxa / 100)) ** (du / 252)
                     for vf, pv, du in bloco)
        return math.floor(pu * 1e6) / 1e6
    cot = sum(fc / (1 + taxa / 100) ** (conta_du(data, dt) / 252)
              for dt, fc in d["fluxo"] if conta_du(data, dt) > 0)
    v = vna_data(d["vna"], data, idx)
    if v is None:
        return None
    return math.floor(cot * v * 1e6) / 1e6


# ── classificacao ──────────────────────────────────────────────────────────────

def carregar_universo():
    """Retorna dict tipo -> lista de tickers com CSV valido."""
    grupos = {"DEB": [], "CRI": [], "CRA": []}
    for f in sorted(FLUXOS_DIR.glob("*.csv")):
        if f.name.startswith("_"):
            continue
        d = ler_csv(f.stem)
        if not d or not d["meta"]:
            continue
        tipo = d["meta"].get("TIPO", "").upper()
        if tipo in grupos:
            grupos[tipo].append(f.stem)
    return grupos


def datas_uteis_recentes(n):
    d = dt_date(2026, 6, 12)
    out = []
    while len(out) < n:
        if d.weekday() < 5 and d not in _FER:
            out.append(d.isoformat())
        d -= timedelta(days=1)
    return out


# ── teste ──────────────────────────────────────────────────────────────────────

def testar(ticker, datas):
    d = ler_csv(ticker)
    if not d:
        return []
    idx = d["meta"].get("INDEXADOR", "")
    taxa_ref = float(d["meta"].get("TAXA_REF", 0) or 0)
    taxa_t = taxa_ref if taxa_ref else 5.0
    # Para CDI usa a taxa de referência exata (para comparar PU base)
    resultados = []
    for data in datas:
        di = datetime.fromisoformat(data).date()
        try:
            pu_local = calc_pu_local(d, taxa_t, di)
            resp = calc_pu_api(ticker, data, taxa_t)
            pu_api = resp.get("PU") if resp else None
            if pu_local is None or pu_api is None:
                resultados.append((ticker, data, idx, taxa_t, pu_local, pu_api, None, "SEM_DADO"))
            else:
                dif = abs(pu_local - pu_api)
                status = "OK" if dif < 0.01 else "FALHA"
                resultados.append((ticker, data, idx, taxa_t, pu_local, pu_api, dif, status))
        except Exception as e:
            resultados.append((ticker, data, idx, taxa_t, None, None, None, f"ERRO:{str(e)[:60]}"))
    return resultados


# ── main ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n",     type=int, default=50, help="tickers por tipo (default 50)")
    ap.add_argument("--datas", type=int, default=5,  help="datas de teste (default 5)")
    ap.add_argument("--tipo",  default=None,          help="filtra tipo: DEB, CRI ou CRA")
    ap.add_argument("--seed",  type=int, default=42,  help="seed para selecao aleatoria")
    args = ap.parse_args()

    random.seed(args.seed)
    datas = datas_uteis_recentes(args.datas)
    print(f"Datas: {datas}")

    universo = carregar_universo()
    for t, lst in universo.items():
        print(f"  {t}: {len(lst)} tickers no universo")
    print()

    tipos = [args.tipo.upper()] if args.tipo else ["DEB", "CRI", "CRA"]

    total_ok = total = falhas = 0
    linhas_falha = []

    for tipo in tipos:
        lst = universo.get(tipo, [])
        sel = random.sample(lst, min(args.n, len(lst)))
        print(f"{'='*70}")
        print(f"TIPO: {tipo}  ({len(sel)} tickers x {len(datas)} datas = {len(sel)*len(datas)} pontos)")
        print(f"{'='*70}")

        tipo_ok = tipo_tot = 0
        for tk in sel:
            rows = testar(tk, datas)
            for r in rows:
                tk_, data, idx, taxa, pl, pa, dif, status = r
                total += 1
                tipo_tot += 1
                if status == "OK":
                    total_ok += 1
                    tipo_ok += 1
                elif status == "FALHA":
                    falhas += 1
                    linhas_falha.append(r)
                    print(f"  FALHA  {tk_} {data} [{idx} {taxa:.4f}%]  local={pl:.6f}  b3={pa:.6f}  dif={dif:.6f}")
                else:
                    print(f"  {status:<8} {tk_} {data}")

        pct = 100 * tipo_ok / tipo_tot if tipo_tot else 0
        print(f"  -> {tipo_ok}/{tipo_tot} OK ({pct:.1f}%)\n")

    print(f"{'='*70}")
    print(f"RESULTADO FINAL: {total_ok}/{total} OK  |  {falhas} falhas")
    if linhas_falha:
        print(f"\nTICKERS COM FALHA:")
        vistos = set()
        for r in linhas_falha:
            tk = r[0]
            if tk not in vistos:
                vistos.add(tk)
                idx = r[2]
                difs = [x[6] for x in linhas_falha if x[0] == tk and x[6] is not None]
                max_dif = max(difs) if difs else 0
                print(f"  {tk}  [{idx}]  max_dif={max_dif:.6f}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
