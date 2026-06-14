#!/usr/bin/env python
"""
Break-even de pre-pagamento (call) para papeis CDI+ (DI-SPREAD).

Ideia: o emissor pode resgatar antecipadamente numa data de call pagando o
principal em aberto + um premio. Monta-se dois fluxos:
  * REAL      : cupons + amortizacoes ate o VENCIMENTO.
  * PRE-PAGTO : cupons ate a data de CALL + resgate (principal*(1+premio)) na call.
O BREAK-EVEN e o spread X (sobre o CDI) no qual PV_real(X) == PV_call(X) — a taxa
de indiferenca entre levar ao vencimento e ser pre-pago.

Usa SO dados locais (CSV de fluxo + curva DI x Pre da B3 ja baixada) — zero API.
Reaproveita o pricer validado em validar_curva (mesmo motor do add-in).

NOTA: a convencao do premio (flat % do principal vs % a.a. pro-rata) vem da
escritura/ANBIMA. Por ora 'premio_pct' = acrescimo flat sobre o principal:
resgate = VNE*(1+premio_pct/100). Ajustavel quando tivermos o dado real.
"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import validar_curva as V


def _ultima_data_curva() -> str:
    return max(V._CURVAS)


def bloco_sintetico(meta, blocos, D: date):
    """cf_D = [(ev, vf, pv, du)] na data D (mesma construcao do add-in), + y0 e curva."""
    d0s = meta["DATA_FLUXO"]
    y, m, dd = d0s.split("-")
    D0 = date(int(y), int(m), int(dd))
    cf0 = sorted(blocos[d0s], key=lambda r: r[3])
    y0 = float(meta["TAXA_REF"])
    cD, c0 = V._CURVAS[D.isoformat()], V._CURVAS[d0s]
    desloc = -V.bdays(D0, D) if D >= D0 else V.bdays(D, D0)
    cf = []
    for (ev, vf0, pv0, du0) in cf0:
        duD = du0 + desloc
        if duD <= 0:
            continue
        if y0 >= 50:   # %CDI (DI-PERC)
            rv = V._fd_di(cD, duD) / V._fd_di(c0, du0)
            rp = V._fd_pct(cD, duD, y0) / V._fd_pct(c0, du0, y0)
            cf.append((ev, vf0 * rv, pv0 * rp, duD))
        else:          # CDI+ (DI-SPREAD)
            r = (V._fd_di(c0, du0) / V._fd_di(cD, duD)) * (1 + y0 / 100) ** ((du0 - duD) / 252)
            cf.append((ev, vf0, pv0 * r, duD))
    cf.sort(key=lambda r: r[3])
    return cf, y0, cD


def pv(cf, y0, X):
    """PV (PU) do bloco cf ao spread/percentual X."""
    return sum(V.pvcdi_ref(cf, y0, X))


def amortizacoes(ticker):
    """Cronograma de amortizacao do CSV: lista (data_evento, face). 'A' = amort."""
    path = ROOT / "data" / "fluxos" / f"{ticker}.csv"
    meta = {}
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        c = ln.split("\t")
        if c[0] == "META" and len(c) >= 3:
            meta[c[1]] = c[2]
        elif c[0] == "FLUXOD" and len(c) >= 7 and c[1] == meta.get("DATA_FLUXO") and c[3] == "A":
            y, m, d = c[2].split("-")
            out.append((date(int(y), int(m), int(d)), float(c[4])))
    return out


def fluxo_call(cf, y0, cD, amorts, call_date: date, premio_pct: float, conv="aa"):
    """Constroi o fluxo de pre-pagamento: fluxo real ate a call + resgate do SALDO
    EM ABERTO na call (com premio). 'amorts' = [(data, face)] do cronograma.
    conv: 'aa' = premio % a.a. compondo no prazo remanescente;
          'aa_linear' = premio % a.a. linear; 'flat' = acrescimo flat."""
    mat = max(cf, key=lambda r: r[3])
    mat_du, mat_dt = mat[3], mat[0]
    du_call = mat_du - V.bdays(call_date, mat_dt)
    if du_call <= 0:
        raise ValueError("call_date fora do prazo do papel")
    base = [r for r in cf if r[3] <= du_call and r[0] <= call_date]
    rem = mat_du - du_call
    if conv == "aa":
        fator = (1 + premio_pct / 100) ** (rem / 252)
    elif conv == "aa_linear":
        fator = 1 + premio_pct / 100 * (rem / 252)
    else:
        fator = 1 + premio_pct / 100
    saldo = sum(face for d, face in amorts if d > call_date)   # principal ainda nao amortizado
    R = saldo * fator                                          # resgate = saldo * fator do premio
    pv_R = R / (V._fd_di(cD, float(du_call)) * (1 + y0 / 100) ** (du_call / 252))
    return base + [(call_date, R, pv_R, du_call)], fator, saldo


def breakeven(ticker, call_date, premio_pct, conv="aa", D=None, lo=-5.0, hi=60.0):
    """Spread X tal que PV_real(X) == PV_call(X). Retorna (X, pv_real, pv_call, y0)."""
    meta, blocos = V.ler_ativo(str(ROOT / "data" / "fluxos" / f"{ticker}.csv"))
    Diso = _ultima_data_curva() if D is None else D
    Dd = date.fromisoformat(Diso) if isinstance(Diso, str) else Diso
    cf, y0, cD = bloco_sintetico(meta, blocos, Dd)
    cd = date.fromisoformat(call_date) if isinstance(call_date, str) else call_date
    cf_call, fator, saldo = fluxo_call(cf, y0, cD, amortizacoes(ticker), cd, premio_pct, conv)

    f = lambda X: pv(cf, y0, X) - pv(cf_call, y0, X)
    a, b = lo, hi
    fa = f(a)
    for _ in range(200):
        mid = (a + b) / 2
        fm = f(mid)
        if fa * fm <= 0:
            b = mid
        else:
            a, fa = mid, fm
        if b - a < 1e-7:
            break
    X = (a + b) / 2
    return X, pv(cf, y0, X), pv(cf_call, y0, X), y0


def _call_exemplo(meta, blocos, anos_antes=2):
    """Escolhe uma data de cupom ~anos_antes do vencimento (call ilustrativa)."""
    from datetime import timedelta
    d0s = meta["DATA_FLUXO"]
    cf0 = sorted(blocos[d0s], key=lambda r: r[3])
    venc = max(cf0, key=lambda r: r[3])[0]
    alvo = venc - timedelta(days=365 * anos_antes)
    cupons = [r[0] for r in cf0 if r[0] < venc]
    if not cupons:
        return None
    return min(cupons, key=lambda d: abs((d - alvo).days)).isoformat()


if __name__ == "__main__":
    # Dados REAIS informados (call_date, premio %a.a., convencao). ABFR14: ano da
    # call assumido 2027 (cliente nao informou) -> revisar.
    casos = [
        ("AALM12", "2027-10-02", 1.50, "aa"),         # 1,50% a.a.
        ("ABFR14", "2027-10-16", 1.41, "aa"),         # 1,41% a.a. (ano assumido)
        ("ACHE14", "2027-08-15", 0.30, "aa_linear"),  # 0,30% a.a. flat
        ("ACHE15", "2027-08-15", 0.30, "aa_linear"),  # 0,30% a.a. flat
        ("ACOV15", "2027-06-10", 0.30, "aa_linear"),  # 0,30% a.a. flat
    ]
    def resolve(g, lo=-10.0, hi=80.0):       # bisseccao p/ g(X)=0
        a, b, fa = lo, hi, g(lo)
        for _ in range(200):
            mid = (a + b) / 2
            fm = g(mid)
            if fa * fm <= 0:
                b = mid
            else:
                a, fa = mid, fm
            if b - a < 1e-7:
                break
        return (a + b) / 2

    print(f"{'TICKER':<8}{'spr%':>6}{'venc':>12}{'call':>12}{'prm%aa':>7}{'conv':>10}"
          f"{'saldo':>8}{'PV@spr':>9}{'BE_indif':>10}{'BE_ytc':>9}")
    for tk, cdt, prem, conv in casos:
        try:
            meta, blocos = V.ler_ativo(str(ROOT / "data" / "fluxos" / f"{tk}.csv"))
            venc = max(sorted(blocos[meta["DATA_FLUXO"]], key=lambda r: r[3]))[0].isoformat()
            cf, y0, cD = bloco_sintetico(meta, blocos, date.fromisoformat(_ultima_data_curva()))
            P = pv(cf, y0, y0)                                   # preco ao spread contratual
            cf_call, fator, saldo = fluxo_call(cf, y0, cD, amortizacoes(tk),
                                               date.fromisoformat(cdt), prem, conv)
            be_indif = resolve(lambda X: pv(cf, y0, X) - pv(cf_call, y0, X))  # PV_real=PV_call
            be_ytc = resolve(lambda X: pv(cf_call, y0, X) - P)               # yield-to-call ao preco P
            print(f"{tk:<8}{y0:>6}{venc:>12}{cdt:>12}{prem:>7}{conv:>10}"
                  f"{saldo:>8.1f}{P:>9.2f}{be_indif:>10.4f}{be_ytc:>9.4f}")
        except Exception as e:
            print(f"{tk:<8}  ERRO: {e}")
