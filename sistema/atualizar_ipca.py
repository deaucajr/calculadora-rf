"""
Atualiza o IPCA (historico BACEN + projecao ANBIMA) agora.
Atualiza o IPCA agora. Pode ser enviado por email.
"""
import subprocess
import sys
from pathlib import Path


def main():
    script = Path(__file__).resolve().parent / "scripts" / "atualizar_ipca.py"
    subprocess.run([sys.executable, str(script)], check=False)
    input("\nPressione Enter para sair...")


if __name__ == "__main__":
    main()
