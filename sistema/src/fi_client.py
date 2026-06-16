"""
Cliente da API FI Analytics — fonte primária de precificação e fluxos de caixa.

Endpoints:
  - Corporate: /deb/debenturecalculator, /cr/cricracalculator
  - Government: /gov/govbondcalculator (2 passos: ISIN → cálculo)
  - BondBuilder: /bb/bondbuildercalculator (fallback com user bonds)
  - User Bonds: /bb/bondbuildercalculator/getuserbonds

Retorna dados completos incluindo:
  - Fluxos de caixa (com % Tai por evento)
  - Juros incorporados (accrued interest) — diferencial vs. B3
  - m2m, m2mRate, maculayDuration
  - taxedM2MRate (gross-up)
  - diEquivalentAdditiveRate, diEquivalentMultiplicativeRate
"""
import requests
import time
from datetime import date as dt_date, datetime
from typing import Optional
from .config import get_required

FI_BASE = "https://endpoint.fi-analytics.com.br"
HEADERS_TEMPLATE = {
    "Content-Type": "application/json; charset=utf-8",
}
_last_call = 0.0
MIN_INTERVAL = 0.3  # segundos entre chamadas


def _rate_limit():
    global _last_call
    elapsed = time.time() - _last_call
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    _last_call = time.time()


def _headers() -> dict:
    h = dict(HEADERS_TEMPLATE)
    h["x-api-key"] = get_required("FI_API_KEY")
    return h


# ═══════════════════════════════════════════════════════════════
# Títulos Corporativos (Debêntures, CRIs, CRAs)
# ═══════════════════════════════════════════════════════════════

def calc_corporate(ticker: str, date_str: str, *,
                   rate: float | None = None,
                   pu: float | None = None,
                   quantity: int = 1,
                   use_intraday: bool = False) -> dict:
    """
    Calcula PU (dada taxa) ou Taxa (dado PU) para um título corporativo.

    Args:
        ticker: código do ativo (ex: VALE33, EGIEA6)
        date_str: data base YYYY-MM-DD
        rate: taxa yield % a.a. (para calcular PU)
        pu: preço unitário (para calcular taxa)
        quantity: quantidade (default=1)
        use_intraday: usar curva intraday (default=False)

    Returns:
        dict com: referenceDate, m2m, m2mRate, maculayDuration,
                  taxedM2MRate (gross-up), diEquivalentAdditiveRate,
                  diEquivalentMultiplicativeRate, cashFlowList, ...
    """
    _rate_limit()

    payload: dict = {
        "ticker": ticker.upper(),
        "date": date_str,
        "quantity": quantity,
        "useIntradayCurve": use_intraday,
    }
    if rate is not None:
        payload["rate"] = rate
    elif pu is not None:
        payload["pu"] = pu

    # Tenta debentures primeiro, depois CRI/CRA
    for segment in ["deb", "cr"]:
        url = f"{FI_BASE}/{segment}/{segment}enturecalculator" if segment == "deb" else f"{FI_BASE}/cr/cricracalculator"
        try:
            r = requests.post(url, json=payload, headers=_headers(), timeout=60)
            if r.status_code == 200:
                data = r.json()
                if data and not data.get("error"):
                    data["_source"] = "FI_Analytics"
                    data["_endpoint"] = segment
                    return data
        except Exception:
            continue

    raise RuntimeError(f"FI Analytics: não foi possível calcular {ticker} (tentou deb e cr)")


def calc_pu_fi(ticker: str, rate: float, date_str: str | None = None) -> dict:
    """Calcula PU via FI Analytics dada uma taxa."""
    if date_str is None:
        date_str = dt_date.today().isoformat()
    return calc_corporate(ticker, date_str, rate=rate)


def calc_yield_fi(ticker: str, pu: float, date_str: str | None = None) -> dict:
    """Calcula Yield via FI Analytics dado um PU."""
    if date_str is None:
        date_str = dt_date.today().isoformat()
    return calc_corporate(ticker, date_str, pu=pu)


# ═══════════════════════════════════════════════════════════════
# Títulos Públicos (NTN-B, NTN-F, LFT, LTN)
# ═══════════════════════════════════════════════════════════════

# Mapeamento de vencimentos NTN-B
NTNB_MAP = {
    "B24": ("15/08/2024", "76019920240815"),
    "B26": ("15/08/2026", "76019920260815"),
    "B27": ("15/05/2027", "76019920270515"),
    "B28": ("15/08/2028", "76019920280815"),
    "B29": ("15/05/2029", "76019920290515"),
    "B30": ("15/08/2030", "76019920300815"),
    "B31": ("15/05/2031", "76019920310515"),
    "B32": ("15/08/2032", "76019920320815"),
    "B33": ("15/05/2033", "76019920330515"),
    "B35": ("15/05/2035", "76019920350515"),
    "B37": ("15/05/2037", "76019920370515"),
    "B40": ("15/08/2040", "76019920400815"),
    "B45": ("15/05/2045", "76019920450515"),
    "B50": ("15/08/2050", "76019920500815"),
    "B55": ("15/05/2055", "76019920550515"),
    "B60": ("15/08/2060", "76019920600815"),
}

NTNF_MAP = {
    "F25": ("01/01/2025", "95019920250101"),
    "F27": ("01/01/2027", "95019920270101"),
    "F29": ("01/01/2029", "95019920290101"),
    "F31": ("01/01/2031", "95019920310101"),
    "F33": ("01/01/2033", "95019920330101"),
}


def _parse_ntnb_ticker(ticker: str) -> tuple[str, str]:
    """
    Converte ticker amigável → (maturity_date, isin/cetip).
    Ex: "NTN-B 30" → ("15/08/2030", "76019920300815")
        "NTNB30"   → ("15/08/2030", "76019920300815")
    """
    t = ticker.upper().replace("-", "").replace(" ", "").replace("_", "")
    if t.startswith("NTNB"):
        code = "B" + t[4:]
    elif t.startswith("NTNF"):
        code = "F" + t[4:]
    else:
        code = t

    if code in NTNB_MAP:
        return NTNB_MAP[code]
    if code in NTNF_MAP:
        return NTNF_MAP[code]

    raise ValueError(f"Vencimento '{ticker}' não mapeado. Use ex: NTN-B 30, NTNB30, NTN-F 31.")


def _get_gov_isin(instrument_type: str, maturity_date: str) -> str:
    """Etapa 1: obter ISIN do título público."""
    url = f"{FI_BASE}/financialutil/gov/getgovbondisin"
    payload = {"instrument_type": instrument_type, "maturity_date": maturity_date}
    _rate_limit()
    r = requests.post(url, json=payload, headers=_headers(), timeout=30)
    r.raise_for_status()
    data = r.json()
    isin = data.get("isin")
    if not isin:
        raise RuntimeError(f"ISIN não encontrado para {instrument_type} {maturity_date}: {data}")
    return isin


def calc_gov_bond(ticker: str, date_str: str, *,
                  rate: float | None = None,
                  pu: float | None = None) -> dict:
    """
    Calcula PU/Taxa para título público via FI Analytics.

    Args:
        ticker: "NTN-B 30", "NTNB30", "NTN-F 31", etc.
        date_str: data base YYYY-MM-DD
        rate: taxa yield % a.a. (para calcular PU)
        pu: preço unitário (para calcular taxa)

    Returns:
        dict com: m2m, m2mRate, maculayDuration, taxedM2MRate, cashFlowList, ...
    """
    maturity_date, cetip = _parse_ntnb_ticker(ticker)

    # Determina o tipo
    t = ticker.upper().replace("-", "").replace(" ", "")
    if t.startswith("NTNB"):
        instrument_type = "NTN-B"
    elif t.startswith("NTNF"):
        instrument_type = "NTN-F"
    else:
        instrument_type = "NTN-B"  # default

    # Etapa 1: obter ISIN
    isin = _get_gov_isin(instrument_type, maturity_date)

    # Etapa 2: calcular
    url = f"{FI_BASE}/gov/govbondcalculator"
    payload: dict = {"isin": isin, "date": date_str}
    if rate is not None:
        payload["rate"] = rate
    elif pu is not None:
        payload["pu"] = pu

    _rate_limit()
    r = requests.post(url, json=payload, headers=_headers(), timeout=60)
    r.raise_for_status()
    data = r.json()
    data["_source"] = "FI_Analytics_Gov"
    data["_cetip"] = cetip
    return data


# ═══════════════════════════════════════════════════════════════
# BondBuilder (Fallback / Listagem de Bonds do Usuário)
# ═══════════════════════════════════════════════════════════════

def get_user_bonds() -> list[dict]:
    """
    Retorna a lista completa de bonds do usuário no FI Analytics.
    Cada item contém: _id (doc_id), bond_name (ticker), e metadados.
    """
    url = f"{FI_BASE}/bb/bondbuildercalculator/getuserbonds"
    email = get_required("FI_USER_EMAIL")
    payload = {"user_email": email, "get_company_bonds": "1"}
    _rate_limit()
    r = requests.post(url, json=payload, headers=_headers(), timeout=60)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"FI getuserbonds erro: {data}")
    return data if isinstance(data, list) else []


def calc_bondbuilder(doc_id: str, date_str: str, *,
                     rate: float | None = None,
                     pu: float | None = None) -> dict:
    """
    Calcula via BondBuilder (fallback quando o ticker não está nos endpoints corporativos).
    """
    url = f"{FI_BASE}/bb/bondbuildercalculator"
    payload: dict = {"doc_id": doc_id, "date": date_str}
    if rate is not None:
        payload["rate"] = rate
    elif pu is not None:
        payload["pu"] = pu
    _rate_limit()
    r = requests.post(url, json=payload, headers=_headers(), timeout=60)
    r.raise_for_status()
    data = r.json()
    data["_source"] = "FI_BondBuilder"
    return data


# ═══════════════════════════════════════════════════════════════
# Função Universal: detecta tipo e calcula
# ═══════════════════════════════════════════════════════════════

def calc_universal(ticker: str, date_str: str, *,
                   rate: float | None = None,
                   pu: float | None = None) -> dict:
    """
    Calcula PU ou Yield para QUALQUER ativo, detectando automaticamente o tipo:
      - NTN-B / NTN-F → gov bond
      - DI1F* → cálculo local (DI Futuro)
      - Demais → corporate (deb → cr)

    Args:
        ticker: código do ativo
        date_str: data base YYYY-MM-DD
        rate: taxa yield % a.a. (para calcular PU)
        pu: preço unitário (para calcular taxa)

    Returns:
        dict padronizado com: PU (ou m2m), yield (ou m2mRate), duration,
        vna, source, cash_flows, ...
    """
    t_upper = ticker.upper().replace(" ", "")

    # DI Futuro → cálculo local (não tem API)
    if t_upper.startswith("DI1"):
        from .di_futuro import calc_di_futuro
        return calc_di_futuro(ticker, date_str, rate=rate, pu=pu)

    # Títulos públicos
    if t_upper.startswith("NTNB") or t_upper.startswith("NTN-B"):
        return calc_gov_bond(ticker, date_str, rate=rate, pu=pu)
    if t_upper.startswith("NTNF") or t_upper.startswith("NTN-F"):
        return calc_gov_bond(ticker, date_str, rate=rate, pu=pu)

    # Corporativos
    try:
        return calc_corporate(ticker, date_str, rate=rate, pu=pu)
    except Exception:
        pass

    # Fallback: BondBuilder
    bonds = get_user_bonds()
    doc_id = None
    for b in bonds:
        if b.get("bond_name", "").upper() == t_upper:
            doc_id = b.get("_id")
            break
    if doc_id:
        return calc_bondbuilder(doc_id, date_str, rate=rate, pu=pu)

    raise RuntimeError(f"Não foi possível calcular '{ticker}': não encontrado em nenhuma fonte.")
