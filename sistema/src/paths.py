"""
Fonte unica do caminho onde ficam os CSV de fluxo dos ativos.

Cada usuario pode apontar para a SUA pasta (local ou na nuvem) sem editar codigo:
basta definir "fluxos_dir" no config.json. Exemplos:
    "fluxos_dir": ""                                  -> padrao: <projeto>/data/fluxos
    "fluxos_dir": "C:/Users/voce/OneDrive/RF/fluxos"  -> pasta na nuvem
    "fluxos_dir": "~/Dropbox/rf_fluxos"               -> ~ expande p/ home

Vale para os scripts Python e tambem para o add-in Excel (o build_xlam grava
este caminho na constante FLUXOS_DIR do .xlam).
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent     # .../sistema
CONFIG_PATH = BASE_DIR / "config.json"
PADRAO = BASE_DIR / "data" / "fluxos"


def fluxos_dir(criar: bool = True) -> Path:
    """Pasta dos fluxos (config 'fluxos_dir' ou padrao data/fluxos). Cria se faltar."""
    destino = None
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            destino = (cfg.get("fluxos_dir") or "").strip() or None
        except Exception:
            destino = None
    if destino:
        p = Path(destino).expanduser()
        if not p.is_absolute():
            p = BASE_DIR / p
    else:
        p = PADRAO
    if criar:
        p.mkdir(parents=True, exist_ok=True)
    return p
