#!/usr/bin/env python
"""
Importa TODOS os ativos da B3 (debentures, CRIs, CRAs) para fluxos/<TICKER>.csv.
Robusto: resume (pula os ja atualizados hoje), delays, log de progresso, tolera erros.

Uso:
  python importar_todos.py             -> importa tudo (resume automatico)
  python importar_todos.py deb         -> so debentures
  python importar_todos.py cri cra     -> CRIs e CRAs
  python importar_todos.py --status    -> quantos ja importados

Pensado para rodar em background (~1-1.5h para ~3500 ativos).
"""
import sys
import time
import json
from datetime import date as dt_date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.paths import fluxos_dir
FLUXOS_DIR = fluxos_dir()
LOG = ROOT / "data" / "import_massa.log"
UNIVERSO = ROOT / "data" / "universo.json"

from importar_fluxos import importar_ticker, gerar_feriados, _iso

DELAY = 0.4  # s entre ativos (poupa a API/senha)


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def ultimo_dia_util(ref: dt_date | None = None) -> str:
    fer = set(gerar_feriados())
    d = ref or dt_date.today()
    while d.weekday() >= 5 or d in fer:
        d -= timedelta(days=1)
    return d.isoformat()


def carregar_universo(refresh=False) -> dict:
    if UNIVERSO.exists() and not refresh:
        return json.loads(UNIVERSO.read_text(encoding="utf-8"))
    from src.api_client import list_tickers
    uni = {}
    for tipo in ["deb", "cri", "cra"]:
        uni[tipo] = list_tickers(tipo)
        log(f"universo {tipo}: {len(uni[tipo])}")
        time.sleep(0.5)
    UNIVERSO.parent.mkdir(exist_ok=True)
    UNIVERSO.write_text(json.dumps(uni), encoding="utf-8")
    return uni


def ja_atualizado(ticker: str, data_iso: str) -> bool:
    """True se o CSV existe e ja tem DATA_FLUXO == data_iso (resume)."""
    path = FLUXOS_DIR / f"{ticker.upper()}.csv"
    if not path.exists():
        return False
    try:
        for ln in path.read_text(encoding="utf-8").splitlines()[:15]:
            p = ln.split("\t")
            if len(p) >= 3 and p[0] == "META" and p[1] == "DATA_FLUXO":
                return p[2] == data_iso
    except Exception:
        return False
    return False


def status():
    n = len(list(FLUXOS_DIR.glob("*.csv"))) - len(list(FLUXOS_DIR.glob("_*.csv")))
    print(f"CSVs de ativos em fluxos/: {n}")


def main(tipos):
    FLUXOS_DIR.mkdir(exist_ok=True)
    data_iso = ultimo_dia_util()
    uni = carregar_universo()
    tickers = []
    for t in tipos:
        tickers += uni.get(t, [])
    log(f"=== Importacao em massa | data={data_iso} | {len(tickers)} ativos ({','.join(tipos)}) ===")

    ok = skip = err = 0
    t0 = time.time()
    for i, tk in enumerate(tickers, 1):
        if ja_atualizado(tk, data_iso):
            skip += 1
            continue
        try:
            msg = importar_ticker(tk, data_iso)
            if msg.startswith("OK"):
                ok += 1
            else:
                err += 1
                log(f"  {tk}: {msg}")
            time.sleep(DELAY)
        except Exception as e:
            err += 1
            log(f"  ERRO {tk}: {e}")
            time.sleep(DELAY)
        if i % 50 == 0:
            taxa = i / max(1, time.time() - t0)
            resta = (len(tickers) - i) / max(0.1, taxa)
            log(f"progresso {i}/{len(tickers)} | ok={ok} skip={skip} err={err} | ~{resta/60:.0f}min restantes")

    log(f"=== FIM | ok={ok} skip={skip} err={err} | {(time.time()-t0)/60:.1f}min ===")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--status" in sys.argv:
        status()
    else:
        tipos = args if args else ["deb", "cri", "cra"]
        main(tipos)
