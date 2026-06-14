#!/usr/bin/env python
"""
Atualiza o IPCA (todo o historico do BACEN + projecao ANBIMA) e, SE saiu mes novo
de IPCA, refresca a VNA dos ativos IPCA (re-importa so eles). Pensado para rodar
3x/dia (10h, 12h, 17h) cobrindo a divulgacao do IPCA, para que NTN-B e ativos
IPCA+ nao fiquem com VNA defasada.

  python atualizar_ipca.py            -> roda a atualizacao agora
  python atualizar_ipca.py --agendar  -> cria 3 tarefas no Windows (10:00/12:00/17:00)

O sync do IPCA/projecao e PUBLICO (BACEN/ANBIMA). O refresh dos ativos IPCA usa a
API da calculadora (precisa de credenciais) e so dispara quando ha mes novo —
entao normalmente nao bate na API.
"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BASE))

HORARIOS = ("10:00", "12:00", "17:00")


def agendar():
    """Cria/atualiza 3 tarefas diarias no Agendador do Windows."""
    py = sys.executable
    script = str(BASE / "atualizar_ipca.py")
    for hh in HORARIOS:
        nome = "RF_IPCA_" + hh.replace(":", "")
        cmd = ["schtasks", "/Create", "/TN", nome, "/SC", "DAILY", "/ST", hh,
               "/TR", f'"{py}" "{script}"', "/F", "/RL", "LIMITED"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(f"{nome} ({hh}): {(r.stdout or r.stderr).strip()}")
    print("\nPronto. O Windows vai atualizar o IPCA as 10h, 12h e 17h, dias uteis e nao uteis.")


def _tem_credenciais():
    try:
        from src.api_client import load_config
        login = str(load_config().get("api", {}).get("login", ""))
        return bool(login) and "SEU_LOGIN" not in login
    except Exception:
        return False


def run():
    from src.sync_bacen import sync_ipca, sync_anbima_ipca_projection
    from importar_todos import log
    log("=== ATUALIZAR IPCA ===")
    try:
        sync_ipca(start="01/01/2000")          # todo o historico
        log("  IPCA historico (BACEN) ok")
    except Exception as e:
        log(f"  sync_ipca: {e}")
    try:
        sync_anbima_ipca_projection()          # projecao ANBIMA (ou extrapolacao)
        log("  projecao IPCA (ANBIMA) ok")
    except Exception as e:
        log(f"  projecao: {e}")
    # refresh da VNA dos ativos IPCA SO se saiu mes novo (e se houver credenciais)
    if _tem_credenciais():
        from rotina_diaria import refresh_ipca_se_novo
        refresh_ipca_se_novo()
    else:
        log("  (sem credenciais: nao refresco ativos IPCA — so historico/projecao)")
    log("=== FIM ATUALIZAR IPCA ===")


if __name__ == "__main__":
    if "--agendar" in sys.argv:
        agendar()
    else:
        run()
