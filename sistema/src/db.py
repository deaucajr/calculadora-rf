import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "rf.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS bonds (
            ticker      TEXT PRIMARY KEY,
            tipo        TEXT NOT NULL,
            method      TEXT,
            issuer      TEXT,
            issuedate   TEXT,
            startingdate TEXT,
            expiredate  TEXT,
            anniversaryday INTEGER,
            vne         REAL,
            yield_contract REAL,
            status      TEXT,
            last_sync   TEXT
        );

        CREATE TABLE IF NOT EXISTS bond_events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker      TEXT NOT NULL,
            event_date  TEXT NOT NULL,
            event_type  TEXT NOT NULL,
            yield_pct   REAL,
            FOREIGN KEY (ticker) REFERENCES bonds(ticker)
        );

        CREATE TABLE IF NOT EXISTS flow_cache (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker        TEXT NOT NULL,
            calc_date     TEXT NOT NULL,
            ref_yield     REAL NOT NULL,
            event_date    TEXT NOT NULL,
            event_type    TEXT NOT NULL,
            final_value   REAL NOT NULL,
            present_value REAL NOT NULL,
            working_days  INTEGER NOT NULL,
            vna           REAL,
            method        TEXT,
            UNIQUE(ticker, calc_date, event_date, event_type)
        );

        CREATE TABLE IF NOT EXISTS cdi_daily (
            date        TEXT PRIMARY KEY,
            rate_annual REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ipca_monthly (
            date        TEXT PRIMARY KEY,
            rate_pct    REAL NOT NULL,
            source      TEXT DEFAULT 'BACEN'
        );

        CREATE TABLE IF NOT EXISTS ipca_projections (
            ref_date    TEXT NOT NULL,
            month       TEXT NOT NULL,
            rate_pct    REAL NOT NULL,
            source      TEXT DEFAULT 'ANBIMA',
            PRIMARY KEY (ref_date, month)
        );

        CREATE TABLE IF NOT EXISTS di_curve (
            curve_date  TEXT NOT NULL,
            maturity    TEXT NOT NULL,
            rate_annual REAL NOT NULL,
            PRIMARY KEY (curve_date, maturity)
        );

        CREATE TABLE IF NOT EXISTS manual_bonds (
            ticker        TEXT PRIMARY KEY,
            descricao     TEXT,
            tipo          TEXT,
            method        TEXT,
            startingdate  TEXT,
            expiredate    TEXT,
            vna_inicial   REAL,
            yield_contract REAL
        );

        CREATE TABLE IF NOT EXISTS manual_flows (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker      TEXT NOT NULL,
            event_date  TEXT NOT NULL,
            event_type  TEXT NOT NULL,
            value_pct   REAL,
            value_abs   REAL,
            FOREIGN KEY (ticker) REFERENCES manual_bonds(ticker)
        );
        """)
    print(f"DB inicializado em {DB_PATH}")


if __name__ == "__main__":
    init_db()
