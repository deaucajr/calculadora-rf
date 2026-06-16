"""
Cálculo local de DI Futuro (DI1F*).
Não depende de API externa — usa contagem de dias úteis e feriados ANBIMA.

Fórmulas:
  PU = 100000 / (1 + taxa/100)^(du/252)
  Taxa = ((100000 / PU)^(252/du) - 1) × 100
  Duration = du / 252

O vencimento é sempre o PRIMEIRO DIA ÚTIL do mês/ano do contrato.
"""
from datetime import date as dt_date, datetime, timedelta
from typing import Optional

# Mapeamento da letra do mês (4º caractere do ticker DI1)
MES_MAP = {
    "F": 1, "G": 2, "H": 3, "J": 4,
    "K": 5, "M": 6, "N": 7, "Q": 8,
    "U": 9, "V": 10, "X": 11, "Z": 12,
}


def _easter(y: int) -> dt_date:
    """Algoritmo de Gauss para Páscoa."""
    a = y % 19; b = y // 100; c = y % 100
    d = b // 4; e = b % 4; f = (b + 8) // 25
    g = (b - f + 1) // 3; h = (19 * a + b - d - g + 15) % 30
    i = c // 4; k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return dt_date(y, month, day)


def _feriados_ano(y: int) -> set[dt_date]:
    """Retorna set de feriados nacionais para um ano."""
    pascoa = _easter(y)
    fer = {
        dt_date(y, 1, 1),           # Confraternização Universal
        pascoa - timedelta(days=48), # Carnaval (segunda)
        pascoa - timedelta(days=47), # Carnaval (terça)
        pascoa - timedelta(days=2),  # Sexta-feira Santa
        dt_date(y, 4, 21),          # Tiradentes
        dt_date(y, 5, 1),           # Dia do Trabalho
        pascoa + timedelta(days=60), # Corpus Christi
        dt_date(y, 9, 7),           # Independência
        dt_date(y, 10, 12),         # Nossa Senhora Aparecida
        dt_date(y, 11, 2),          # Finados
        dt_date(y, 11, 15),         # Proclamação da República
        dt_date(y, 12, 25),         # Natal
    }
    if y >= 2024:
        fer.add(dt_date(y, 11, 20))  # Consciência Negra
    return fer


def _feriados_range(ano_ini: int, ano_fim: int) -> set[dt_date]:
    fer = set()
    for y in range(ano_ini, ano_fim + 1):
        fer |= _feriados_ano(y)
    return fer


# Cache global de feriados
_FERIADOS = _feriados_range(2000, 2070)


def _is_business_day(d: dt_date) -> bool:
    return d.weekday() < 5 and d not in _FERIADOS


def _first_business_day(year: int, month: int) -> dt_date:
    """Primeiro dia útil do mês."""
    d = dt_date(year, month, 1)
    while not _is_business_day(d):
        d += timedelta(days=1)
    return d


def _parse_di_ticker(ticker: str) -> tuple[int, int]:
    """
    Extrai (mês, ano) do ticker DI1.
    Ex: DI1F25 → mês=1 (Jan), ano=2025
        DI1Z30 → mês=12 (Dez), ano=2030
    """
    t = ticker.upper().replace(" ", "")
    if len(t) < 5:
        raise ValueError(f"Ticker DI inválido: {ticker}. Use formato DI1F25.")
    mes_char = t[3]
    ano_str = t[4:6]
    if mes_char not in MES_MAP:
        raise ValueError(f"Mês '{mes_char}' inválido no ticker {ticker}. Use F-Z.")
    mes = MES_MAP[mes_char]
    ano = 2000 + int(ano_str)
    return mes, ano


def _count_business_days(start: dt_date, end: dt_date) -> int:
    """Conta dias úteis entre start (exclusive) e end (inclusive)."""
    count = 0
    d = start + timedelta(days=1)
    while d <= end:
        if _is_business_day(d):
            count += 1
        d += timedelta(days=1)
    return max(1, count)


def calc_di_futuro(ticker: str, date_str: str, *,
                   rate: float | None = None,
                   pu: float | None = None) -> dict:
    """
    Calcula PU ou Taxa de um DI Futuro.

    Args:
        ticker: ex: DI1F25, DI1Z30
        date_str: data base YYYY-MM-DD
        rate: taxa % a.a. (para calcular PU)
        pu: preço unitário (para calcular taxa)

    Returns:
        dict com: PU, yield, duration, du, vencimento, source
    """
    mes, ano = _parse_di_ticker(ticker)
    vencimento = _first_business_day(ano, mes)
    base_date = datetime.fromisoformat(date_str).date()

    if base_date >= vencimento:
        raise ValueError(f"Data base ({date_str}) >= vencimento ({vencimento.isoformat()})")

    du = _count_business_days(base_date, vencimento)
    t = du / 252.0

    if rate is not None:
        # Calcular PU a partir da taxa
        computed_pu = 100000.0 / ((1.0 + rate / 100.0) ** t)
        return {
            "ticker": ticker,
            "date": date_str,
            "vencimento": vencimento.isoformat(),
            "du": du,
            "yield": rate,
            "PU": round(computed_pu, 6),
            "duration": round(t, 6),
            "vna": None,
            "source": "DI_Local",
            "n_flows": 1,
        }

    elif pu is not None:
        # Calcular taxa a partir do PU
        computed_yield = ((100000.0 / pu) ** (1.0 / t) - 1.0) * 100.0
        return {
            "ticker": ticker,
            "date": date_str,
            "vencimento": vencimento.isoformat(),
            "du": du,
            "yield": round(computed_yield, 6),
            "PU": pu,
            "duration": round(t, 6),
            "vna": None,
            "source": "DI_Local",
            "n_flows": 1,
        }

    else:
        raise ValueError("Informe rate ou pu para calcular DI Futuro.")


# ═══════════════════════════════════════════════════════════════
# Lista de todos os DI Futuros disponíveis
# ═══════════════════════════════════════════════════════════════

def list_di_tickers() -> list[str]:
    """Retorna todos os tickers de DI Futuro com vencimento futuro."""
    today = dt_date.today()
    tickers = []
    for ano in range(today.year, today.year + 12):
        for mes_char, mes_num in MES_MAP.items():
            try:
                venc = _first_business_day(ano, mes_num)
                if venc > today:
                    tickers.append(f"DI1{mes_char}{str(ano)[2:]}")
            except Exception:
                pass
    return sorted(tickers)

ALL_DI_TICKERS = list_di_tickers()
