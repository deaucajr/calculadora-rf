#!/usr/bin/env python
"""
Reconciliacao: confere se TODO ativo do universo da CALC/B3 tem o CSV de fluxo
no SEU computador.

A pasta dos fluxos e a configurada em config.json -> "fluxos_dir" (pode ser local
ou na nuvem, ex: OneDrive/Dropbox). Em branco, usa <projeto>/data/fluxos. Assim
cada pessoa que baixar o codigo aponta para a propria pasta sem mexer no codigo.

Uso:
  python verificar_cadastro.py            -> so RELATA cobertura e o que falta
  python verificar_cadastro.py --baixar   -> baixa (cadastra) na API o que falta
  python verificar_cadastro.py --refresh  -> reconsulta o universo na B3 (sem cache)

Listar o universo usa a API (precisa de credenciais em credenciais.txt). O
--baixar tambem chama a API, apenas para os ativos que faltam (poupa requisicoes).
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.paths import fluxos_dir
from importar_todos import carregar_universo, ultimo_dia_util
from importar_fluxos import importar_ticker

TIPOS = ("deb", "cri", "cra")


def tickers_locais(pasta: Path) -> set[str]:
    """Tickers que ja tem CSV de fluxo no PC (ignora arquivos _auxiliares)."""
    return {p.stem.upper() for p in pasta.glob("*.csv") if not p.name.startswith("_")}


def main(argv):
    baixar = "--baixar" in argv
    refresh = "--refresh" in argv

    pasta = fluxos_dir()
    print(f"Pasta dos fluxos : {pasta}")
    locais = tickers_locais(pasta)
    print(f"Ativos com CSV no PC: {len(locais)}\n")

    print("Consultando o universo da CALC/B3 (deb/cri/cra)...")
    uni = carregar_universo(refresh=refresh)

    faltam_total, universo_total = [], set()
    print(f"\n{'TIPO':5}{'universo':>10}{'no PC':>8}{'faltam':>8}")
    print("-" * 31)
    for tipo in TIPOS:
        univ = {t.upper() for t in uni.get(tipo, [])}
        universo_total |= univ
        faltam = sorted(univ - locais)
        faltam_total += faltam
        print(f"{tipo.upper():5}{len(univ):>10}{len(univ & locais):>8}{len(faltam):>8}")
    print("-" * 31)

    extras = sorted(locais - universo_total)
    if extras:
        print(f"\nObs: {len(extras)} CSV locais nao estao no universo atual "
              f"(ativos vencidos/retirados). Ex: {extras[:8]}")

    if not faltam_total:
        print("\n[ OK ] Voce tem TODOS os ativos do universo cadastrados no PC.")
        return 0

    print(f"\n[FALTAM] {len(faltam_total)} ativos sem CSV no PC. Ex: {faltam_total[:15]}")

    if not baixar:
        print("\nPara baixar/cadastrar SO os que faltam, rode:")
        print("   python scripts/verificar_cadastro.py --baixar")
        return 1

    data = ultimo_dia_util()
    print(f"\nBaixando {len(faltam_total)} faltantes da API (data {data})...")
    ok = err = 0
    for i, t in enumerate(faltam_total, 1):
        try:
            st = importar_ticker(t, data)
            ok += 1
            marca = "OK" if not str(st).upper().startswith("ERRO") else "!!"
            print(f"  [{i}/{len(faltam_total)}] {marca} {t}: {st}")
        except Exception as e:
            err += 1
            print(f"  [{i}/{len(faltam_total)}] !! {t}: ERRO {e}")
        time.sleep(0.4)  # poupa a API
    print(f"\nConcluido: {ok} baixados, {err} com erro. "
          f"Reabra o Excel para usar os novos ativos.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
