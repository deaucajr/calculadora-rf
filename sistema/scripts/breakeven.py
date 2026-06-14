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


def fluxo_call(cf, y0, cD, vne, call_date: date, premio_pct: float):
    """Constroi o fluxo de pre-pagamento: cupons ate a call + resgate na call."""
    mat = max(cf, key=lambda r: r[3])           # evento de vencimento (maior du)
    mat_du, mat_dt = mat[3], mat[0]
    du_call = mat_du - V.bdays(call_date, mat_dt)
    if du_call <= 0:
        raise ValueError("call_date fora do prazo do papel")
    # cupons pagos ATE a call (exclui o que vence depois, inclui amortizacao parcial <= call)
    base = [r for r in cf if r[3] <= du_call and r[0] <= call_date]
    # resgate antecipado = principal em aberto * (1 + premio)   [bullet: principal = VNE]
    R = vne * (1 + premio_pct / 100.0)
    pv_R = R / (V._fd_di(cD, float(du_call)) * (1 + y0 / 100) ** (du_call / 252))
    return base + [(call_date, R, pv_R, du_call)]


def breakeven(ticker, call_date, premio_pct, D=None, lo=-5.0, hi=60.0):
    """Spread X tal que PV_real(X) == PV_call(X). Retorna (X, pv_real, pv_call, y0)."""
    meta, blocos = V.ler_ativo(str(ROOT / "data" / "fluxos" / f"{ticker}.csv"))
    Diso = _ultima_data_curva() if D is None else D
    Dd = date.fromisoformat(Diso) if isinstance(Diso, str) else Diso
    cf, y0, cD = bloco_sintetico(meta, blocos, Dd)
    vne = float(meta.get("VNE", 1000.0))
    cd = date.fromisoformat(call_date) if isinstance(call_date, str) else call_date
    cf_call = fluxo_call(cf, y0, cD, vne, cd, premio_pct)

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
    # 5 CDI+ bullet. call_date/premio sao ILUSTRATIVOS (call ~2 anos antes do
    # vencimento, premio de exemplo) — trocar pelos valores reais p/ validar.
    # 5 CDI+ bullet limpos (com cupons, PV ~ par). Premio 1% e call ~2 anos antes
    # do vencimento sao SO placeholders — trocar pelos reais (ANBIMA/escritura).
    tickers = [("AALM12", 1.0), ("ABFR14", 1.0), ("ACHE14", 1.0),
               ("ACHE15", 1.0), ("ACOV15", 1.0)]
    print(f"{'TICKER':<9}{'spread%':>8}{'venc':>12}{'call(ex)':>12}{'prem%':>6}"
          f"{'PV@spread':>11}{'PV_call':>10}{'BREAKEVEN%':>11}")
    for tk, prem in tickers:
        try:
            meta, blocos = V.ler_ativo(str(ROOT / "data" / "fluxos" / f"{tk}.csv"))
            venc = max(sorted(blocos[meta["DATA_FLUXO"]], key=lambda r: r[3]))[0].isoformat()
            cdt = _call_exemplo(meta, blocos)
            X, pr, pc, y0 = breakeven(tk, cdt, prem)
            # sanity: PV ao spread contratual deve ficar ~par
            par = breakeven.__globals__["pv"]
            cf, _, _ = bloco_sintetico(meta, blocos, date.fromisoformat(_ultima_data_curva()))
            pv_par = par(cf, y0, y0)
            print(f"{tk:<9}{y0:>8}{venc:>12}{cdt:>12}{prem:>6}"
                  f"{pv_par:>11.2f}{pc:>10.2f}{X:>11.4f}")
        except Exception as e:
            print(f"{tk:<9}  ERRO: {e}")
