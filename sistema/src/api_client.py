import json
import time
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"
CREDENCIAIS_TXT = BASE_DIR / "credenciais.txt"
TOKEN_CACHE_PATH = BASE_DIR / "data" / ".token_cache.json"

BASE_URL = "https://calculadorarendafixa.com.br"
BOND_API = BASE_URL + "/bond-calculator-web/api"
BOND_FREE = BASE_URL + "/bond-calculator-web/free"


def _ler_credenciais_txt() -> dict:
    """Le login/senha de um credenciais.txt simples (linhas 'chave=valor' ou
    'chave: valor'; ignora # e linhas vazias). Aceita login/usuario/email e
    senha/password. Retorna {} se o arquivo nao existir."""
    if not CREDENCIAIS_TXT.exists():
        return {}
    out = {}
    for linha in CREDENCIAIS_TXT.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        sep = "=" if "=" in linha else (":" if ":" in linha else None)
        if not sep:
            continue
        chave, valor = linha.split(sep, 1)
        chave, valor = chave.strip().lower(), valor.strip()
        if chave in ("login", "usuario", "usuário", "email", "e-mail", "user"):
            out["login"] = valor
        elif chave in ("senha", "password", "pass"):
            out["senha"] = valor
    return out


def load_config() -> dict:
    """config.json (ajustes) sobreposto pelas credenciais do credenciais.txt,
    que tem prioridade. Assim o login/senha fica num txt fora do git, sem
    precisar editar o config.json."""
    cfg = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
    cfg.setdefault("api", {})
    cred = _ler_credenciais_txt()
    if cred:
        cfg["api"].update(cred)        # credenciais.txt tem prioridade
    return cfg


def _load_config() -> dict:            # compat
    return load_config()


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
