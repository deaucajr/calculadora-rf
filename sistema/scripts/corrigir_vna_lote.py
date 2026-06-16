#!/usr/bin/env python
"""
Corrige EM LOTE todos os CSVs IPCA com VNA=1.0 re-sincronizando via FI Analytics/B3.

Para cada ticker com VNA quebrado:
  1. Chama sync_ticker() do novo motor
  2. VNA calculado LOCALMENTE via IPCA do BACEN
  3. TAI e AMORT recalculados com VNA correto

Uso:
  python corrigir_vna_lote.py           # corrige todos com VNA=1.0 (~0.5s/ativo)
  python corrigir_vna_lote.py --max 50  # corrige so 50 (teste)
  python corrigir_vna_lote.py --dry-run # lista quantos seriam corrigidos
"""
import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.paths import fluxos_dir
from src.sync_engine import sync_ticker
from src.fmt_br import parse_br


def encontrar_vna_quebrados() -> list[str]:
    """Retorna lista de tickers com VNA=1.0 nos CSVs."""
    fluxos = fluxos_dir(criar=True)
    quebrados = []
    for f in sorted(fluxos.glob("*.csv")):
        if f.name.startswith("_"):
            continue
        try:
            txt = f.read_text(encoding="utf-8")
            # So processa IPCA com VNA=1.0
            if "indexador;IPCA" not in txt and "indexador;ipca" not in txt:
                continue
            if not re.search(r'^vna;1,0+$', txt, re.MULTILINE):
                continue
            quebrados.append(f.stem)
        except Exception:
            pass
    return quebrados


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    max_n = None

    for a in sys.argv[1:]:
        if a.startswith("--max="):
            max_n = int(a.split("=")[1])
        elif a == "--max" and len(args) > 0:
            max_n = int(args[0])

    tickers = encontrar_vna_quebrados()
    print(f"Ativos IPCA com VNA=1.0: {len(tickers)}", flush=True)

    if dry_run:
        print("(DRY RUN — nada sera alterado)")
        if tickers:
            print(f"Exemplo: {tickers[:5]}")
        return

    if max_n:
        tickers = tickers[:max_n]
        print(f"Limitado a {max_n} ativos")

    ok = skip = err = 0
    t0 = time.time()

    for i, tk in enumerate(tickers, 1):
        try:
            r = sync_ticker(tk)
            if r["status"] == "OK":
                ok += 1
            else:
                err += 1
                if err <= 5:
                    print(f"  [ERRO] {tk}: {r.get('msg', '?')}")
        except Exception as e:
            err += 1
            if err <= 5:
                print(f"  [EXC] {tk}: {e}")

        time.sleep(0.3)  # respeita API

        if i % 100 == 0:
            elapsed = (time.time() - t0) / 60
            remaining = (len(tickers) - i) * elapsed / max(1, i)
            print(f"  [{i}/{len(tickers)}] ok={ok} err={err} | ~{remaining:.0f}min restantes", flush=True)

    elapsed = (time.time() - t0) / 60
    print(f"\nConcluido: ok={ok} err={err} | {elapsed:.1f} min")

    # Verifica quantos restam
    restantes = len(encontrar_vna_quebrados())
    print(f"Ativos ainda com VNA=1.0: {restantes}")


if __name__ == "__main__":
    main()
