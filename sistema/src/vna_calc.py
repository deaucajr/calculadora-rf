"""
Calculo PROPRIO de VNA (Valor Nominal Atualizado) desde a data de emissao.

Nao depende de API externa para VNA — usa:
  - IPCA mensal publicado (BACEN serie 433) para meses passados
  - Projecao ANBIMA Focus para meses futuros
  - CDI diario (BACEN serie 12) para CDI+
  - Cronograma de amortizacao proprio

FORMULAS:
  IPCA:   VNA(d) = VNE * IPCA_index(emissao, d) * (1 - amort_acumulada(d))
  CDI+:   VNA(d) = VNE * CDI_factor(emissao, d)
  %CDI:   VNA(d) = VNE * CDI_factor(emissao, d) ^ (pct_cdi/100)
  PRE:    VNA(d) = VNE  (constante)

PRECISAO ALVO: erro < 0,00001 vs FI Analytics (5a-6a casa decimal)
"""
from datetime import date as dt_date, datetime
from dateutil.relativedelta import relativedelta
from .db import get_conn


# ─── IPCA Index ───────────────────────────────────────────────

def get_ipca_index(start: str, end: str) -> float:
    """
    Fator acumulado IPCA entre duas datas (pro-rata ANBIMA).

    Meses completos: IPCA publicado (BACEN 433).
    Mes parcial (corrente): projecao ANBIMA, pro-rata por dias uteis/21.

    Ex: IPCA_index('2024-05-15', '2026-06-15') = 1.1108 (11.08%)
    """
    d0 = datetime.fromisoformat(start).date()
    d1 = datetime.fromisoformat(end).date()

    if d1 <= d0:
        return 1.0

    factor = 1.0
    cursor = dt_date(d0.year, d0.month, 1)

    while cursor <= d1:
        y, m = cursor.year, cursor.month
        month_str = cursor.strftime("%Y-%m")
        last_day = (cursor + relativedelta(months=1)) - relativedelta(days=1)

        if last_day < d0:
            cursor += relativedelta(months=1)
            continue

        total_du = 21  # convencao ANBIMA

        if last_day <= d1:
            # Mes completo: IPCA publicado
            rate = _get_monthly_ipca(y, m)
            if rate is None:
                rate = _get_ipca_projection(month_str) or 0.0
            factor *= (1.0 + rate / 100.0)
        else:
            # Mes parcial: projecao pro-rata
            elapsed = max(1, int((d1 - dt_date(y, m, 1)).days * 252.0 / 365.0))
            rate = _get_ipca_projection(month_str)
            if rate is None:
                rate = _get_last_ipca() or 0.0
            factor *= (1.0 + rate / 100.0) ** (elapsed / total_du)

        cursor += relativedelta(months=1)

    return factor


def _get_monthly_ipca(y: int, m: int) -> float | None:
    prefix = f"{y}-{m:02d}"
    with get_conn() as conn:
        row = conn.execute(
            "SELECT rate_pct FROM ipca_monthly WHERE date LIKE ? ORDER BY date DESC LIMIT 1",
            (prefix + "%",)
        ).fetchone()
    return float(row["rate_pct"]) if row else None


def _get_ipca_projection(month: str) -> float | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT rate_pct FROM ipca_projections WHERE month=? ORDER BY ref_date DESC LIMIT 1",
            (month,)
        ).fetchone()
    return float(row["rate_pct"]) if row else None


def _get_last_ipca() -> float | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT rate_pct FROM ipca_monthly ORDER BY date DESC LIMIT 1"
        ).fetchone()
    return float(row["rate_pct"]) if row else None


# ─── CDI Accumulated ──────────────────────────────────────────

def get_cdi_factor(start: str, end: str) -> float:
    """
    Fator acumulado CDI entre duas datas (BACEN serie 12).

    Retorna: Π (1 + CDI_diario/100) para cada dia no intervalo.
    Ex: CDI_factor('2024-01-01', '2026-06-15') ≈ 1.30 (30%)
    """
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT date, rate_annual FROM cdi_daily
            WHERE date > ? AND date <= ?
            ORDER BY date
        """, (start, end)).fetchall()

    factor = 1.0
    for r in rows:
        factor *= (1.0 + float(r["rate_annual"]) / 100.0)
    return factor


# ─── VNA por indexador ────────────────────────────────────────

def calc_vna_ipca(vne: float, emission_date: str, calc_date: str,
                  amort_schedule: list[dict] | None = None) -> dict:
    """
    VNA para IPCA desde a emissao.
    amort_schedule: [{'date': 'YYYY-MM-DD', 'pct': 0.05}, ...]  # % do VNE amortizado
    """
    d_emi = emission_date[:10]
    d_calc = calc_date[:10]

    ipca_factor = get_ipca_index(d_emi, d_calc)

    # Amortizacao acumulada
    cumul_amort = 0.0
    if amort_schedule:
        cumul_amort = sum(
            float(a["pct"]) for a in amort_schedule
            if a["date"][:10] <= d_calc
        )
        # Converter de % do VNE para fracao
        if cumul_amort > 1.0:
            cumul_amort /= 100.0

    amort_factor = 1.0 - cumul_amort
    vna = vne * ipca_factor * amort_factor

    return {
        "vna": round(vna, 8),
        "ipca_factor": round(ipca_factor, 10),
        "amort_factor": round(amort_factor, 10),
        "cumul_amort_pct": round(cumul_amort * 100, 4),
        "indexador": "IPCA",
    }


def calc_vna_cdi(vne: float, emission_date: str, calc_date: str,
                 pct_cdi: float = 100.0) -> dict:
    """
    VNA para CDI+/%CDI desde a emissao.
    pct_cdi: 100 = CDI+, <100 ou >100 = %CDI
    """
    d_emi = emission_date[:10]
    d_calc = calc_date[:10]

    cdi_factor = get_cdi_factor(d_emi, d_calc)

    if abs(pct_cdi - 100.0) < 0.001:
        # CDI+ puro (spread tratado separadamente no desconto)
        adjusted = cdi_factor
        vna = vne * adjusted
    else:
        # %CDI: fator ^ (pct/100)
        adjusted = cdi_factor ** (pct_cdi / 100.0)
        vna = vne * adjusted

    return {
        "vna": round(vna, 8),
        "cdi_factor": round(cdi_factor, 10),
        "adjusted_factor": round(adjusted, 10) if 'adjusted' in dir() else round(cdi_factor, 10),
        "pct_cdi": pct_cdi,
        "indexador": "%CDI" if abs(pct_cdi - 100.0) > 0.001 else "CDI+",
    }


def calc_vna_pre(vne: float, emission_date: str = "", calc_date: str = "") -> dict:
    """VNA para PRE: constante = VNE."""
    return {
        "vna": vne,
        "indexador": "PRE",
    }


# ─── Funcao universal ─────────────────────────────────────────

def calcular_vna(ticker_info: dict, calc_date: str) -> dict:
    """
    Calcula VNA para qualquer ticker.

    ticker_info:
      - vne: float
      - indexador: 'IPCA' | 'CDI+' | '%CDI' | 'PRE'
      - inicio_rentabilidade: str (YYYY-MM-DD)
      - amort_schedule: list[dict] opcional
      - pct_cdi: float opcional

    Retorna dict com: vna, factor, indexador
    """
    idx = (ticker_info.get("indexador") or "").upper().strip()
    vne = float(ticker_info.get("vne") or 1000.0)
    inicio = ticker_info.get("inicio_rentabilidade") or ""

    if not inicio:
        # Fallback: data de emissao ou hoje
        inicio = ticker_info.get("data_emissao") or calc_date

    if "IPCA" in idx:
        return calc_vna_ipca(vne, inicio, calc_date, ticker_info.get("amort_schedule"))
    elif "CDI" in idx or "%CDI" in idx:
        pct = float(ticker_info.get("pct_cdi") or 100.0)
        if "%CDI" in idx and pct == 100.0:
            pct = float(ticker_info.get("taxa_ref") or 98.0)
        return calc_vna_cdi(vne, inicio, calc_date, pct)
    else:
        return calc_vna_pre(vne, inicio, calc_date)
