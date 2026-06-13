#!/usr/bin/env python
"""
Rotina diária de atualização.
Agendar via Agendador de Tarefas do Windows para rodar todo dia útil às 7h.

O que faz:
  1. Baixa CDI do BACEN (somente os dias novos)
  2. Baixa IPCA do BACEN (somente se houver nova divulgação)
  3. Baixa curva DI da B3
  4. Sincroniza projeção IPCA ANBIMA
  5. Atualiza o flow_cache para todos os ativos registrados (1 calcPU por ativo)

Total de chamadas API: len(registered_bonds) + 1 login
"""
import sys
import logging
from datetime import date as dt_date
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "data" / "daily_update.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


def run():
    today = dt_date.today()
    log.info(f"=== Daily update {today} ===")

    from src.db import init_db
    init_db()

    # 1. CDI — baixa somente a diferença desde o último registro
    try:
        from src.db import get_conn
        from src.sync_bacen import sync_cdi
        with get_conn() as conn:
            row = conn.execute(
                "SELECT MAX(date) as last FROM cdi_daily"
            ).fetchone()
        last = row["last"] or "01/01/2000"
        # Converte YYYY-MM-DD → DD/MM/YYYY para a API BACEN
        from datetime import datetime
        last_dt = datetime.fromisoformat(last) if len(last) == 10 else datetime.strptime(last, "%d/%m/%Y")
        start_str = last_dt.strftime("%d/%m/%Y")
        n = sync_cdi(start=start_str)
        log.info(f"CDI: {n} novos registros")
    except Exception as e:
        log.error(f"CDI sync falhou: {e}")

    # 2. IPCA mensal
    try:
        from src.sync_bacen import sync_ipca
        n = sync_ipca(start="01/01/2025")
        log.info(f"IPCA: {n} registros")
    except Exception as e:
        log.error(f"IPCA sync falhou: {e}")

    # 3. Projeção ANBIMA
    try:
        from src.sync_bacen import sync_anbima_ipca_projection
        sync_anbima_ipca_projection()
        log.info("ANBIMA IPCA: ok")
    except Exception as e:
        log.error(f"ANBIMA sync falhou: {e}")

    # 4. Curva DI
    try:
        from src.sync_b3_curve import sync_di_curve_b3
        sync_di_curve_b3()
        log.info("Curva DI: ok")
    except Exception as e:
        log.error(f"Curva DI sync falhou: {e}")

    # 5. Flow cache
    try:
        from src.sync_flows import sync_flows
        sync_flows(today.isoformat())
        log.info("Flow cache: ok")
    except Exception as e:
        log.error(f"Flow cache sync falhou: {e}")

    # 6. Regenera o dashboard Excel
    try:
        from excel.generate_dashboard import generate
        path = generate()
        log.info(f"Dashboard Excel: {path}")
    except Exception as e:
        log.error(f"Dashboard Excel falhou: {e}")

    log.info("=== Daily update concluído ===\n")


if __name__ == "__main__":
    run()
