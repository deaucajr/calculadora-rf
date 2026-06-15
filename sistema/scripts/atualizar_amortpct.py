#!/usr/bin/env python
"""
Atualiza as linhas AMORTPCT nos CSVs de ativos IPCA+ amortizantes ja importados,
sem precisar re-importar via calcPU (so getbonddetails, chamada leve).

Necessario para ativos importados ANTES da implementacao da correcao de amortizacao
(2026-06-14). Novos imports via importar_fluxos.py ja incluem AMORTPCT automaticamente.

Uso:
  python scripts/atualizar_amortpct.py           -> atualiza todos IPCA sem AMORTPCT
  python scripts/atualizar_amortpct.py --max 100 -> processa so os primeiros 100
  python scripts/atualizar_amortpct.py TICKER    -> atualiza um ticker especifico
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.paths import fluxos_dir
from src.api_client import get_bond_details

SEP = "\t"
DELAY = 0.3  # s entre chamadas


def _tem_amortpct(path: Path) -> bool:
    for ln in path.read_text(encoding="utf-8").splitlines():
        if ln.startswith("AMORTPCT"):
            return True
    return False


def _indexador_csv(path: Path) -> str:
    for ln in path.read_text(encoding="utf-8").splitlines():
        p = ln.split(SEP)
        if p[0] == "META" and len(p) >= 3 and p[1] == "INDEXADOR":
            return p[2].upper()
    return ""


def _atualizar(ticker: str) -> str:
    path = fluxos_dir() / f"{ticker}.csv"
    if not path.exists():
        return f"  {ticker}: CSV nao encontrado"
    if _indexador_csv(path) != "IPCA":
        return f"  {ticker}: nao IPCA, pulado"
    det = get_bond_details(ticker)
    amort_evs = sorted(
        (e["date"][:10], e["yield"])
        for e in det.get("events", [])
        if e.get("eventType") == "A"
    )
    if not amort_evs:
        return f"  {ticker}: sem eventos A (bullet? nao-amort?)"
    # reescreve CSV: remove linhas AMORTPCT antigas e adiciona novas
    linhas = [ln for ln in path.read_text(encoding="utf-8").splitlines()
              if not ln.startswith("AMORTPCT")]
    for d_iso, pct in amort_evs:
        linhas.append(SEP.join(["AMORTPCT", d_iso, f"{pct:.8f}"]))
    path.write_text("\n".join(linhas), encoding="utf-8")
    return f"  {ticker}: {len(amort_evs)} A events -> AMORTPCT ok"


def main():
    args = sys.argv[1:]
    if args and not args[0].startswith("--"):
        # ticker especifico
        print(_atualizar(args[0].upper()))
        return

    max_n = None
    for i, a in enumerate(args):
        if a == "--max" and i + 1 < len(args):
            max_n = int(args[i + 1])

    pasta = fluxos_dir()
    tickers = sorted(p.stem.upper() for p in pasta.glob("*.csv") if not p.name.startswith("_"))
    pendentes = [tk for tk in tickers if not _tem_amortpct(pasta / f"{tk}.csv")
                 and _indexador_csv(pasta / f"{tk}.csv") == "IPCA"]

    print(f"Ativos IPCA sem AMORTPCT: {len(pendentes)} de {len(tickers)} locais")
    if max_n:
        pendentes = pendentes[:max_n]
        print(f"Processando os primeiros {max_n}...")

    ok = 0
    for i, tk in enumerate(pendentes, 1):
        r = _atualizar(tk)
        print(f"[{i}/{len(pendentes)}] {r}")
        if "ok" in r:
            ok += 1
        time.sleep(DELAY)

    print(f"\nPronto: {ok} atualizados de {len(pendentes)} processados.")


if __name__ == "__main__":
    main()
