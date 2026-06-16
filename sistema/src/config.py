"""
Carregador de tokens e configuração.
Lê do arquivo tokens.txt (gitignored) — NUNCA hardcoda senhas no código.
"""
import os
from pathlib import Path
from typing import Optional

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
_TOKENS_PATH = _CONFIG_DIR / "tokens.txt"
_TEMPLATE_PATH = _CONFIG_DIR / "tokens_template.txt"

_cache: dict[str, str] = {}
_loaded = False


def _load_tokens() -> dict[str, str]:
    """Lê o arquivo tokens.txt e retorna dict com as variáveis."""
    global _cache, _loaded
    if _loaded:
        return _cache

    tokens: dict[str, str] = {}

    # Primeiro tenta o arquivo real (gitignored)
    path = _TOKENS_PATH if _TOKENS_PATH.exists() else _TEMPLATE_PATH

    if not path.exists():
        return tokens

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("=="):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            tokens[key.strip()] = val.strip()

    _cache = tokens
    _loaded = True
    return tokens


def get_token(key: str) -> Optional[str]:
    """Retorna o valor de um token pelo nome da chave, ou None se não encontrado."""
    tokens = _load_tokens()
    val = tokens.get(key, "")
    if not val or val.startswith("SUA_") or val.startswith("seu."):
        return None
    return val


def get_required(key: str) -> str:
    """Retorna o token ou levanta erro se não configurado."""
    val = get_token(key)
    if val is None:
        raise RuntimeError(
            f"Token '{key}' não configurado. "
            f"Preencha {_TOKENS_PATH} (use {_TEMPLATE_PATH} como modelo)."
        )
    return val


def get_fluxos_dir() -> Path:
    """Retorna o diretório de fluxos (rede ou local)."""
    rede = get_token("REDE_FLUXOS_DIR")
    if rede:
        p = Path(rede)
        if p.exists():
            return p
    default = Path(__file__).resolve().parent.parent / "data" / "fluxos"
    default.mkdir(parents=True, exist_ok=True)
    return default


def reload_tokens():
    """Força recarregar o arquivo de tokens (útil se foi editado)."""
    global _loaded
    _loaded = False
    _cache.clear()
    return _load_tokens()
