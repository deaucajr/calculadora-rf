"""
Sincroniza o cadastro de debêntures, CRIs e CRAs da API.
Chama getbonddetails para cada ticker registrado.
"""
import json
import time
from datetime import datetime, date
from pathlib import Path

from .api_client import get_bond_details
from .db import get_conn

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_bond(data: dict):
    ticker = data["codbond"]
    tipo = data.get("tipoIF", {}).get("codigoAsString", "DEB")
    with get_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO bonds
              (ticker, tipo, method, issuer, issuedate, startingdate,
               expiredate, anniversaryday, vne, yield_contract, status, last_sync)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            ticker, tipo,
            data.get("method"),
            data.get("issuer"),
            data.get("issuedate"),
            data.get("startingdate"),
            data.get("expiredate"),
            data.get("anniversaryday"),
            data.get("vne"),
            data.get("yield"),
            data.get("status"),
            datetime.now().isoformat(timespec="seconds"),
        ))

        conn.execute("DELETE FROM bond_events WHERE ticker=?", (ticker,))
        for ev in data.get("events", []):
            conn.execute("""
                INSERT INTO bond_events (ticker, event_date, event_type, yield_pct)
                VALUES (?,?,?,?)
            """, (ticker, ev["date"], ev["eventType"], ev.get("yield")))


def sync_registered(delay_s: float = 0.3):
    """Sincroniza apenas os tickers listados em config.json → registered_bonds."""
    cfg = _load_config()
    tickers = cfg.get("registered_bonds", [])
    if not tickers:
        print("Nenhum ativo registrado em config.json → registered_bonds")
        return

    ok, err = 0, 0
    for ticker in tickers:
        try:
            data = get_bond_details(ticker)
            save_bond(data)
            ok += 1
            print(f"  OK {ticker}")
            time.sleep(delay_s)
        except Exception as e:
            err += 1
            print(f"  ERR {ticker}: {e}")

    print(f"\nSincronização concluída: {ok} ok, {err} erros")


def register_bond(ticker: str):
    """Adiciona um ticker ao config e sincroniza imediatamente."""
    cfg = _load_config()
    if ticker not in cfg.get("registered_bonds", []):
        cfg.setdefault("registered_bonds", []).append(ticker)
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
    data = get_bond_details(ticker)
    save_bond(data)
    print(f"Ativo {ticker} registrado com sucesso.")
    return data


def list_registered() -> list[str]:
    cfg = _load_config()
    return cfg.get("registered_bonds", [])


if __name__ == "__main__":
    sync_registered()
