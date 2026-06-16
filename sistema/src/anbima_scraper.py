"""
Scraper do ANBIMA Data (https://data.anbima.com.br/) para enriquecimento de dados.

Extrai informações que as APIs de cálculo não fornecem:
  - Características do ativo (emissor, data emissão, vencimento, garantias)
  - Cronograma de amortização detalhado
  - Datas de pagamento de juros (cupons)
  - Indexador e spread contratual
  - Rating e setor

Exemplo: https://data.anbima.com.br/debentures/AAJR11/caracteristicas

Estratégia: usa requests + BeautifulSoup (se disponível) ou regex como fallback.
Prioriza chamadas leves para não sobrecarregar o servidor.
"""
import re
import json
import time
from datetime import date as dt_date, datetime
from typing import Optional
import requests

ANBIMA_BASE = "https://data.anbima.com.br"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

_last_call = 0.0
MIN_INTERVAL = 1.0  # respeitar o servidor


def _rate_limit():
    global _last_call
    elapsed = time.time() - _last_call
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    _last_call = time.time()


# ═══════════════════════════════════════════════════════════════
# Características do ativo
# ═══════════════════════════════════════════════════════════════

def get_caracteristicas(ticker: str) -> dict:
    """
    Extrai características de uma debênture do ANBIMA Data.

    Args:
        ticker: código do ativo (ex: AAJR11)

    Returns:
        dict com: emissor, data_emissao, data_vencimento, indexador,
                  spread, garantia, setor, rating, situacao, ...
    """
    url = f"{ANBIMA_BASE}/debentures/{ticker.upper()}/caracteristicas"
    _rate_limit()

    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 404:
            return {"_error": "não_encontrado", "ticker": ticker}
        r.raise_for_status()
    except Exception as e:
        return {"_error": str(e), "ticker": ticker}

    html = r.text
    data: dict = {"ticker": ticker, "_fonte": "ANBIMA_Data", "_url": url}

    # Tenta extrair dados estruturados (JSON-LD, scripts)
    script_match = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
    for s in script_match:
        try:
            ld = json.loads(s)
            if isinstance(ld, dict):
                data.update(_flatten_jsonld(ld))
        except Exception:
            pass

    # Extração por regex dos campos principais
    patterns = {
        "emissor": r'Emissor[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
        "data_emissao": r'Data\s+de\s+Emissão[:\s]*</[^>]+>\s*<[^>]+>(\d{2}/\d{2}/\d{4})',
        "data_vencimento": r'Data\s+de\s+Vencimento[:\s]*</[^>]+>\s*<[^>]+>(\d{2}/\d{2}/\d{4})',
        "indexador": r'Indexador[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
        "spread": r'Spread[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
        "garantia": r'Garantia[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
        "setor": r'Setor[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
    }

    for key, pat in patterns.items():
        m = re.search(pat, html, re.IGNORECASE | re.DOTALL)
        if m:
            val = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            if val:
                data[key] = val

    # Buscar rating (se disponível)
    rating_m = re.findall(
        r'(AAA|AA\+|AA|AA-|A\+|A|A-|BBB\+|BBB|BBB-|BB\+|BB|BB-|B\+|B|B-)',
        html, re.IGNORECASE
    )
    if rating_m:
        data["rating"] = max(set(rating_m), key=rating_m.count)

    # Buscar situação
    sit_m = re.search(
        r'(ATIVO|RESGATADA|CANCELADA|VENCIDA|INADIMPLENTE)',
        html, re.IGNORECASE
    )
    if sit_m:
        data["situacao"] = sit_m.group(1).upper()

    # Extrair tabelas de fluxos se existirem
    data.update(_extract_amort_table(html))

    return data


def _flatten_jsonld(ld: dict) -> dict:
    """Converte JSON-LD para dict plano."""
    result = {}
    name_map = {
        "name": "nome",
        "description": "descricao",
        "issuer": "emissor",
        "tickerSymbol": "ticker",
    }
    for k, v in ld.items():
        key = name_map.get(k, k)
        if isinstance(v, str):
            result[key] = v
    return result


def _extract_amort_table(html: str) -> dict:
    """Tenta extrair tabela de amortização do HTML."""
    result: dict = {}

    # Procura linhas de tabela com datas e percentuais
    # Padrão comum: <td>data</td><td>percentual%</td>
    rows = re.findall(
        r'<tr[^>]*>\s*<td[^>]*>(\d{2}/\d{2}/\d{4})</td>\s*<td[^>]*>([\d.,]+)\s*%?</td>',
        html, re.DOTALL
    )
    if rows:
        amort = []
        for date_str, pct_str in rows:
            try:
                d = datetime.strptime(date_str, "%d/%m/%Y").date().isoformat()
                p = float(pct_str.replace(",", "."))
                amort.append({"date": d, "pct": p / 100.0})
            except Exception:
                pass
        if amort:
            result["amort_schedule"] = amort

    return result


# ═══════════════════════════════════════════════════════════════
# Listagem de debêntures
# ═══════════════════════════════════════════════════════════════

def list_debentures(pagina: int = 1, limit: int = 100) -> list[dict]:
    """
    Lista debêntures disponíveis no ANBIMA Data (paginado).

    Args:
        pagina: número da página (1-based)
        limit: registros por página

    Returns:
        lista de dicts com ticker e dados básicos
    """
    url = f"{ANBIMA_BASE}/debentures"
    _rate_limit()

    try:
        r = requests.get(url, headers=HEADERS, params={"page": pagina, "limit": limit}, timeout=30)
        r.raise_for_status()
    except Exception as e:
        return [{"_error": str(e)}]

    html = r.text

    # Tenta encontrar dados estruturados
    tickers = re.findall(r'href="/debentures/([A-Z0-9]{4,12})/', html)
    # Remove duplicatas mantendo ordem
    seen = set()
    unique = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return [{"ticker": t, "_fonte": "ANBIMA_Data_lista"} for t in unique]


# ═══════════════════════════════════════════════════════════════
# Enriquecimento de ticker (combina fontes)
# ═══════════════════════════════════════════════════════════════

def enriquecer_ticker(ticker: str) -> dict:
    """
    Busca dados complementares de um ticker em todas as fontes disponíveis.

    Args:
        ticker: código do ativo

    Returns:
        dict com dados mesclados de todas as fontes
    """
    data = {"ticker": ticker}

    # ANBIMA Data
    try:
        anbima_data = get_caracteristicas(ticker)
        if "_error" not in anbima_data:
            data["anbima"] = anbima_data
            # Propaga campos relevantes
            for k in ["emissor", "data_emissao", "data_vencimento",
                       "indexador", "spread", "garantia", "setor",
                       "rating", "situacao", "amort_schedule"]:
                if k in anbima_data:
                    data[k] = anbima_data[k]
    except Exception:
        pass

    return data
