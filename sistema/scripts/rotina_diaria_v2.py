#!/usr/bin/env python
"""
Rotina Diária do RF_Calc — versão 2 (FI Analytics como fonte primária).

Executa diariamente (ideal: 7h30 via Agendador de Tarefas):
  1. Atualiza CDI e IPCA do BACEN
  2. Sincroniza todos os ativos do FI Analytics (incremental)
  3. Enriquece dados com ANBIMA Data (opcional)
  4. Atualiza _feriados.csv
  5. Gera log e relatório de mudanças

Uso:
  python rotina_diaria_v2.py                 -> executa rotina completa
  python rotina_diaria_v2.py --agendar        -> registra no Agendador de Tarefas
  python rotina_diaria_v2.py --status         -> mostra status atual
  python rotina_diaria_v2.py --ticker EGIEA6  -> sincroniza um ticker específico
"""
import sys
import time
import json
from datetime import date as dt_date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.db import init_db, get_conn
from src.sync_engine import sync_incremental, sync_all, sync_ticker
from src.paths import fluxos_dir, aplicar_no_addin
from src.config import get_required


def rotina_completa(data_calc: str | None = None):
    """Executa a rotina completa de atualização diária."""
    if data_calc is None:
        data_calc = dt_date.today().isoformat()

    print(f"\n{'='*60}")
    print(f"  RF_CALC — ROTINA DIÁRIA v2")
    print(f"  Data: {data_calc}")
    print(f"  Início: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")

    init_db()

    # 1. BACEN
    print("[1/5] Atualizando dados BACEN...")
    from src import sync_bacen
    try:
        n_cdi = sync_bacen.sync_cdi()
        n_ipca = sync_bacen.sync_ipca()
        n_proj = sync_bacen.sync_anbima_ipca_projection()
        print(f"  CDI: {n_cdi} registros | IPCA: {n_ipca} registros | Projeções: {n_proj}")
    except Exception as e:
        print(f"  ⚠ Erro BACEN: {e}")

    # 2. FI Analytics (sincronização incremental)
    print("\n[2/5] Sincronizando FI Analytics (incremental)...")
    result = sync_incremental(data_calc)
    print(f"  OK={result['ok']} Pulo={result['skip']} Erro={result['err']}")

    # 3. ANBIMA Data (enriquecimento — opcional, apenas ativos novos)
    print("\n[3/5] Enriquecendo com ANBIMA Data...")
    try:
        from src.anbima_scraper import enriquecer_ticker
        with get_conn() as conn:
            novos = conn.execute("""
                SELECT ticker FROM bonds
                WHERE last_sync = ?
            """, (data_calc,)).fetchall()
        novos_tickers = [r["ticker"] for r in novos]
        enriquecidos = 0
        for tk in novos_tickers[:50]:  # limita a 50/dia pra não sobrecarregar
            try:
                enriquecer_ticker(tk)
                enriquecidos += 1
                time.sleep(1.5)
            except Exception:
                pass
        print(f"  {enriquecidos} ativos enriquecidos (de {len(novos_tickers)} novos)")
    except Exception as e:
        print(f"  ⚠ ANBIMA: {e}")

    # 4. Propagar caminho para o add-in
    print("\n[4/5] Atualizando configuração do add-in...")
    cfg = aplicar_no_addin()
    print(f"  {cfg}")

    # 5. Resumo
    print(f"\n[5/5] {'='*50}")
    print(f"  Fim: {datetime.now().strftime('%H:%M:%S')}")
    print(f"  Ativos sincronizados: {result['ok']}")
    print(f"  Erros: {result['err']}")
    print(f"{'='*50}\n")

    return result


def agendar(hora: str = "07:30"):
    """Registra a rotina no Agendador de Tarefas do Windows."""
    script_path = Path(__file__).resolve()
    python_exe = sys.executable
    task_name = "RF_Calc_RotinaDiaria_v2"

    # Via schtasks
    import subprocess
    cmd = (
        f'schtasks /Create /SC DAILY /TN "{task_name}" '
        f'/TR "\\"{python_exe}\\" \\"{script_path}\\"" '
        f'/ST {hora} /F'
    )
    print(f"Criando tarefa: {task_name} às {hora}")
    print(f"Comando: {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode == 0:
        print(f"✓ Tarefa agendada: {task_name} — {hora} diariamente")
    else:
        print(f"✗ Erro: {r.stderr}")
        print("Tente executar como Administrador.")


def status():
    """Mostra status atual da base."""
    init_db()
    with get_conn() as conn:
        n = conn.execute("SELECT COUNT(*) FROM bonds").fetchone()[0]
        n_sync = conn.execute(
            "SELECT COUNT(DISTINCT ticker) FROM bonds WHERE last_sync IS NOT NULL"
        ).fetchone()[0]
        ultimo = conn.execute(
            "SELECT MAX(last_sync) FROM bonds"
        ).fetchone()[0]

    fluxos = fluxos_dir(criar=False)
    n_csvs = len(list(fluxos.glob("*.csv"))) if fluxos.exists() else 0

    print(f"Base RF_Calc:")
    print(f"  Ativos cadastrados: {n}")
    print(f"  Já sincronizados:   {n_sync}")
    print(f"  Última sincronização: {ultimo or 'nunca'}")
    print(f"  CSVs em {fluxos}: {n_csvs}")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        rotina_completa()
    elif args[0] == "--agendar":
        agendar(args[1] if len(args) > 1 else "07:30")
    elif args[0] == "--status":
        status()
    elif args[0] == "--ticker" and len(args) > 1:
        r = sync_ticker(args[1])
        print(json.dumps(r, indent=2, ensure_ascii=False))
    elif args[0] == "--force":
        # Força sincronização completa (ignora resume)
        result = sync_all(resume=False)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(__doc__)
