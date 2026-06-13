"""
Calcula o VNA (Valor Nominal Atualizado) para papéis IPCA e CDI.
Segue a convenção ANBIMA: pro-rata por dias úteis no mês corrente.
"""
from datetime import date as dt_date, datetime
from dateutil.relativedelta import relativedelta
from .db import get_conn


def get_ipca_monthly(start_date: str, end_date: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT date, rate_pct FROM ipca_monthly
            WHERE date >= ? AND date <= ?
            ORDER BY date
        """, (start_date, end_date)).fetchall()
    return [{"date": r["date"], "rate_pct": float(r["rate_pct"])} for r in rows]


def get_ipca_projection(month: str) -> float | None:
    """Retorna projeção IPCA para um mês (YYYY-MM), mais recente disponível."""
    with get_conn() as conn:
        row = conn.execute("""
            SELECT rate_pct FROM ipca_projections
            WHERE month = ?
            ORDER BY ref_date DESC LIMIT 1
        """, (month,)).fetchone()
    return float(row["rate_pct"]) if row else None


def _business_days_in_month(year: int, month: int) -> int:
    """Aproximação ANBIMA: 21 dias úteis por mês."""
    return 21


def _business_days_elapsed(year: int, month: int, day_date: dt_date) -> int:
    """Dias úteis decorridos no mês até a data (aproximação por calendário corrido × 252/365)."""
    first = dt_date(year, month, 1)
    return max(1, int((day_date - first).days * 252 / 365))


def calc_vna_ipca(vne: float, base_date: str, calc_date: str) -> float:
    """
    Calcula VNA de um papel IPCA.

    vne        : Valor Nominal de Emissão (ou VNA na data de emissão)
    base_date  : data-base de atualização (YYYY-MM-DD)
    calc_date  : data de cálculo (YYYY-MM-DD)

    Fórmula (convenção ANBIMA):
      VNA(t) = VNE × Π (1 + IPCA_m)^(du_m / total_du_m)

    Meses completos: IPCA publicado.
    Mês corrente (parcial): usa projeção ANBIMA pro-rata.
    """
    base = datetime.fromisoformat(base_date).date()
    calc = datetime.fromisoformat(calc_date).date()

    if calc <= base:
        return vne

    factor = 1.0
    cursor = dt_date(base.year, base.month, 1)

    while cursor <= calc:
        year, month = cursor.year, cursor.month
        month_str = cursor.strftime("%Y-%m")
        # Último dia do mês
        last_day = (cursor + relativedelta(months=1)) - relativedelta(days=1)

        if last_day < base:
            cursor = cursor + relativedelta(months=1)
            continue

        total_du = _business_days_in_month(year, month)

        if last_day <= calc:
            # Mês completo
            rate = _get_monthly_ipca(year, month)
            if rate is None:
                # Sem dado: usa projeção
                rate = get_ipca_projection(month_str) or 0.0
            factor *= (1 + rate / 100)
        else:
            # Mês parcial (mês corrente)
            elapsed_du = _business_days_elapsed(year, month, calc)
            rate = get_ipca_projection(month_str)
            if rate is None:
                rate = _get_last_known_ipca() or 0.0
            factor *= (1 + rate / 100) ** (elapsed_du / total_du)

        cursor = cursor + relativedelta(months=1)

    return vne * factor


def _get_monthly_ipca(year: int, month: int) -> float | None:
    """Busca IPCA publicado para o mês (qualquer dia do mês no DB)."""
    month_prefix = f"{year}-{month:02d}"
    with get_conn() as conn:
        row = conn.execute("""
            SELECT rate_pct FROM ipca_monthly
            WHERE date LIKE ?
            ORDER BY date DESC LIMIT 1
        """, (month_prefix + "%",)).fetchone()
    return float(row["rate_pct"]) if row else None


def _get_last_known_ipca() -> float | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT rate_pct FROM ipca_monthly ORDER BY date DESC LIMIT 1"
        ).fetchone()
    return float(row["rate_pct"]) if row else None


def calc_vna_cdi(vne: float, base_date: str, calc_date: str, pct_cdi: float = 100.0) -> float:
    """
    Calcula VNA de um papel CDI.
    Usa histórico CDI do BACEN (série 12).
    pct_cdi: % do CDI (ex: 100 = 100% CDI, 95.5 = 95,5% CDI)
    """
    from .sync_bacen import get_cdi_accumulated
    factor = get_cdi_accumulated(base_date, calc_date)
    # Aplica o % do CDI: (CDI_factor - 1) × pct/100 + 1
    # Convenção: (1 + cdi_diário)^n onde cdi_diário = selic × pct/100
    # Simplificação: elevamos o fator inteiro ao pct/100
    adjusted_factor = factor ** (pct_cdi / 100)
    return vne * adjusted_factor
