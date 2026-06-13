"""
Baixa a curva DI (futuros DI1) da B3.
Usada para precificação de papéis CDI e projeção de cupons flutuantes.
"""
import re
import requests
from datetime import date as dt_date, datetime
from .db import get_conn


B3_FUTURES_URL = "https://sistemaswebb3-derivativos.b3.com.br/futures-prices/search"
B3_SETTLEMENT_URL = "https://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-ajustes-do-pregao-ptBR.asp"


def _parse_vencimento_di(codigo: str) -> str | None:
    """
    Converte código DI1 (ex: DI1F27 = jan/2027) para YYYY-MM-DD.
    Letras de mês ANBIMA: F=Jan, G=Feb, H=Mar, J=Apr, K=May, M=Jun,
                           N=Jul, Q=Aug, U=Sep, V=Oct, X=Nov, Z=Dec
    """
    meses = {"F": 1, "G": 2, "H": 3, "J": 4, "K": 5, "M": 6,
             "N": 7, "Q": 8, "U": 9, "V": 10, "X": 11, "Z": 12}
    m = re.match(r"DI1([FGHJKMNQUVXZ])(\d{2})$", codigo.upper().strip())
    if not m:
        return None
    mes = meses[m.group(1)]
    ano = 2000 + int(m.group(2))
    # Primeiro dia útil do mês de vencimento (aproximação: dia 1)
    return f"{ano}-{mes:02d}-01"


def sync_di_curve_b3():
    """
    Tenta baixar a curva DI via API pública da B3.
    Fallback: scraping do HTML de ajustes do pregão.
    """
    print("Baixando curva DI da B3...")
    curve_date = dt_date.today().isoformat()
    rows = []

    try:
        # Tentativa 1: API JSON da B3
        params = {
            "language": "pt-br",
            "pageNumber": 1,
            "pageSize": 200,
        }
        headers = {
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://www.b3.com.br",
            "Referer": "https://www.b3.com.br/",
        }
        r = requests.get(B3_FUTURES_URL, params=params, headers=headers, timeout=30)
        if r.status_code == 200:
            items = r.json().get("data", {}).get("items", []) or r.json().get("items", [])
            for item in items:
                code = item.get("ticker") or item.get("code") or ""
                if not code.startswith("DI1"):
                    continue
                price = item.get("settlementPrice") or item.get("preco") or 0
                maturity = _parse_vencimento_di(code)
                if maturity and price:
                    # Preço DI1: PU = 100000 / (1 + r/100)^(du/252)
                    # Inverter para taxa
                    du = _business_days_approx(curve_date, maturity)
                    if du > 0:
                        rate = ((100000 / float(price)) ** (252 / du) - 1) * 100
                        rows.append((curve_date, maturity, rate))

    except Exception as e:
        print(f"  API B3 indisponível ({e}), tentando scraping HTML...")

    if not rows:
        rows = _scrape_b3_html(curve_date)

    if rows:
        with get_conn() as conn:
            conn.execute("DELETE FROM di_curve WHERE curve_date=?", (curve_date,))
            conn.executemany(
                "INSERT OR REPLACE INTO di_curve (curve_date, maturity, rate_annual) VALUES (?,?,?)",
                rows,
            )
        print(f"Curva DI: {len(rows)} vértices salvos para {curve_date}")
    else:
        print("  Não foi possível baixar a curva DI. Usando CDI flat como fallback.")
        _fallback_flat_curve(curve_date)


def _scrape_b3_html(curve_date: str) -> list[tuple]:
    """Scraping do HTML de ajustes do pregão B3 para DI1."""
    try:
        date_br = datetime.fromisoformat(curve_date).strftime("%Y%m%d")
        r = requests.get(
            B3_SETTLEMENT_URL,
            params={"Data": date_br},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        if r.status_code != 200:
            return []

        rows = []
        meses = {"jan": "01", "fev": "02", "mar": "03", "abr": "04",
                 "mai": "05", "jun": "06", "jul": "07", "ago": "08",
                 "set": "09", "out": "10", "nov": "11", "dez": "12"}

        pattern = re.compile(
            r"DI1\s+(\w{3}/\d{4})\s+[\d,.]+\s+([\d,.]+)", re.IGNORECASE
        )
        for m in pattern.finditer(r.text):
            try:
                mes_ano = m.group(1).lower()
                price = float(m.group(2).replace(".", "").replace(",", "."))
                p = mes_ano.split("/")
                mes = meses.get(p[0], "01")
                ano = p[1]
                maturity = f"{ano}-{mes}-01"
                du = _business_days_approx(curve_date, maturity)
                if du > 0 and price > 0:
                    rate = ((100000 / price) ** (252 / du) - 1) * 100
                    rows.append((curve_date, maturity, rate))
            except Exception:
                continue
        return rows
    except Exception as e:
        print(f"  Scraping falhou: {e}")
        return []


def _fallback_flat_curve(curve_date: str):
    """Usa CDI atual como curva flat para todos os vencimentos."""
    from .sync_bacen import get_last_cdi_rate
    rate = get_last_cdi_rate() or 11.0
    maturities = []
    from dateutil.relativedelta import relativedelta
    base = datetime.fromisoformat(curve_date)
    for months in [3, 6, 9, 12, 18, 24, 36, 48, 60, 84, 120]:
        m = (base + relativedelta(months=months)).strftime("%Y-%m-01")
        maturities.append((curve_date, m, rate))

    with get_conn() as conn:
        conn.execute("DELETE FROM di_curve WHERE curve_date=?", (curve_date,))
        conn.executemany(
            "INSERT OR REPLACE INTO di_curve VALUES (?,?,?)",
            maturities,
        )
    print(f"  Curva flat: {len(maturities)} vértices a {rate:.2f}% ao ano")


def _business_days_approx(start: str, end: str) -> int:
    """Aproximação de dias úteis (252/ano)."""
    d0 = datetime.fromisoformat(start)
    d1 = datetime.fromisoformat(end)
    cal_days = (d1 - d0).days
    return max(1, int(cal_days * 252 / 365))


def get_di_rate_for_date(target_date: str, curve_date: str | None = None) -> float:
    """
    Retorna a taxa DI interpolada para um vencimento específico.
    Usa interpolação linear (log-linear na prática) entre os vértices.
    """
    if curve_date is None:
        curve_date = dt_date.today().isoformat()

    with get_conn() as conn:
        rows = conn.execute("""
            SELECT maturity, rate_annual FROM di_curve
            WHERE curve_date = ?
            ORDER BY maturity
        """, (curve_date,)).fetchall()

    if not rows:
        from .sync_bacen import get_last_cdi_rate
        return get_last_cdi_rate() or 11.0

    mats = [(r["maturity"], r["rate_annual"]) for r in rows]

    if target_date <= mats[0][0]:
        return mats[0][1]
    if target_date >= mats[-1][0]:
        return mats[-1][1]

    for i in range(len(mats) - 1):
        if mats[i][0] <= target_date <= mats[i + 1][0]:
            d0, r0 = mats[i]
            d1, r1 = mats[i + 1]
            t0 = _business_days_approx(curve_date, d0)
            t1 = _business_days_approx(curve_date, d1)
            t = _business_days_approx(curve_date, target_date)
            if t1 == t0:
                return r0
            # interpolação log-linear
            import math
            f0 = (1 + r0 / 100) ** (t0 / 252)
            f1 = (1 + r1 / 100) ** (t1 / 252)
            ft = f0 * (f1 / f0) ** ((t - t0) / (t1 - t0))
            return ((ft ** (252 / t)) - 1) * 100

    return mats[-1][1]


if __name__ == "__main__":
    sync_di_curve_b3()
