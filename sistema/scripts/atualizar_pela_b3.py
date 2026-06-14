#!/usr/bin/env python
"""
Atualiza ativos pela API da B3 (calculadorarendafixa).

Para cada ticker: baixa o fluxo OFICIAL para a pasta automatica (fluxos/<TICKER>.csv)
e, se o ticker estava na pasta MANUAL (fluxos_manual/), MOVE o arquivo manual para
fluxos_antigo/ (vira 'antigo'). Assim, o que voce criou a mao vira automatico e o
manual fica guardado como historico.

  python atualizar_pela_b3.py ABC [XYZ ...]

O add-in le fluxos/ (automatico) com prioridade sobre fluxos_manual/, entao apos
isso o ABC passa a ser o da B3 automaticamente. Precisa de credenciais (credenciais.txt).
"""
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.paths import fluxos_manual_dir, fluxos_antigo_dir
from importar_fluxos import importar_ticker
from importar_todos import ultimo_dia_util


def atualizar(tickers):
    data = ultimo_dia_util()
    man, ant = fluxos_manual_dir(), fluxos_antigo_dir()
    ok = err = 0
    for tk in tickers:
        tk = tk.upper().strip()
        try:
            st = importar_ticker(tk, data)          # grava em fluxos/<tk>.csv (automatico)
        except Exception as e:
            err += 1
            print(f"  {tk}: ERRO na B3 ({e}) — mantido como esta")
            continue
        if str(st).upper().startswith("ERRO"):
            err += 1
            print(f"  {tk}: B3 sem fluxo ({st}) — mantido manual")
            continue
        origem = man / f"{tk}.csv"
        if origem.exists():
            shutil.move(str(origem), str(ant / f"{tk}.csv"))
            print(f"  {tk}: atualizado pela B3; manual -> antigo. {st}")
        else:
            print(f"  {tk}: atualizado pela B3 (nao havia manual). {st}")
        ok += 1
        time.sleep(0.4)
    print(f"\nConcluido: {ok} atualizados, {err} com erro. Reabra o Excel.")


if __name__ == "__main__":
    alvos = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not alvos:
        print("uso: python atualizar_pela_b3.py TICKER [TICKER ...]")
        sys.exit(1)
    atualizar(alvos)
