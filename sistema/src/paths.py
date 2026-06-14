"""
Fonte unica do caminho onde ficam os CSV de fluxo dos ativos.

Cada usuario pode apontar para a SUA pasta (local ou na nuvem) sem editar codigo:
basta definir "fluxos_dir" no config.json. Exemplos:
    "fluxos_dir": ""                                  -> padrao: <projeto>/data/fluxos
    "fluxos_dir": "C:/Users/voce/OneDrive/RF/fluxos"  -> pasta na nuvem
    "fluxos_dir": "~/Dropbox/rf_fluxos"               -> ~ expande p/ home

FONTE UNICA: defina a pasta UMA vez em config.json -> "fluxos_dir". Vale para os
scripts Python (ler/gravar) E para o add-in Excel — o setup/build propaga esse
caminho para onde o add-in le (rf_fluxos.txt), via aplicar_no_addin().
"""
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent     # .../sistema
CONFIG_PATH = BASE_DIR / "config.json"
PADRAO = BASE_DIR / "data" / "fluxos"
ADDIN_CFG = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "AddIns" / "rf_fluxos.txt"
DIST_CFG = BASE_DIR / "dist" / "rf_fluxos_dir.txt"


def caminho_configurado() -> str | None:
    """Valor bruto de fluxos_dir no config.json (None se vazio = usa o padrao local)."""
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return (cfg.get("fluxos_dir") or "").strip() or None
        except Exception:
            return None
    return None


def fluxos_dir(criar: bool = True) -> Path:
    """Pasta dos fluxos (config 'fluxos_dir' ou padrao data/fluxos). Cria se faltar."""
    destino = caminho_configurado()
    if destino:
        p = Path(destino).expanduser()
        if not p.is_absolute():
            p = BASE_DIR / p
    else:
        p = PADRAO
    if criar:
        p.mkdir(parents=True, exist_ok=True)
    return p


def aplicar_no_addin(propagar_dist: bool = True) -> dict:
    """Propaga o caminho de fluxos (config.json) para onde o ADD-IN le, para que
    scripts e add-in usem SEMPRE a mesma pasta:
      - %APPDATA%\\Microsoft\\AddIns\\rf_fluxos.txt   (o add-in DESTA maquina)
      - sistema/dist/rf_fluxos_dir.txt                (default p/ os colegas) —
        so se for um caminho EXPLICITO no config.json (compartilhado), nunca o
        padrao local. Retorna dict com o que foi escrito."""
    p = str(fluxos_dir(criar=False))
    res = {}
    try:
        if ADDIN_CFG.parent.exists():
            ADDIN_CFG.write_text(p + "\n", encoding="utf-8")
            res["addin"] = str(ADDIN_CFG)
    except Exception as e:
        res["addin_erro"] = str(e)
    if propagar_dist and caminho_configurado():
        try:
            DIST_CFG.parent.mkdir(parents=True, exist_ok=True)
            DIST_CFG.write_text(
                "# Caminho oficial da pasta de fluxos (gerado de config.json -> fluxos_dir).\n"
                "# Os colegas so rodam o instalar.bat; ele usa a linha abaixo.\n"
                + p + "\n", encoding="utf-8")
            res["dist"] = str(DIST_CFG)
        except Exception as e:
            res["dist_erro"] = str(e)
    return res


if __name__ == "__main__":
    print("fluxos_dir =", fluxos_dir(criar=False))
    print("aplicado em:", aplicar_no_addin())
