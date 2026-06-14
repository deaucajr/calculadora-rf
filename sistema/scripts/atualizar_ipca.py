#!/usr/bin/env python
"""
Atualiza o IPCA (todo o historico do BACEN + projecao ANBIMA) e, SE saiu mes novo
de IPCA, refresca a VNA dos ativos IPCA (re-importa so eles). Pensado para rodar
3x/dia (10h, 12h, 17h) cobrindo a divulgacao do IPCA, para que NTN-B e ativos
IPCA+ nao fiquem com VNA defasada.

  python atualizar_ipca.py                  -> SO o IPCA publico (BACEN + ANBIMA)
  python atualizar_ipca.py --refresh-ativos -> tambem refresca a VNA EXATA dos ativos
                                               IPCA via calc API (so se ha mes novo)
  python atualizar_ipca.py --agendar        -> 3 tarefas no Windows (10:00/12:00/17:00)

Por padrao NAO toca na calc API: so o IPCA do BACEN + projecao ANBIMA (publico) —
que e o que muda quando sai IPCA. O add-in ja extrapola a VNA dos IPCA+ por esse
ritmo (nao da erro). O --refresh-ativos e um EXTRA opcional para deixar a VNA
EXATA (re-importa so os ativos IPCA, e so quando ha mes novo de IPCA).
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


def run(refrescar_ativos=False):
    from src.sync_bacen import sync_ipca, sync_anbima_ipca_projection
    from importar_todos import log
    log("=== ATUALIZAR IPCA ===")
    try:
        sync_ipca(start="01/01/2000")          # todo o historico (BACEN, publico)
        log("  IPCA historico (BACEN) ok")
    except Exception as e:
        log(f"  sync_ipca: {e}")
    try:
        sync_anbima_ipca_projection()          # projecao ANBIMA (ou extrapolacao)
        log("  projecao IPCA (ANBIMA) ok")
    except Exception as e:
        log(f"  projecao: {e}")
    # EXTRA opcional: VNA exata via calc API (so com --refresh-ativos, credenciais e mes novo)
    if refrescar_ativos:
        if _tem_credenciais():
            from rotina_diaria import refresh_ipca_se_novo
            refresh_ipca_se_novo()
        else:
            log("  --refresh-ativos pedido mas sem credenciais (credenciais.txt) — pulado")
    log("=== FIM ATUALIZAR IPCA ===")


if __name__ == "__main__":
    if "--agendar" in sys.argv:
        agendar()
    else:
        run(refrescar_ativos="--refresh-ativos" in sys.argv)
