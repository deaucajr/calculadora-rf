"""
Sincroniza o cache de fluxos de caixa via calcPU da API.
Chamado uma vez por dia no daily_update.
Para cada ativo registrado: salva os finalValue + workingDays no flow_cache.
Isso permite recalcular PU/yield/duration localmente para qualquer taxa.
"""
import time
from datetime import date as dt_date

from .api_client import calc_pu_api
from .db import get_conn
from .sync_bonds import list_registered


def sync_flows(calc_date: str | None = None, delay_s: float = 0.5):
    """
    Baixa calcPU para todos os ativos registrados usando a taxa do contrato.
    calc_date: YYYY-MM-DD (default = hoje)
    """
    if calc_date is None:
        calc_date = dt_date.today().isoformat()

    tickers = list_registered()
    if not tickers:
        print("Nenhum ativo registrado.")
        return

    ok, skip, err = 0, 0, 0
    for ticker in tickers:
        try:
            with get_conn() as conn:
                bond = conn.execute(
                    "SELECT yield_contract, status FROM bonds WHERE ticker=?",
                    (ticker,)
                ).fetchone()

            if not bond:
                print(f"  ? {ticker}: não encontrado no cadastro, pule sync_bonds primeiro")
                skip += 1
                continue

            if bond["status"] != "A":
                skip += 1
                continue

            yield_ref = bond["yield_contract"] or 0.0
            result = calc_pu_api(ticker, calc_date, yield_ref)

            flows = result.get("cashFlowList", [])
            if not flows:
                skip += 1
                continue

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
                        ticker, calc_date, yield_ref,
                        f["date"], f["eventType"],
                        f["finalValue"], f["presentValue"], f["workingDays"],
                        vna, method,
                    ))

            ok += 1
            print(f"  ✓ {ticker}  PU={result.get('PU', '?'):.4f}  flows={len(flows)}")
            time.sleep(delay_s)

        except Exception as e:
            err += 1
            print(f"  ✗ {ticker}: {e}")

    print(f"\nFluxos: {ok} ok, {skip} pulados, {err} erros  (data={calc_date})")


if __name__ == "__main__":
    sync_flows()
