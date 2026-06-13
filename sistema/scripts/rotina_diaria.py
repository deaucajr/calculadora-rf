#!/usr/bin/env python
"""
Rotina diaria: detecta ativos novos na B3, atualiza os existentes e mantem
os CSV de fluxo do dia. Pensada para o Agendador de Tarefas do Windows.

O que faz:
  1. Recarrega o universo (list deb/cri/cra) -> detecta novos ativos.
  2. Importa/atualiza todos para o ultimo dia util (resume: pula os ja feitos).
  3. Loga resumo em data/rotina_diaria.log.

Uso:
  python rotina_diaria.py            -> roda a rotina
  python rotina_diaria.py --agendar  -> cria a tarefa no Agendador (7h30, dias uteis)
"""
import sys
import subprocess
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
sys.path.insert(0, str(ROOT))


def agendar():
    """Cria tarefa no Agendador do Windows: 7h30, seg-sex."""
    py = sys.executable
    script = str(BASE / "rotina_diaria.py")
    cmd = [
        "schtasks", "/Create", "/TN", "RF_RotinaDiaria", "/SC", "WEEKLY",
        "/D", "MON,TUE,WED,THU,FRI", "/ST", "07:30",
        "/TR", f'"{py}" "{script}"', "/F", "/RL", "LIMITED",
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
    (ROOT / "data" / "fluxos" / "_cdi.csv").write_text("\n".join(out), encoding="utf-8")
    log(f"  _cdi.csv: {len(out)} dias (ultimo {rows[-1]['date']})")


def run():
    from importar_todos import carregar_universo, main as importar_main, log
    log("=== ROTINA DIARIA ===")
    atualizar_cdi()
    # 1. refresh do universo (detecta novos ativos)
    antes = {}
    try:
        import json
        uni_path = ROOT / "data" / "universo.json"
        if uni_path.exists():
            antes = json.loads(uni_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    uni = carregar_universo(refresh=True)
    for t in ("deb", "cri", "cra"):
        novos = set(uni.get(t, [])) - set(antes.get(t, []))
        if novos:
            log(f"  novos {t}: {len(novos)} -> {sorted(novos)[:10]}")
    # 2. importa/atualiza tudo p/ hoje (resume)
    importar_main(["deb", "cri", "cra"])
    log("=== ROTINA DIARIA FIM ===")


if __name__ == "__main__":
    if "--agendar" in sys.argv:
        agendar()
    else:
        run()
