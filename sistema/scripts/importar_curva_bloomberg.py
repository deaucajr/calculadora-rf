"""
Importa serie historica de contratos de DI Futuro no formato Bloomberg (OD*)
e converte para _curva_di.csv (mesma estrutura do RF_Calc).

Formato de entrada esperado (CSV ou Excel):
  - Coluna de indice: data do pregao (qualquer formato que pandas reconheca)
  - Colunas de contratos: ODF21, ODG21, ODH21, ... (OD = Bloomberg, DI1 = B3)
  - Valores: PU settlement (preco de ajuste B3, ex: 99.123 ou 99123.45)

Convencao de nomes Bloomberg vs B3:
  OD -> DI1  (prefixo Bloomberg -> B3)
  Codigo de mes: F=Jan G=Feb H=Mar J=Apr K=May M=Jun N=Jul Q=Aug U=Sep V=Oct X=Nov Z=Dec
  Ano: 2 digitos (21 = 2021, 26 = 2026)

Vencimento DI Futuro:
  Primeiro dia util do mes do contrato (calendario B3 simplificado).

PU -> taxa a.a.:
  taxa_aa = (100000 / PU)^(252/du) - 1
  Onde du = dias uteis de T+1 ate o vencimento inclusive.
  Nota: se o arquivo tiver PU em formato diferente (ex: 98.765 ao inves de 98765),
  o script tenta ambas as escalas automaticamente.

Saida: data/fluxos/_curva_di.csv (merge com dados existentes)

Uso:
  python scripts/importar_curva_bloomberg.py arquivo.csv
  python scripts/importar_curva_bloomberg.py arquivo.xlsx [--forcar] [--coldata NOME]

Opcoes:
  --forcar      Sobrescreve datas ja existentes em _curva_di.csv
  --coldata X   Nome da coluna de datas se nao for o indice (default: usa indice)
"""
import sys
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.paths import fluxos_dir

CURVA_CSV = fluxos_dir() / "_curva_di.csv"

# Codigo de mes Bloomberg/B3 -> numero do mes
MES_CODIGO = {
    "F": 1, "G": 2, "H": 3, "J": 4,
    "K": 5, "M": 6, "N": 7, "Q": 8,
    "U": 9, "V": 10, "X": 11, "Z": 12,
}

# Feriados nacionais fixos (mm, dd) — igual ao importar_curva_historica
_FERIADOS_FIXOS = {(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (11, 20), (12, 25)}


def _eh_dia_util(d: datetime.date) -> bool:
    return d.weekday() < 5 and (d.month, d.day) not in _FERIADOS_FIXOS


def _primeiro_dia_util(mes: int, ano: int) -> datetime.date:
    """Primeiro dia util do mes/ano (calendario BR simplificado)."""
    d = datetime.date(ano, mes, 1)
    while not _eh_dia_util(d):
        d += datetime.timedelta(days=1)
    return d


def _du(trade_date: datetime.date, expiry: datetime.date) -> int:
    """Dias uteis de T+1 ate vencimento inclusive."""
    cur = trade_date + datetime.timedelta(days=1)
    if cur > expiry:
        return 0
    count = 0
    while cur <= expiry:
        if _eh_dia_util(cur):
            count += 1
        cur += datetime.timedelta(days=1)
    return count


def _parse_contrato(col: str) -> tuple[int, int] | None:
    """
    Parseia coluna tipo 'ODF21' ou 'DI1F21' ou 'DI1F2021'.
    Retorna (mes, ano_4d) ou None se nao reconhecido.
    """
    col = col.upper().strip()
    if col.startswith("OD"):
        resto = col[2:]
    elif col.startswith("DI1"):
        resto = col[3:]
    else:
        return None
    if len(resto) < 3:
        return None
    mes_code = resto[0]
    ano_str = resto[1:]
    mes = MES_CODIGO.get(mes_code)
    if mes is None:
        return None
    try:
        ano_i = int(ano_str)
    except ValueError:
        return None
    # 4 digitos: 2021, 2026 etc
    if ano_i >= 1990:
        return (mes, ano_i)
    # 2 digitos: 21->2021, 90->1990
    ano4 = (1900 + ano_i) if ano_i >= 90 else (2000 + ano_i)
    return (mes, ano4)


def _pu_para_taxa(pu: float, du: int) -> float | None:
    """
    Converte PU B3 para taxa % a.a. (mesma escala de _curva_di.csv).
    PU B3: proximo a 100000 (ex: 93518.45); formato centesimal (93.51) tambem aceito.
    Retorna None se invalido.
    """
    if du <= 0 or pu <= 0:
        return None
    # Normaliza escala: PU B3 e nominalmente 100000. Se vier como 93.51, multiplica.
    pu_norm = pu if pu >= 1000 else pu * 1000
    taxa_dec = (100_000.0 / pu_norm) ** (252.0 / du) - 1.0
    taxa_pct = taxa_dec * 100  # converte para % (10.4 = 10.4% a.a.)
    # Sanidade: 0-100% a.a.
    return taxa_pct if 0 < taxa_pct < 100 else None


def _ler_curva_csv() -> dict[str, list[tuple[int, float]]]:
    curvas: dict[str, list[tuple[int, float]]] = {}
    if not CURVA_CSV.exists():
        return curvas
    for linha in CURVA_CSV.read_text(encoding="utf-8").splitlines():
        p = linha.split("\t")
        if len(p) == 3:
            try:
                curvas.setdefault(p[0], []).append((int(p[1]), float(p[2])))
            except ValueError:
                pass
    return curvas


def _gravar_curva_csv(curvas: dict[str, list[tuple[int, float]]]):
    CURVA_CSV.parent.mkdir(parents=True, exist_ok=True)
    linhas = []
    for data_iso in sorted(curvas):
        for du, taxa in sorted(curvas[data_iso]):
            linhas.append(f"{data_iso}\t{du}\t{taxa:.6f}")
    CURVA_CSV.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def importar_bloomberg(caminho: str, forcar: bool = False, col_data: str | None = None) -> int:
    """
    Importa serie historica Bloomberg OD* -> _curva_di.csv.
    Retorna numero de datas novas adicionadas.
    """
    try:
        import pandas as pd
        import numpy as np
    except ImportError:
        print("ERRO: pandas nao instalado. Execute: pip install pandas openpyxl")
        return 0

    path = Path(caminho)
    if not path.exists():
        print(f"ERRO: arquivo nao encontrado: {path}")
        return 0

    print(f"Carregando: {path.name}")
    ext = path.suffix.lower()
    if ext in (".xlsx", ".xls", ".xlsm"):
        df = pd.read_excel(path, index_col=None)
    else:
        # Tenta com diferentes separadores
        for sep in (",", ";", "\t"):
            try:
                df = pd.read_csv(path, sep=sep, index_col=None)
                if len(df.columns) > 1:
                    break
            except Exception:
                continue

    print(f"  {len(df)} linhas, {len(df.columns)} colunas")
    print(f"  Colunas: {list(df.columns)[:8]} ...")

    # Identifica coluna de datas
    if col_data:
        df.index = pd.to_datetime(df[col_data], dayfirst=True, errors="coerce")
        df = df.drop(columns=[col_data])
    else:
        # Tenta usar a primeira coluna como data
        primeira = df.columns[0]
        tentativa = pd.to_datetime(df[primeira], dayfirst=True, errors="coerce")
        if tentativa.notna().sum() > len(df) * 0.5:
            df.index = tentativa
            df = df.drop(columns=[primeira])
        else:
            df.index = pd.to_datetime(df.index, dayfirst=True, errors="coerce")

    # Identifica colunas de contratos DI
    contratos: dict[str, tuple[int, int]] = {}
    for col in df.columns:
        parsed = _parse_contrato(str(col))
        if parsed:
            contratos[col] = parsed

    if not contratos:
        print("ERRO: nenhuma coluna OD*/DI1* encontrada. Verifique o arquivo.")
        print(f"  Colunas disponiveis: {list(df.columns)}")
        return 0

    print(f"  Contratos identificados: {len(contratos)}")
    print(f"  Exemplos: {list(contratos.keys())[:8]}")

    # Pre-computa vencimentos
    expiries: dict[tuple[int, int], datetime.date] = {}
    for (mes, ano) in set(contratos.values()):
        try:
            expiries[(mes, ano)] = _primeiro_dia_util(mes, ano)
        except ValueError:
            pass  # mes/ano invalido

    curvas = {} if forcar else _ler_curva_csv()
    novas = 0
    ignoradas = 0
    linhas_sem_du: set[str] = set()

    for idx, row in df.iterrows():
        # Parseia data do pregao
        try:
            ts = pd.Timestamp(idx)
            if pd.isna(ts):
                continue
            trade_date = ts.date()
        except Exception:
            continue

        data_iso = trade_date.isoformat()
        if data_iso in curvas and not forcar:
            ignoradas += 1
            continue

        pontos: list[tuple[int, float]] = []
        for col, (mes, ano) in contratos.items():
            expiry = expiries.get((mes, ano))
            if expiry is None or trade_date >= expiry:
                continue  # contrato vencido nessa data

            try:
                pu = float(row[col])
            except (ValueError, TypeError, KeyError):
                continue
            if pu != pu or pu <= 0:  # NaN check
                continue

            du = _du(trade_date, expiry)
            if du <= 0:
                linhas_sem_du.add(col)
                continue

            taxa = _pu_para_taxa(pu, du)
            if taxa is not None:
                pontos.append((du, taxa))

        if pontos:
            pontos.sort()
            curvas[data_iso] = pontos
            novas += 1

    if linhas_sem_du:
        print(f"  Aviso: {len(linhas_sem_du)} contratos ignorados por du=0 (ja vencidos antes de T+1)")

    if novas:
        _gravar_curva_csv(curvas)
        print(f"Adicionadas {novas} datas ({ignoradas} ja existiam).")
        print(f"Salvo: {CURVA_CSV}")
    else:
        print(f"Nenhuma data nova ({ignoradas} ja existiam).")
    return novas


def _parse_args(args: list[str]) -> tuple[str, bool, str | None]:
    arquivo = ""
    forcar = "--forcar" in args
    col_data = None
    non_flags = [a for a in args if not a.startswith("--")]
    if non_flags:
        arquivo = non_flags[0]
    for i, a in enumerate(args):
        if a == "--coldata" and i + 1 < len(args):
            col_data = args[i + 1]
    return arquivo, forcar, col_data


if __name__ == "__main__":
    args = sys.argv[1:]
    arquivo, forcar, col_data = _parse_args(args)
    if not arquivo:
        print("Uso: python scripts/importar_curva_bloomberg.py ARQUIVO [--forcar] [--coldata NOME_COLUNA]")
        print("  ARQUIVO: .csv, .xlsx ou .xls com colunas OD*/DI1* e datas como indice/primeira coluna")
        print("  --forcar: sobrescreve datas ja existentes")
        print("  --coldata X: nome da coluna de datas (se nao for o indice nem a primeira coluna)")
        print()
        print("Exemplo de cabecalho CSV:")
        print("  data,ODF24,ODG24,ODH24,ODJ24,ODK24,ODM24,ODN24,ODQ24,ODU24")
        print("  2023-01-02,92350.45,92280.12,...")
        sys.exit(1)
    importar_bloomberg(arquivo, forcar=forcar, col_data=col_data)
