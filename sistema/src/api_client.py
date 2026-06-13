import json
import time
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"
TOKEN_CACHE_PATH = BASE_DIR / "data" / ".token_cache.json"

BASE_URL = "https://calculadorarendafixa.com.br"
BOND_API = BASE_URL + "/bond-calculator-web/api"
BOND_FREE = BASE_URL + "/bond-calculator-web/free"


def _load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def _get_token() -> str:
    """Returns cached token or fetches a new one."""
    cfg = _load_config()
    cache = {}
    if TOKEN_CACHE_PATH.exists():
        try:
            cache = json.loads(TOKEN_CACHE_PATH.read_text())
        except Exception:
            pass

    ttl = cfg.get("token_cache_minutes", 55) * 60
    if cache.get("token") and (time.time() - cache.get("ts", 0)) < ttl:
        return cache["token"]

    resp = requests.post(
        BASE_URL + "/calculadora/login",
        json={"login": cfg["api"]["login"], "senha": cfg["api"]["senha"]},
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    token = resp.json()["Authorization"]
    TOKEN_CACHE_PATH.write_text(json.dumps({"token": token, "ts": time.time()}))
    return token


def _headers() -> dict:
    return {
        "Accept": "application/json",
        "Authorization": _get_token(),
        "origem": "S",
    }


def list_tickers(tipo: str = "deb") -> list[str]:
    """tipo: deb | cri | cra"""
    endpoints = {
        "deb": "/listbondcodes",
        "cri": "/listbondcodescri",
        "cra": "/listbondcodescra",
    }
    url = BOND_FREE + endpoints[tipo]
    r = requests.get(url, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def get_bond_details(ticker: str) -> dict:
    url = BOND_API + f"/getbonddetails/{ticker}"
    r = requests.get(url, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def calc_pu_api(ticker: str, date: str, yield_pct: float) -> dict:
    """date: YYYY-MM-DD, yield_pct: e.g. 3.5 for 3.5%"""
    url = BOND_API + f"/calcPU/{ticker}/{date}/{yield_pct}"
    r = requests.get(url, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def calc_yield_api(ticker: str, date: str, pu: float) -> dict:
    """date: YYYY-MM-DD, pu: bond price"""
    url = BOND_API + f"/calcyield/{ticker}/{date}/{pu}"
    r = requests.get(url, headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()
