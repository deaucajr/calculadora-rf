#!/usr/bin/env python
"""
Rotina diaria: detecta ativos novos na B3, atualiza os existentes e mantem
os CSV de fluxo do dia. Pensada para o Agendador de Tarefas do Windows.

O que faz:
  1. Recarrega o universo (list deb/cri/cra) -> detecta novos ativos.
  2. Importa/atualiza todos para o ultimo dia util (resume: pula os ja feitos).
  3. Loga resumo em data/rotina_diaria.log.

Passos: CDI (BACEN) + curva DI x Pre (B3) publicos; ativos novos; e um RODIZIO
de deteccao de mudanca de fluxo (getbonddetails) que re-importa so o que mudou.

Modos:
  python rotina_diaria.py            -> COMPLETO: re-importa todos p/ hoje (pesado)
  python rotina_diaria.py --leve     -> LEVE: publicos + novos + rodizio (poucas
                                        chamadas; recomendado, pois o add-in ja
                                        precifica CDI por curva e IPCA/PRE
                                        independem da data)
  python rotina_diaria.py --agendar [--leve]  -> agenda no Windows (7h30, dias uteis)
"""
import sys
import subprocess
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
sys.path.insert(0, str(ROOT))


def agendar(leve=False):
    """Cria tarefa no Agendador do Windows: 7h30, seg-sex."""
    py = sys.executable
    script = str(BASE / "rotina_diaria.py")
    alvo = f'"{py}" "{script}"' + (" --leve" if leve else "")
    cmd = [
        "schtasks", "/Create", "/TN", "RF_RotinaDiaria", "/SC", "WEEKLY",
        "/D", "MON,TUE,WED,THU,FRI", "/ST", "07:30",
        "/TR", alvo, "/F", "/RL", "LIMITED",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout or r.stderr)


def atualizar_cdi():
    """Atualiza CDI do BACEN e reexporta fluxos/_cdi.csv (p/ DI-PERC no add-in)."""
    from src.sync_bacen import sync_cdi
    from src.db import get_conn
    from importar_todos import log
    try:
        sync_cdi(start="01/01/2026")
    except Exception as e:
        log(f"  sync_cdi: {e}")
    with get_conn() as c:
        rows = c.execute("SELECT date, rate_annual FROM cdi_daily ORDER BY date").fetchall()
    out = [f'{r["date"]}\t{float(r["rate_annual"]) / 100:.10f}' for r in rows]
    from src.paths import fluxos_dir
    (fluxos_dir() / "_cdi.csv").write_text("\n".join(out), encoding="utf-8")
    log(f"  _cdi.csv: {len(out)} dias (ultimo {rows[-1]['date']})")


def atualizar_curva_di():
    """Baixa a curva DI x Pre da B3 (ultimos pregoes) -> fluxos/_curva_di.csv."""
    from src.sync_b3_curve import sync_curva_di
    from importar_todos import log
    try:
        novas = sync_curva_di()
        log(f"  _curva_di.csv: {novas} datas novas")
    except Exception as e:
        log(f"  curva DI: {e}")


# quantos ativos checar por mudanca de fluxo a cada execucao (rodizio leve)
LOTE_MUDANCAS = 250


def verificar_mudancas_lote(atualizar=True):
    """Rodizio leve: checa LOTE_MUDANCAS ativos (getbonddetails) e re-importa
    so os que mudaram de fluxo. Poucas chamadas; cobre o universo em ~dias."""
    from importar_todos import log
    from verificar_mudancas import rodar
    try:
        res = rodar(max_lote=LOTE_MUDANCAS, atualizar=atualizar, log=lambda m: log(m))
        log(f"  mudancas de fluxo: {len(res['mudou'])} mudaram, "
            f"{res['novos']} baseline, {res['verificados']} verificados, "
            f"{res['restantes']} restantes no rodizio")
    except Exception as e:
        log(f"  verificar_mudancas: {e}")


def _novos_do_universo():
    """Refresh do universo e retorna o conjunto de tickers novos (por tipo)."""
    from importar_todos import carregar_universo, log
    import json
    antes = {}
    try:
        uni_path = ROOT / "data" / "universo.json"
        if uni_path.exists():
            antes = json.loads(uni_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    uni = carregar_universo(refresh=True)
    novos = {}
    for t in ("deb", "cri", "cra"):
        n = sorted(set(uni.get(t, [])) - set(antes.get(t, [])))
        if n:
            novos[t] = n
            log(f"  novos {t}: {len(n)} -> {n[:10]}")
    return novos


def run(leve=False):
    """leve=False: atualiza TODOS os ativos p/ hoje (pesado, ~1 calcPU/ativo).
    leve=True: so dados publicos (CDI/curva) + ativos novos + rodizio de
    mudancas — bem menos chamadas a API (recomendado no dia a dia, ja que o
    add-in precifica CDI por curva e IPCA/PRE independem da data)."""
    from importar_todos import main as importar_main, log, ultimo_dia_util
    from importar_fluxos import importar_ticker
    log(f"=== ROTINA DIARIA{' (leve)' if leve else ''} ===")
    atualizar_cdi()
    atualizar_curva_di()
    novos = _novos_do_universo()

    if leve:
        # importa so os ativos novos (poucas chamadas)
        data = ultimo_dia_util()
        for t, lst in novos.items():
            for tk in lst:
                try:
                    log(f"  novo {tk}: {importar_ticker(tk, data)}")
                except Exception as e:
                    log(f"  novo {tk}: ERRO {e}")
    else:
        importar_main(["deb", "cri", "cra"])     # refresh completo

    verificar_mudancas_lote(atualizar=True)        # rodizio de mudanca de fluxo
    log("=== ROTINA DIARIA FIM ===")


if __name__ == "__main__":
    if "--agendar" in sys.argv:
        agendar(leve="--leve" in sys.argv)
    else:
        run(leve="--leve" in sys.argv)
