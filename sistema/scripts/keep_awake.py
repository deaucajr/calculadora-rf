#!/usr/bin/env python
"""
Impede o Windows de hibernar/suspender enquanto este processo roda.
Usa SetThreadExecutionState (nao mexe em config de energia do sistema;
o estado normal volta sozinho quando o processo termina).

Uso:
  python keep_awake.py            -> mantem acordado ate Ctrl+C
  python keep_awake.py 8          -> mantem acordado por 8 horas e sai
"""
import ctypes
import sys
import time
from datetime import datetime

ES_CONTINUOUS       = 0x80000000
ES_SYSTEM_REQUIRED  = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

KEEP = ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
RESET = ES_CONTINUOUS


def main():
    horas = float(sys.argv[1]) if len(sys.argv) > 1 else None
    fim = time.time() + horas * 3600 if horas else None
    ctypes.windll.kernel32.SetThreadExecutionState(KEEP)
    print(f"[{datetime.now():%H:%M:%S}] keep-awake ATIVO"
          + (f" por {horas}h" if horas else " (ate Ctrl+C)"), flush=True)
    try:
        while True:
            # Reafirma a cada 50s (alguns sistemas expiram o flag)
            ctypes.windll.kernel32.SetThreadExecutionState(KEEP)
            time.sleep(50)
            if fim and time.time() >= fim:
                break
    except KeyboardInterrupt:
        pass
    finally:
        ctypes.windll.kernel32.SetThreadExecutionState(RESET)
        print(f"[{datetime.now():%H:%M:%S}] keep-awake encerrado", flush=True)


if __name__ == "__main__":
    main()
