"""
Baixa dados do BACEN (SGS):
- CDI diário (série 12 = SELIC Over, equivalente ao CDI para precificação)
- IPCA mensal (série 433)
- Projeção ANBIMA do IPCA
"""
import requests
from datetime import date as dt_date, datetime
from .db import get_conn


BACEN_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series}/dados"
ANBIMA_IPCA_URL = "https://www.anbima.com.br/pt_br/informar/projecao-de-inflacao.htm"


def _get_bacen(series: int, start: str | None = None, end: str | None = None) -> list[dict]:
    """Retorna lista de {data, valor} do SGS BACEN."""
    params = {"formato": "json"}
    if start:
        params["dataInicial"] = start
    if end:
        params["dataFinal"] = end

    r = requests.get(
        BACEN_URL.format(series=series),
        params=params,
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def sync_cdi(start: str = "01/01/2000"):
    """
    Sincroniza CDI diário do BACEN.
    Série 12 = Taxa SELIC Over (% ao ano base 252).
    start: DD/MM/YYYY
    """
    print("Baixando CDI do BACEN...")
    data = _get_bacen(12, start=start)
    rows = []
    for item in data:
        d = datetime.strptime(item["data"], "%d/%m/%Y").date().isoformat()
        rows.append((d, float(item["valor"].replace(",", "."))))

    with get_conn() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO cdi_daily (date, rate_annual) VALUES (?,?)",
            rows,
        )
    print(f"CDI: {len(rows)} registros salvos")
    return len(rows)


def sync_ipca(start: str = "01/01/2000"):
    """
    Sincroniza IPCA mensal do BACEN.
    Série 433 = IPCA % ao mês.
    """
    print("Baixando IPCA do BACEN...")
    data = _get_bacen(433, start=start)
    rows = []
    for item in data:
        d = datetime.strptime(item["data"], "%d/%m/%Y").date().isoformat()
        rows.append((d, float(item["valor"].replace(",", "."))))

    with get_conn() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO ipca_monthly (date, rate_pct) VALUES (?,?)",
            rows,
        )
    print(f"IPCA: {len(rows)} registros salvos")
    return len(rows)


def sync_anbima_ipca_projection():
    """
    Baixa a projeção de IPCA da ANBIMA.
    A ANBIMA publica uma tabela de projeções mensais de IPCA.
    Fonte: API pública da ANBIMA.
    """
    print("Baixando projeção IPCA ANBIMA...")
    try:
        url = "https://api.anbima.com.br/v1/indices/ipca/projecao"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            items = r.json()
            ref = dt_date.today().isoformat()
            rows = []
            for item in items:
                month = item.get("mesAno") or item.get("month") or ""
                rate = item.get("taxa") or item.get("rate") or 0
                rows.append((ref, month, float(rate)))

            with get_conn() as conn:
                conn.executemany(
                    "INSERT OR REPLACE INTO ipca_projections (ref_date, month, rate_pct) VALUES (?,?,?)",
                    rows,
                )
            print(f"ANBIMA IPCA: {len(rows)} projeções salvas")
            return len(rows)
    except Exception as e:
        print(f"ANBIMA IPCA não disponível via API ({e}), usando extrapolação CDI.")

    _extrapolate_ipca_projection()
    return 0


def _extrapolate_ipca_projection():
    """
    Fallback: usa a última taxa do IPCA disponível como projeção dos próximos 24 meses.
    """
    with get_conn() as conn:
        row = conn.execute(
            "SELECT date, rate_pct FROM ipca_monthly ORDER BY date DESC LIMIT 1"
        ).fetchone()

    if not row:
        return

    ref = dt_date.today().isoformat()
    last_rate = row["rate_pct"]
    last_date = datetime.fromisoformat(row["date"])

    from dateutil.relativedelta import relativedelta
    rows = []
    for i in range(1, 25):
        m = (last_date + relativedelta(months=i)).strftime("%Y-%m")
        rows.append((ref, m, last_rate))

    with get_conn() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO ipca_projections (ref_date, month, rate_pct, source) VALUES (?,?,?,'extrapolado')",
            rows,
        )
    print(f"IPCA extrapolado: {len(rows)} meses à taxa de {last_rate:.4f}%")


def get_last_cdi_rate() -> float | None:
    """
    Retorna a última taxa CDI anualizada (% ao ano, base 252).
    A série 12 do BACEN retorna % ao dia; convertemos aqui.
    """
    with get_conn() as conn:
        row = conn.execute(
            "SELECT rate_annual FROM cdi_daily ORDER BY date DESC LIMIT 1"
        ).fetchone()
    if not row:
        return None
    daily_pct = float(row["rate_annual"])
    return ((1 + daily_pct / 100) ** 252 - 1) * 100


def get_cdi_accumulated(start_date: str, end_date: str) -> float:
    """
    Calcula o fator CDI acumulado entre duas datas.
    A série 12 do BACEN retorna taxa % ao dia (ex: 0.0534 = 0,0534% a.d.).
    Fator = Π (1 + rate_daily_pct/100) para cada dia útil no intervalo.
    Retorna o fator (ex: 1.0543 para 5.43% de acumulação).
    """
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT date, rate_annual FROM cdi_daily
            WHERE date > ? AND date <= ?
            ORDER BY date
        """, (start_date, end_date)).fetchall()

    factor = 1.0
    for row in rows:
        factor *= (1 + float(row["rate_annual"]) / 100)
    return factor


if __name__ == "__main__":
    sync_cdi()
    sync_ipca()
    sync_anbima_ipca_projection()
