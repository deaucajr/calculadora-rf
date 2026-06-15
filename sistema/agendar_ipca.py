"""
Agenda a atualizacao do IPCA 3x/dia (10h, 12h, 17h). Rode UMA vez.
Agenda a atualizacao do IPCA. Pode ser enviado por email.
"""
import subprocess
import sys
from pathlib import Path


def main():
    script = Path(__file__).resolve().parent / "scripts" / "atualizar_ipca.py"
    subprocess.run([sys.executable, str(script), "--agendar"], check=False)
    input("\nPressione Enter para sair...")


if __name__ == "__main__":
    main()
