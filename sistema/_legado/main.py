#!/usr/bin/env python
"""
CLI principal do sistema de renda fixa.

Uso:
  python main.py pu  TICKER YIELD [DATA]      # PU dado yield
  python main.py taxa TICKER PU [DATA]         # yield dado PU
  python main.py add  TICKER                   # registra ativo e baixa fluxos
  python main.py sync                          # sincroniza todos os fluxos
  python main.py list                          # lista ativos registrados
  python main.py info TICKER                   # detalhes do ativo
  python main.py setup                         # inicializa banco e baixa dados base
"""
import sys
import json
from datetime import date as dt_date

# Garante que o pacote src é encontrado
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

from src.db import init_db, get_conn
from src.calc import calc_pu, calc_yield, bond_info
from src.sync_bonds import register_bond, sync_registered, list_registered
from src.sync_flows import sync_flows


def cmd_pu(ticker: str, yield_pct: float, calc_date: str | None = None):
    result = calc_pu(ticker.upper(), yield_pct, calc_date)
    _print_result(result)


def cmd_taxa(ticker: str, pu: float, calc_date: str | None = None):
    result = calc_yield(ticker.upper(), pu, calc_date)
    _print_result(result)


def cmd_add(ticker: str):
    data = register_bond(ticker.upper())
    sync_flows()  # atualiza fluxos após cadastro
    print(f"\nAtivo cadastrado: {data.get('codbond')} | {data.get('method')} | venc {data.get('expiredate')}")


def cmd_sync():
    sync_flows()


def cmd_list():
    tickers = list_registered()
    if not tickers:
        print("Nenhum ativo registrado. Use: python main.py add TICKER")
        return
    with get_conn() as conn:
        for t in tickers:
            row = conn.execute(
                "SELECT tipo, method, expiredate, status FROM bonds WHERE ticker=?", (t,)
            ).fetchone()
            if row:
                print(f"  {t:<14} {row['tipo']:<5} {row['method']:<15} venc:{row['expiredate']}  [{row['status']}]")
            else:
                print(f"  {t}  (sem detalhes — execute sync)")


def cmd_info(ticker: str):
    info = bond_info(ticker.upper())
    if not info:
        print(f"Ativo '{ticker}' não encontrado.")
        return
    print(json.dumps(info, indent=2, default=str, ensure_ascii=False))


def cmd_setup():
    print("=== Setup inicial ===")
    init_db()
    from src.sync_bacen import sync_cdi, sync_ipca, sync_anbima_ipca_projection
    from src.sync_b3_curve import sync_di_curve_b3
    sync_cdi(start="01/01/2010")
    sync_ipca(start="01/01/2000")
    sync_anbima_ipca_projection()
    sync_di_curve_b3()
    print("\n✓ Setup concluído. Agora registre seus ativos com: python main.py add TICKER")


def _print_result(r: dict):
    print(f"\n{'─'*40}")
    print(f"  Ativo      : {r['ticker']}")
    print(f"  Data       : {r['calc_date']}")
    print(f"  PU         : {r['PU']:.6f}")
    print(f"  Yield      : {r['yield']:.6f}% a.a.")
    print(f"  Duration   : {r['duration']:.4f} anos")
    if r.get('vna'):
        print(f"  VNA        : {r['vna']:.6f}")
    print(f"  Fonte      : {r['source']}  ({r['n_flows']} fluxos)")
    print(f"{'─'*40}\n")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0].lower()

    try:
        if cmd == "pu":
            if len(args) < 3:
                print("Uso: python main.py pu TICKER YIELD [DATA]")
                return
            date = args[3] if len(args) > 3 else None
            cmd_pu(args[1], float(args[2]), date)

        elif cmd == "taxa":
            if len(args) < 3:
                print("Uso: python main.py taxa TICKER PU [DATA]")
                return
            date = args[3] if len(args) > 3 else None
            cmd_taxa(args[1], float(args[2]), date)

        elif cmd == "add":
            if len(args) < 2:
                print("Uso: python main.py add TICKER")
                return
            cmd_add(args[1])

        elif cmd == "sync":
            date = args[1] if len(args) > 1 else None
            sync_flows(date)

        elif cmd == "list":
            cmd_list()

        elif cmd == "info":
            if len(args) < 2:
                print("Uso: python main.py info TICKER")
                return
            cmd_info(args[1])

        elif cmd == "setup":
            cmd_setup()

        else:
            print(f"Comando desconhecido: {cmd}")
            print(__doc__)

    except ValueError as e:
        print(f"\n⚠ Erro: {e}")
    except Exception as e:
        print(f"\n✗ Erro inesperado: {e}")
        raise


if __name__ == "__main__":
    main()
