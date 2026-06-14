#!/usr/bin/env python
"""
Insere um ativo MANUAL em fluxos_manual/ garantindo o formato certo (TAB + CRLF —
o add-in precisa de fim de linha Windows; LF puro quebra a leitura).

  python inserir_manual.py arquivo.csv      -> normaliza e copia p/ fluxos_manual/
  python inserir_manual.py --template ABC   -> cria um esqueleto ABC.csv p/ editar

Formato do CSV (separado por TAB):
  META<TAB>CAMPO<TAB>VALOR        (TICKER, TIPO, INDEXADOR, VENCIMENTO,
                                   DATA_FLUXO, VNE, TAXA_EMISSAO, ...)
  FLUXO<TAB>data<TAB>J|A<TAB>VF<TAB>PV<TAB>DU<TAB>FC%     (IPCA/PRE; FC% = fracao do VNA)
  VNA<TAB>data<TAB>valor                                  (1+ pontos de VNA)
Para CDI use linhas FLUXOD (data_calc, data_evento, evento, VF, PV, DU).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.paths import fluxos_manual_dir

TEMPLATE = [
    ["META", "TICKER", "{TK}"], ["META", "TIPO", "DEB"], ["META", "INDEXADOR", "PRE"],
    ["META", "EMISSOR", "MANUAL"], ["META", "METHOD", "PRE"],
    ["META", "VENCIMENTO", "2030-01-15"], ["META", "DATA_FLUXO", "2026-06-12"],
    ["META", "VNE", "1000.0"], ["META", "TAXA_EMISSAO", "12.0"],
    ["FLUXO", "2028-01-17", "J", "60", "55", "400", "0.06"],
    ["FLUXO", "2030-01-15", "A", "1000", "800", "900", "1.0"],
    ["VNA", "2026-06-12", "1000.0"], ["VNA", "2030-01-15", "1000.0"],
]


def _gravar_crlf(destino: Path, linhas_tab: list[str]):
    # newline="" + \r\n explicito -> garante CRLF (Windows), exigido pelo add-in
    destino.parent.mkdir(parents=True, exist_ok=True)
    with open(destino, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(linhas_tab) + "\r\n")


def template(ticker: str):
    tk = ticker.upper().strip()
    linhas = ["\t".join(c).replace("{TK}", tk) for c in TEMPLATE]
    destino = fluxos_manual_dir() / f"{tk}.csv"
    _gravar_crlf(destino, linhas)
    print(f"Template criado: {destino}\nEdite os valores e abra o Excel (=RF_PU(\"{tk}\";taxa;data)).")


def importar_arquivo(origem: str):
    src = Path(origem)
    txt = src.read_text(encoding="utf-8", errors="replace")
    linhas = [ln.rstrip("\r\n") for ln in txt.splitlines() if ln.strip()]
    # ticker: do META TICKER, senao o nome do arquivo
    tk = src.stem.upper()
    for ln in linhas:
        c = ln.split("\t")
        if c[0] == "META" and len(c) >= 3 and c[1].strip().upper() == "TICKER":
            tk = c[2].strip().upper()
            break
    destino = fluxos_manual_dir() / f"{tk}.csv"
    _gravar_crlf(destino, linhas)
    print(f"Inserido (CRLF): {destino}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--template" in args:
        i = args.index("--template")
        template(args[i + 1] if i + 1 < len(args) else "ABC")
    elif args:
        importar_arquivo(args[0])
    else:
        print("uso: python inserir_manual.py arquivo.csv  |  --template TICKER")
