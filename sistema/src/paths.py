"""
Fonte única do caminho onde ficam os CSV de fluxo dos ativos.

Cada usuário pode apontar para a SUA pasta (local ou na nuvem) sem editar código:
basta definir REDE_FLUXOS_DIR no config/tokens.txt.

Precedência:
  1. Variável de ambiente RF_FLUXOS_DIR
  2. config/tokens.txt → REDE_FLUXOS_DIR
  3. Padrão local: sistema/data/fluxos/

FONTE ÚNICA: defina a pasta UMA vez. Vale para os scripts Python (ler/gravar)
E para o add-in Excel — o setup/build propaga esse caminho para onde o add-in lê.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent     # .../sistema
PADRAO = BASE_DIR / "data" / "fluxos"
ADDIN_CFG = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "AddIns" / "rf_fluxos.txt"
DIST_CFG = BASE_DIR / "dist" / "rf_fluxos_dir.txt"


def _config_path() -> str | None:
    """Lê o caminho da rede do tokens.txt (nova config) ou config.json (legado)."""
    # 1. Variável de ambiente (prioridade máxima)
    env = os.environ.get("RF_FLUXOS_DIR", "").strip()
    if env:
        return env

    # 2. tokens.txt (nova config)
    tokens_path = BASE_DIR / "config" / "tokens.txt"
    if tokens_path.exists():
        for line in tokens_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("REDE_FLUXOS_DIR="):
                val = line.split("=", 1)[1].strip()
                if val:
                    return val

    # 3. config.json (legado)
    import json
    cfg_path = BASE_DIR / "config.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            val = (cfg.get("fluxos_dir") or "").strip()
            if val:
                return val
        except Exception:
            pass

    return None


def fluxos_dir(criar: bool = True) -> Path:
    """Pasta dos fluxos AUTOMÁTICOS (FI Analytics + B3)."""
    destino = _config_path()
    if destino:
        p = Path(destino).expanduser()
        if not p.is_absolute():
            p = BASE_DIR / p
    else:
        p = PADRAO
    if criar:
        p.mkdir(parents=True, exist_ok=True)
    return p


def fluxos_manual_dir(criar: bool = True) -> Path:
    """Pasta dos ativos inseridos MANUALMENTE."""
    p = fluxos_dir(criar=False).parent / "fluxos_manual"
    if criar:
        p.mkdir(parents=True, exist_ok=True)
    return p


def fluxos_antigo_dir(criar: bool = True) -> Path:
    """Pasta dos CSVs superados por atualização."""
    p = fluxos_dir(criar=False).parent / "fluxos_antigo"
    if criar:
        p.mkdir(parents=True, exist_ok=True)
    return p


def aplicar_no_addin(propagar_dist: bool = True) -> dict:
    """Propaga o caminho de fluxos para onde o ADD-IN lê."""
    p = str(fluxos_dir(criar=False))
    res = {}
    try:
        if ADDIN_CFG.parent.exists():
            ADDIN_CFG.write_text(p + "\n", encoding="utf-8")
            res["addin"] = str(ADDIN_CFG)
    except Exception as e:
        res["addin_erro"] = str(e)
    if propagar_dist and _config_path():
        try:
            DIST_CFG.parent.mkdir(parents=True, exist_ok=True)
            DIST_CFG.write_text(
                "# Caminho oficial da pasta de fluxos (gerado de config/tokens.txt).\n"
                "# Os colegas só rodam o instalar.py; ele usa a linha abaixo.\n"
                + p + "\n", encoding="utf-8")
            res["dist"] = str(DIST_CFG)
        except Exception as e:
            res["dist_erro"] = str(e)
    return res


if __name__ == "__main__":
    print("fluxos_dir =", fluxos_dir(criar=False))
    print("aplicado em:", aplicar_no_addin())
