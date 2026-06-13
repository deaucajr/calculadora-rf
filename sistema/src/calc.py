"""
Motor de cálculo local de PU, yield e duration.

Estratégia:
  1. Usa o flow_cache (calcPU da API) quando disponível para a data.
  2. Para yield diferente do ref_yield: aplica ajuste marginal sobre presentValues.
     Fórmula: PV_i(y1) = PV_i(y0) × ((1+y0/100)/(1+y1/100))^(du_i/252)
     Isso isola o spread da parte CDI (que permanece no presentValue base).
  3. Para manual_bonds: desconto direto dos finalValues (sem CDI embutido).

1 chamada API por dia por papel → cálculos ilimitados de yield/PU localmente.
"""
from datetime import date as dt_date
from scipy.optimize import brentq
from .db import get_conn


def _load_flows(ticker: str, calc_date: str) -> list[dict]:
    """Busca fluxos do cache. Retorna lista com final_value, present_value, working_days, ref_yield."""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT event_date, event_type, final_value, present_value,
                   working_days, vna, ref_yield
            FROM flow_cache
            WHERE ticker = ? AND calc_date = ?
            ORDER BY working_days
        """, (ticker, calc_date)).fetchall()

        if not rows:
            rows = conn.execute("""
                SELECT fc.event_date, fc.event_type, fc.final_value, fc.present_value,
                       fc.working_days, fc.vna, fc.ref_yield
                FROM flow_cache fc
                WHERE fc.ticker = ?
                  AND fc.calc_date = (
                    SELECT MAX(calc_date) FROM flow_cache
                    WHERE ticker = ? AND calc_date <= ?
                  )
                ORDER BY fc.working_days
            """, (ticker, ticker, calc_date)).fetchall()

    if not rows:
        return []
    return [dict(r) for r in rows]


def _load_manual_flows(ticker: str) -> list[dict]:
    """Fluxos de papéis inseridos manualmente."""
    with get_conn() as conn:
        bond = conn.execute(
            "SELECT * FROM manual_bonds WHERE ticker = ?", (ticker,)
        ).fetchone()
        if not bond:
            return []

        flows = conn.execute("""
            SELECT event_date, event_type, value_pct, value_abs
            FROM manual_flows
            WHERE ticker = ?
            ORDER BY event_date
        """, (ticker,)).fetchall()

    today = dt_date.today().isoformat()
    result = []
    for f in flows:
        if f["event_date"] < today:
            continue
        if f["value_abs"]:
            fv = float(f["value_abs"])
        elif f["value_pct"]:
            vna = dict(bond).get("vna_inicial", 1000) or 1000
            fv = float(f["value_pct"]) / 100 * vna
        else:
            continue
        wd = _approx_bdays(today, f["event_date"])
        result.append({
            "event_date": f["event_date"],
            "event_type": f["event_type"],
            "final_value": fv,
            "working_days": wd,
        })
    return result


def _approx_bdays(start: str, end: str) -> int:
    from datetime import datetime
    d0 = datetime.fromisoformat(start)
    d1 = datetime.fromisoformat(end)
    return max(1, int((d1 - d0).days * 252 / 365))


def _pu_from_flows(flows: list[dict], yield_pct: float) -> float:
    """
    PU ajustado para novo yield partindo dos presentValues armazenados.

    Para papéis DI-SPREAD, o presentValue já inclui o desconto CDI.
    Ao mudar o spread de y0 para y1, o ajuste marginal é:
        PV_i(y1) = PV_i(y0) × ((1+y0/100) / (1+y1/100))^(du_i/252)

    Para papéis manuais (sem present_value), faz desconto direto do final_value.
    """
    total = 0.0
    for f in flows:
        t = f["working_days"] / 252
        pv0 = f.get("present_value")
        y0 = f.get("ref_yield")
        if pv0 is not None and y0 is not None:
            # Ajuste marginal: substitui só o desconto do spread
            adj = ((1 + y0 / 100) / (1 + yield_pct / 100)) ** t
            total += pv0 * adj
        else:
            # Fallback: desconto direto (papéis manuais ou legado)
            total += f["final_value"] / (1 + yield_pct / 100) ** t
    return total


def _duration_from_flows(flows: list[dict], yield_pct: float) -> float:
    pu = _pu_from_flows(flows, yield_pct)
    if pu <= 0:
        return 0.0
    total_num = 0.0
    for f in flows:
        t = f["working_days"] / 252
        pv0 = f.get("present_value")
        y0 = f.get("ref_yield")
        if pv0 is not None and y0 is not None:
            adj = ((1 + y0 / 100) / (1 + yield_pct / 100)) ** t
            pv_i = pv0 * adj
        else:
            pv_i = f["final_value"] / (1 + yield_pct / 100) ** t
        total_num += t * pv_i
    return total_num / pu


def _fetch_and_cache(ticker: str, calc_date: str, yield_ref: float | None = None) -> str:
    """Chama calcPU da API para uma data específica e salva no cache. Retorna source string."""
    from .api_client import calc_pu_api
    with get_conn() as conn:
        row = conn.execute(
            "SELECT yield_contract FROM bonds WHERE ticker=?", (ticker,)
        ).fetchone()
    y = yield_ref or (float(row["yield_contract"]) if row else 0.0)

    result = calc_pu_api(ticker, calc_date, y)
    flows = result.get("cashFlowList", [])
    vna = result.get("VNA")
    method = result.get("method")

    with get_conn() as conn:
        conn.execute(
            "DELETE FROM flow_cache WHERE ticker=? AND calc_date=?",
            (ticker, calc_date)
        )
        for f in flows:
            conn.execute("""
                INSERT OR IGNORE INTO flow_cache
                  (ticker, calc_date, ref_yield, event_date, event_type,
                   final_value, present_value, working_days, vna, method)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                ticker, calc_date, y,
                f["date"], f["eventType"],
                f["finalValue"], f["presentValue"], f["workingDays"],
                vna, method,
            ))
    return f"api:{calc_date}"


def calc_pu(
    ticker: str,
    yield_pct: float,
    calc_date: str | None = None,
    fetch_if_missing: bool = True,
) -> dict:
    """
    Calcula PU e duration para um ticker dado uma yield (spread DI em % a.a.).

    calc_date : YYYY-MM-DD (padrão = hoje)
    fetch_if_missing : se True e não há cache para a data, chama a API automaticamente.

    Retorna: {PU, duration, yield, vna, source, calc_date, ticker}
    """
    if calc_date is None:
        calc_date = dt_date.today().isoformat()

    flows = _load_flows(ticker, calc_date)
    source = "cache"

    if not flows and fetch_if_missing:
        try:
            source = _fetch_and_cache(ticker, calc_date)
            flows = _load_flows(ticker, calc_date)
        except Exception:
            pass

    if not flows:
        flows = _load_manual_flows(ticker)
        source = "manual"

    if not flows:
        raise ValueError(
            f"Sem fluxos para '{ticker}' em {calc_date}. "
            "Execute sync_flows, registre o ativo ou adicione fluxos manualmente."
        )

    pu = _pu_from_flows(flows, yield_pct)
    dur = _duration_from_flows(flows, yield_pct)
    vna = flows[0].get("vna") if flows else None

    return {
        "ticker": ticker,
        "calc_date": calc_date,
        "yield": yield_pct,
        "PU": round(pu, 6),
        "duration": round(dur, 6),
        "vna": vna,
        "source": source,
        "n_flows": len(flows),
    }


def calc_yield(
    ticker: str,
    pu_target: float,
    calc_date: str | None = None,
    fetch_if_missing: bool = True,
) -> dict:
    """
    Dado um PU e uma data, calcula a yield implícita.
    Usa bissecção (brentq) no intervalo 0.01% a 99%.
    """
    if calc_date is None:
        calc_date = dt_date.today().isoformat()

    flows = _load_flows(ticker, calc_date)
    source = "cache"

    if not flows and fetch_if_missing:
        try:
            source = _fetch_and_cache(ticker, calc_date)
            flows = _load_flows(ticker, calc_date)
        except Exception:
            pass

    if not flows:
        flows = _load_manual_flows(ticker)
        source = "manual"

    if not flows:
        raise ValueError(f"Sem fluxos para '{ticker}' em {calc_date}.")

    def diff(y):
        return _pu_from_flows(flows, y) - pu_target

    try:
        y = brentq(diff, 0.01, 99.0, xtol=1e-8, maxiter=100)
    except ValueError:
        raise ValueError(
            f"Não foi possível encontrar yield para PU={pu_target:.4f} "
            f"(PU máx={_pu_from_flows(flows, 0.01):.2f}, "
            f"PU mín={_pu_from_flows(flows, 99.0):.2f})"
        )

    pu = _pu_from_flows(flows, y)
    dur = _duration_from_flows(flows, y)
    vna = flows[0].get("vna") if flows else None

    return {
        "ticker": ticker,
        "calc_date": calc_date,
        "yield": round(y, 6),
        "PU": round(pu, 6),
        "duration": round(dur, 6),
        "vna": vna,
        "source": source,
        "n_flows": len(flows),
    }


def bond_info(ticker: str) -> dict | None:
    """Retorna metadados do papel (tabela bonds ou manual_bonds)."""
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM bonds WHERE ticker=?", (ticker,)).fetchone()
        if row:
            return dict(row)
        row = conn.execute(
            "SELECT * FROM manual_bonds WHERE ticker=?", (ticker,)
        ).fetchone()
        return dict(row) if row else None
