"""
Baixa a curva de juros DI x Pre (taxas referenciais BM&FBOVESPA) da B3 e salva
em data/fluxos/_curva_di.csv para uso na precificacao de ativos CDI em qualquer
data disponivel.

Fonte (portal novo da B3, descoberto via inspecao do app Angular):
  Base:    https://sistemaswebb3-derivativos.b3.com.br/referenceRatesProxy/
  Metodos: Search/GetDate/<b64>   -> lista de datas disponiveis (ultimos ~20 pregoes)
           Search/GetList/<b64>   -> curva de uma data
  Param:   {"language":"pt-br","id":"PRE","date":"YYYY-MM-DD"}  (PRE = "DI x pre")
  Retorno: JSON duplo-encodado; results[] = {day252, day360, rate "14,40"}

Saida (TSV, lido pelo add-in RF_Calc):
  data/fluxos/_curva_di.csv
  colunas:  data_iso <TAB> du <TAB> taxa_aa
  (uma linha por vertice por data; merge incremental com o ja salvo)
"""
import base64
import json
from pathlib import Path

import requests

BASE = "https://sistemaswebb3-derivativos.b3.com.br/referenceRatesProxy/"
PRODUTO = "PRE"  # DI x Pre (curva de juros prefixada / desconto DI)
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://sistemaswebb3-derivativos.b3.com.br/referenceRatesPage/all?language=pt-br",
}
FLUXOS_DIR = Path(__file__).resolve().parent.parent / "data" / "fluxos"
CURVA_CSV = FLUXOS_DIR / "_curva_di.csv"


def _call(metodo: str, params: dict):
    """Chama o proxy da B3; trata o JSON duplo-encodado. Retorna objeto python."""
    b64 = base64.b64encode(json.dumps(params).encode()).decode()
    r = requests.get(BASE + metodo + "/" + b64, headers=HEADERS, timeout=40)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, str):          # vem como string JSON-encodada
        data = json.loads(data)
    return data


def datas_disponiveis() -> list[str]:
    """Datas (YYYY-MM-DD) com curva PRE publicada, mais recente primeiro."""
    dts = _call("Search/GetDate", {"language": "pt-br", "id": PRODUTO})
    return [d[:10] for d in dts]       # corta o 'T00:00:00'


def baixar_curva(data_iso: str) -> list[tuple[int, float]]:
    """Curva PRE de uma data: lista (du, taxa_aa). Vazia se nao houver."""
    res = _call("Search/GetList",
                {"language": "pt-br", "id": PRODUTO, "date": data_iso})
    out = []
    for v in res.get("results", []):
        du = int(v["day252"])
        taxa = float(str(v["rate"]).replace(".", "").replace(",", "."))
        out.append((du, taxa))
    out.sort()
    return out


def _ler_existente() -> dict[str, list[tuple[int, float]]]:
    """Le o _curva_di.csv atual em {data: [(du,taxa),...]}."""
    curvas: dict[str, list[tuple[int, float]]] = {}
    if not CURVA_CSV.exists():
        return curvas
    for linha in CURVA_CSV.read_text(encoding="utf-8").splitlines():
        p = linha.split("\t")
        if len(p) == 3:
            curvas.setdefault(p[0], []).append((int(p[1]), float(p[2])))
    return curvas


def _gravar(curvas: dict[str, list[tuple[int, float]]]):
    FLUXOS_DIR.mkdir(parents=True, exist_ok=True)
    linhas = []
    for data_iso in sorted(curvas):
        for du, taxa in sorted(curvas[data_iso]):
            linhas.append(f"{data_iso}\t{du}\t{taxa:.6f}")
    CURVA_CSV.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def sync_curva_di(forcar: bool = False) -> int:
    """
    Baixa todas as datas disponiveis ainda nao salvas e atualiza _curva_di.csv.
    Retorna o numero de datas novas gravadas. Use forcar=True p/ rebaixar tudo.
    """
    print("Curva DI x Pre (B3): consultando datas disponiveis...")
    disp = datas_disponiveis()
    print(f"  {len(disp)} datas publicadas (de {disp[-1]} a {disp[0]})")

    curvas = {} if forcar else _ler_existente()
    novas = 0
    for data_iso in disp:
        if data_iso in curvas and not forcar:
            continue
        pts = baixar_curva(data_iso)
        if pts:
            curvas[data_iso] = pts
            novas += 1
            print(f"  + {data_iso}: {len(pts)} vertices")

    if novas or forcar:
        _gravar(curvas)
        print(f"Salvo: {CURVA_CSV}  ({len(curvas)} datas, {novas} novas)")
    else:
        print("Nada novo a baixar (curvas ja atualizadas).")
    return novas


if __name__ == "__main__":
    import sys
    sync_curva_di(forcar="--forcar" in sys.argv)
