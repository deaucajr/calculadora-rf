#!/usr/bin/env python
"""
Detecta se o FLUXO de algum ativo que voce ja tem mudou (resgate antecipado,
renegociacao de amortizacao/cupom, mudanca de vencimento) — SEM re-importar tudo.

Como economiza chamadas:
  * usa SO o getbonddetails (1 chamada LEVE por ativo), nao o calcPU (pesado);
  * compara uma "assinatura" (hash do cronograma) com a ultima salva;
  * verifica por RODIZIO um lote limitado por execucao (--max, padrao 300),
    sempre os menos-recentemente-verificados -> cobre todo o universo em poucos
    dias sem pico de requisicoes;
  * so re-importa (calcPU) os que realmente mudaram (com --atualizar).

Assinaturas ficam em data/_assinaturas.json (regeneravel, fora do git).

Uso:
  python verificar_mudancas.py                 -> checa um lote e RELATA mudancas
  python verificar_mudancas.py --max 500       -> tamanho do lote por execucao
  python verificar_mudancas.py --todos         -> varre TODOS de uma vez (pesado)
  python verificar_mudancas.py --atualizar     -> re-importa os que mudaram
"""
import hashlib
import json
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.paths import fluxos_dir
from src.api_client import get_bond_details
from importar_fluxos import importar_ticker
from importar_todos import ultimo_dia_util

ASSINATURAS = ROOT / "data" / "_assinaturas.json"
DELAY = 0.3  # s entre chamadas (poupa a API)


def assinatura(det: dict) -> str:
    """Hash estavel do que define o FLUXO: vencimento, VNE, taxa, metodo e o
    cronograma de eventos (data/tipo/taxa). Nao muda no dia a dia — so quando o
    contrato muda."""
    evs = sorted(
        (str(e.get("date")), str(e.get("eventType")), str(e.get("yield")))
        for e in det.get("events", [])
    )
    chave = json.dumps(
        [det.get("expiredate"), det.get("vne"), det.get("yield"),
         det.get("method"), evs],
        sort_keys=True, default=str,
    )
    return hashlib.sha1(chave.encode("utf-8")).hexdigest()[:16]


def tickers_locais(pasta: Path) -> list[str]:
    return sorted(p.stem.upper() for p in pasta.glob("*.csv")
                  if not p.name.startswith("_"))


def carregar_assinaturas() -> dict:
    if ASSINATURAS.exists():
        try:
            return json.loads(ASSINATURAS.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def main(argv):
    atualizar = "--atualizar" in argv
    todos = "--todos" in argv
    max_lote = 10**9 if todos else 300
    for i, a in enumerate(argv):
        if a == "--max" and i + 1 < len(argv):
            max_lote = int(argv[i + 1])

    pasta = fluxos_dir()
    locais = tickers_locais(pasta)
    sigs = carregar_assinaturas()
    hoje = date.today().isoformat()

    # rodizio: primeiro os nunca-verificados, depois os mais antigos
    fila = sorted(locais, key=lambda t: sigs.get(t, {}).get("ts", ""))
    lote = fila[:max_lote]

    print(f"Pasta dos fluxos : {pasta}")
    print(f"Ativos locais    : {len(locais)} | verificando agora: {len(lote)}"
          f"{' (TODOS)' if todos else f' (lote; rode de novo p/ continuar o rodizio)'}\n")

    mudou, novos, erros = [], 0, 0
    for n, tk in enumerate(lote, 1):
        try:
            det = get_bond_details(tk)
            s = assinatura(det)
            antiga = sigs.get(tk, {}).get("sig")
            sigs[tk] = {"sig": s, "ts": hoje}
            if antiga is None:
                novos += 1                      # 1a vez: vira baseline
            elif s != antiga:
                mudou.append(tk)
                print(f"  [{n}/{len(lote)}] MUDOU  {tk}")
        except Exception as e:
            erros += 1
            print(f"  [{n}/{len(lote)}] ERRO   {tk}: {e}")
        time.sleep(DELAY)

    ASSINATURAS.parent.mkdir(parents=True, exist_ok=True)
    ASSINATURAS.write_text(json.dumps(sigs, ensure_ascii=False), encoding="utf-8")

    print(f"\nResumo: {len(mudou)} mudaram | {novos} baseline (1a vez) | "
          f"{erros} erros | {len(lote)} verificados")
    restantes = sum(1 for t in locais if not sigs.get(t, {}).get("sig"))
    if restantes:
        print(f"Faltam {restantes} ativos para completar o 1o rodizio "
              f"(rode de novo, ou use --todos).")

    if not mudou:
        print("\n[ OK ] Nenhuma mudanca de fluxo detectada neste lote.")
        return 0

    print(f"\n[ATENCAO] Fluxo mudou em {len(mudou)} ativos: {mudou}")
    if not atualizar:
        print("Para re-importar SO esses, rode:")
        print("   python scripts/verificar_mudancas.py --atualizar")
        return 1

    data = ultimo_dia_util()
    print(f"\nRe-importando {len(mudou)} ativos alterados (data {data})...")
    ok = err = 0
    for tk in mudou:
        try:
            print(f"  {tk}: {importar_ticker(tk, data)}")
            ok += 1
        except Exception as e:
            print(f"  {tk}: ERRO {e}")
            err += 1
        time.sleep(DELAY)
    print(f"\nAtualizados: {ok} ok, {err} erro. Reabra o Excel.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
