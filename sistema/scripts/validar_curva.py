"""
Valida o motor de precificacao CDI baseado na curva DI x Pre da B3.

Ideia (ancoragem no bloco validado):
  Para uma data D, ancoramos no bloco da DATA_FLUXO (D0, ja validado 80/80) e
  movemos so o "delta" via curva da B3 + recalculo de dias uteis. Em D=D0 o
  resultado e IDENTICO ao atual por construcao -> serve de prova de corretude.

Tipos:
  DI-SPREAD (y0<50, CDI+spread): a projecao/desconto DI se cancelam; preco em D =
     pv0 * R * ((1+y0)/(1+taxa))^(duD/252), com R movendo a data via curva.
  DI-PERC  (y0>=50, %CDI): nao cancela; reconstroi bloco sintetico em D (vf,pv,du)
     e aplica o MESMO PvCdi (forward CDI da curva da B3).
"""
import glob
import math
from datetime import date, timedelta
from pathlib import Path

FLUXOS = Path(__file__).resolve().parent.parent / "data" / "fluxos"

# ---------- calendario / dias uteis (espelha ContaDU do VBA) ----------
_FER = set()
for ln in (FLUXOS / "_feriados.csv").read_text(encoding="utf-8").splitlines():
    ln = ln.strip()
    if ln:
        y, m, d = ln.split("-")
        _FER.add(date(int(y), int(m), int(d)))

def bdays(d0: date, d1: date) -> int:
    """Dias uteis em (d0, d1]  (igual ao ContaDU do add-in)."""
    if d1 <= d0:
        return 0
    n = 0
    d = d0 + timedelta(days=1)
    while d <= d1:
        if d.weekday() < 5 and d not in _FER:
            n += 1
        d += timedelta(days=1)
    return n

# ---------- curva DI da B3 ----------
_CURVAS: dict[str, list[tuple[int, float]]] = {}
for ln in (FLUXOS / "_curva_di.csv").read_text(encoding="utf-8").splitlines():
    p = ln.split("\t")
    if len(p) == 3:
        _CURVAS.setdefault(p[0], []).append((int(p[1]), float(p[2])))
for k in _CURVAS:
    _CURVAS[k].sort()

def _fd_di(curva, x: float) -> float:
    """Fator DI (crescimento) a 100% CDI ate du=x, interp log-linear no fator."""
    dus = [d for d, _ in curva]
    rates = {d: r for d, r in curva}
    if x <= dus[0]:
        r = rates[dus[0]]; return (1 + r / 100) ** (x / 252)
    if x >= dus[-1]:
        r = rates[dus[-1]]; return (1 + r / 100) ** (x / 252)
    import bisect
    i = bisect.bisect_left(dus, x)
    if dus[i] == x:
        r = rates[x]; return (1 + r / 100) ** (x / 252)
    a, b = dus[i - 1], dus[i]
    fa = (1 + rates[a] / 100) ** (a / 252)
    fb = (1 + rates[b] / 100) ** (b / 252)
    return fa * (fb / fa) ** ((x - a) / (b - a))

def _fd_pct(curva, x: float, pct: float) -> float:
    """Fator a pct% do CDI ate du=x: reconstroi CDI forward da curva e reaplica pct."""
    if x <= 0:
        return 1.0
    dus = [d for d, _ in curva]
    # vertices ate x (+ ponto final x)
    pts = [d for d in dus if d < x] + [x]
    fd = 1.0
    prev = 0
    ln_prev = 0.0
    for v in pts:
        ln_v = math.log(_fd_di(curva, v))
        dseg = v - prev
        if dseg > 0:
            cdi_d = math.exp((ln_v - ln_prev) / dseg) - 1     # CDI diario do segmento
            fd *= (1 + pct / 100 * cdi_d) ** dseg
            prev = v
            ln_prev = ln_v
    return fd

# ---------- leitura de ativo ----------
def ler_ativo(path):
    meta = {}
    blocos = {}  # data_calc -> [(event_date, vf, pv, du)]
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        p = ln.split("\t")
        if p[0] == "META" and len(p) >= 3:
            meta[p[1]] = p[2]
        elif p[0] == "FLUXOD" and len(p) >= 7:
            y, m, d = p[2].split("-")
            blocos.setdefault(p[1], []).append(
                (date(int(y), int(m), int(d)), float(p[4]), float(p[5]), int(p[6])))
    return meta, blocos

# ---------- PvCdi de referencia (port exato do VBA) ----------
def pvcdi_ref(cf, y0, taxa):
    """cf = [(event,vf,pv,du)] ordenado por du. Retorna lista de PVs."""
    out = []
    if y0 >= 50:
        prev = 0; ln_prev = 0.0; ln_fp = 0.0
        for (_, vf, pv, du) in cf:
            ln0 = math.log(vf / pv)
            dseg = du - prev
            if dseg > 0:
                g = (math.exp((ln0 - ln_prev) / dseg) - 1) * 100 / y0
                ln_fp += math.log(1 + g * taxa / 100) * dseg
                prev = du; ln_prev = ln0
            out.append(vf / math.exp(ln_fp))
    else:
        for (_, vf, pv, du) in cf:
            out.append(pv * ((1 + y0 / 100) / (1 + taxa / 100)) ** (du / 252))
    return out

# ---------- preco na DATA_FLUXO (modelo atual) ----------
def pu_atual(meta, blocos, taxa):
    d0 = meta["DATA_FLUXO"]
    cf = sorted(blocos[d0], key=lambda r: r[3])
    y0 = float(meta["TAXA_REF"])
    return sum(pvcdi_ref(cf, y0, taxa))

# ---------- NOVO: preco em data D arbitraria via curva ----------
def pu_curva(meta, blocos, taxa, D: date):
    d0s = meta["DATA_FLUXO"]
    y, m, d = d0s.split("-"); D0 = date(int(y), int(m), int(d))
    cf0 = sorted(blocos[d0s], key=lambda r: r[3])
    y0 = float(meta["TAXA_REF"])
    Diso = D.isoformat()
    if Diso not in _CURVAS or d0s not in _CURVAS:
        return None
    cD, c0 = _CURVAS[Diso], _CURVAS[d0s]

    # delta de dias uteis entre D e D0 (ancora no du0 gravado, como o add-in)
    desloc = -bdays(D0, D) if D >= D0 else bdays(D, D0)
    cf_D = []
    for (ev, vf0, pv0, du0) in cf0:
        duD = du0 + desloc
        if duD <= 0:
            continue
        if y0 >= 50:  # DI-PERC: bloco sintetico
            rv = _fd_di(cD, duD) / _fd_di(c0, du0)
            rp = _fd_pct(cD, duD, y0) / _fd_pct(c0, du0, y0)
            cf_D.append((ev, vf0 * rv, pv0 * rp, duD))
        else:         # DI-SPREAD: pv movido pela curva (DI+spread)
            r = (_fd_di(c0, du0) / _fd_di(cD, duD)) * (1 + y0 / 100) ** ((du0 - duD) / 252)
            cf_D.append((ev, vf0, pv0 * r, duD))
    cf_D.sort(key=lambda r: r[3])
    return sum(pvcdi_ref(cf_D, y0, taxa))


if __name__ == "__main__":
    # 1) checagem do calendario: du recalculado em D0 deve bater com o armazenado
    print("=== checagem calendario (du recalc vs armazenado em D0) ===")
    ok_cal = tot = 0
    amostra = sorted(glob.glob(str(FLUXOS / "*.csv")))
    for path in amostra:
        if Path(path).name.startswith("_"):
            continue
        meta, blocos = ler_ativo(path)
        if meta.get("INDEXADOR") != "CDI" or "DATA_FLUXO" not in meta:
            continue
        d0s = meta["DATA_FLUXO"]
        if d0s not in blocos:
            continue
        y, m, d = d0s.split("-"); D0 = date(int(y), int(m), int(d))
        for (ev, vf, pv, du) in blocos[d0s]:
            tot += 1
            if bdays(D0, ev) == du:
                ok_cal += 1
        if tot >= 200:
            break
    print(f"  {ok_cal}/{tot} dus batem exatamente\n")

    # 2) exatidao em D0 e precos em datas anteriores, p/ varios ativos CDI
    print("=== precos: atual(D0) vs curva(D0) [deve bater] + datas passadas ===")
    n = 0
    for path in amostra:
        if Path(path).name.startswith("_"):
            continue
        meta, blocos = ler_ativo(path)
        if meta.get("INDEXADOR") != "CDI" or "DATA_FLUXO" not in meta:
            continue
        d0s = meta["DATA_FLUXO"]
        if d0s not in blocos or len(blocos[d0s]) < 2:
            continue
        y0 = float(meta["TAXA_REF"])
        taxa = y0  # precifica na taxa de referencia
        pa = pu_atual(meta, blocos, taxa)
        y, m, d = d0s.split("-"); D0 = date(int(y), int(m), int(d))
        pc0 = pu_curva(meta, blocos, taxa, D0)
        tipo = "PERC" if y0 >= 50 else "SPREAD"
        diff = abs(pa - pc0) / pa * 1e4 if pc0 else float("nan")
        # uma data anterior com curva
        datas = sorted([k for k in _CURVAS if k < d0s], reverse=True)
        pant = pu_curva(meta, blocos, taxa, date.fromisoformat(datas[0])) if datas else None
        print(f"  {meta['TICKER']:<12} {tipo:<6} y0={y0:>5}  atual={pa:12.6f}  "
              f"curva(D0)={pc0:12.6f}  dif={diff:6.3f}bps  "
              f"{datas[0] if datas else '--'}={pant:12.6f}" if pant else
              f"  {meta['TICKER']:<12} {tipo:<6} y0={y0:>5}  atual={pa:12.6f}  curva(D0)={pc0:12.6f}  dif={diff:6.3f}bps")
        n += 1
        if n >= 12:
            break
