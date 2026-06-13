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


def rodar(max_lote=300, atualizar=False, todos=False, limite_auto=50, log=print) -> dict:
    """Verifica um lote (rodizio) e detecta fluxos alterados. Reutilizavel pela
    rotina diaria. Retorna dict com mudou/novos/erros/verificados/restantes.

    atualizar: re-importa os que mudaram. limite_auto: trava de seguranca — se
    mais que isso 'mudar' no lote (provavel falso alarme/mudanca de schema da
    API), NAO auto-reimporta; so avisa."""
    pasta = fluxos_dir()
    locais = tickers_locais(pasta)
    sigs = carregar_assinaturas()
    hoje = date.today().isoformat()
    lote_n = len(locais) if todos else max_lote

    # rodizio: primeiro os nunca-verificados, depois os mais antigos
    fila = sorted(locais, key=lambda t: sigs.get(t, {}).get("ts", ""))
    lote = fila[:lote_n]

    mudou, novos, erros = [], 0, 0
    for tk in lote:
        try:
            det = get_bond_details(tk)
            s = assinatura(det)
            antiga = sigs.get(tk, {}).get("sig")
            sigs[tk] = {"sig": s, "ts": hoje}
            if antiga is None:
                novos += 1                      # 1a vez: vira baseline
            elif s != antiga:
                mudou.append(tk)
        except Exception as e:
            erros += 1
            log(f"  ERRO {tk}: {e}")
        time.sleep(DELAY)

    ASSINATURAS.parent.mkdir(parents=True, exist_ok=True)
    ASSINATURAS.write_text(json.dumps(sigs, ensure_ascii=False), encoding="utf-8")
    restantes = sum(1 for t in locais if not sigs.get(t, {}).get("sig"))

    res = {"mudou": mudou, "novos": novos, "erros": erros,
           "verificados": len(lote), "restantes": restantes, "locais": len(locais)}

    if mudou:
        log(f"[ATENCAO] fluxo mudou em {len(mudou)}: {mudou}")
    if atualizar and mudou:
        if len(mudou) > limite_auto:
            log(f"  (auto-update ABORTADO: {len(mudou)} > limite {limite_auto} — "
                f"provavel falso alarme; revise e rode --atualizar manualmente.)")
        else:
            data = ultimo_dia_util()
            for tk in mudou:
                try:
                    log(f"  re-import {tk}: {importar_ticker(tk, data)}")
                except Exception as e:
                    log(f"  re-import {tk}: ERRO {e}")
                time.sleep(DELAY)
    return res


def main(argv):
    atualizar = "--atualizar" in argv
    todos = "--todos" in argv
    max_lote = 300
    for i, a in enumerate(argv):
        if a == "--max" and i + 1 < len(argv):
            max_lote = int(argv[i + 1])

    print(f"Pasta dos fluxos : {fluxos_dir()}")
    res = rodar(max_lote=max_lote, atualizar=atualizar, todos=todos)
    print(f"\nResumo: {len(res['mudou'])} mudaram | {res['novos']} baseline (1a vez) | "
          f"{res['erros']} erros | {res['verificados']} verificados de {res['locais']}")
    if res["restantes"]:
        print(f"Faltam {res['restantes']} para completar o 1o rodizio "
              f"(rode de novo, ou use --todos).")
    if not res["mudou"]:
        print("[ OK ] Nenhuma mudanca de fluxo detectada neste lote.")
        return 0
    if not atualizar:
        print("Para re-importar SO esses, rode: python scripts/verificar_mudancas.py --atualizar")
        return 1
    print("Atualizacao concluida. Reabra o Excel.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
