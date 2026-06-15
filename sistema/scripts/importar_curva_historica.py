"""
Baixa arquivos TaxaSwap (TS) historicos da B3 e extrai a curva DI x PRE.

Fonte: https://www.b3.com.br/pesquisapregao/download?filelist=TS{YYMMDD}.ex_,
  - outer: ZIP normal (PK header) que contem o inner SFX
  - inner: Windows SFX executavel (.ex_) que embute outro ZIP com TaxaSwap.txt
  - solucao: busca 'PK\x03\x04' dentro do binario SFX e abre como ZipFile

Formato TaxaSwap.txt (largura fixa, latin-1):
  [21:26] tipo ('PRE  ' = curva DI x Pre; 'CDI  ', 'USD  ', etc.)
  [41:46] du (dias uteis ate vencimento)
  [46:51] dc (dias corridos ate vencimento)
  [51]    sinal ('+' ou '-')
  [52:66] taxa (14 digitos, dividir por 1e9 para obter decimal a.a.)
  [66]    vertice ('F'=futuro, 'M'=mercado)

Saida: data/fluxos/_curva_di.csv (mesma estrutura do sync_b3_curve.py)
  data_iso<TAB>du<TAB>taxa_aa   (uma linha por vertice por data)

Uso:
  python scripts/importar_curva_historica.py 2024-01-01 2024-12-31
  python scripts/importar_curva_historica.py 2020-01-01 2025-12-31 --forcar
  python scripts/importar_curva_historica.py 2024-06-10 2024-06-10   # dia unico
"""
import sys
import io
import time
import zipfile
import datetime
import requests
import urllib3
urllib3.disable_warnings()
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.paths import fluxos_dir

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://www.b3.com.br/",
}

CURVA_CSV = fluxos_dir() / "_curva_di.csv"
DELAY = 0.5  # segundos entre downloads para nao sobrecarregar a B3

# Feriados nacionais fixos do Brasil (apenas os federais; Carnaval/Corpus Christi
# sao moveis e nao estao aqui — o impacto na contagem de du e minimo).
_FERIADOS_FIXOS = {(1, 1), (4, 21), (5, 1), (9, 7), (10, 12), (11, 2), (11, 15), (11, 20), (12, 25)}


def _eh_dia_util(d: datetime.date) -> bool:
    return d.weekday() < 5 and (d.month, d.day) not in _FERIADOS_FIXOS


def _dias_uteis(ini: datetime.date, fim: datetime.date) -> list[datetime.date]:
    dias = []
    cur = ini
    while cur <= fim:
        if _eh_dia_util(cur):
            dias.append(cur)
        cur += datetime.timedelta(days=1)
    return dias


def _baixar_taxaswap(data_iso: str) -> bytes | None:
    """Baixa o arquivo TaxaSwap da B3 para a data. Retorna None se indisponivel."""
    y, m, d = data_iso.split("-")
    yymmdd = y[2:] + m + d
    url = f"https://www.b3.com.br/pesquisapregao/download?filelist=TS{yymmdd}.ex_,"
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=60)
        if r.status_code != 200 or len(r.content) < 1000:
            return None
        return r.content
    except Exception:
        return None


def _extrair_taxaswap_txt(raw: bytes) -> str | None:
    """
    Extrai TaxaSwap.txt do arquivo double-nested:
      outer ZIP -> inner SFX binary -> inner ZIP (embutido no SFX) -> TaxaSwap.txt
    Retorna texto em latin-1, ou None se falhar.
    """
    try:
        # Nivel 1: outer e um ZIP normal
        outer = zipfile.ZipFile(io.BytesIO(raw))
        inner_bytes = outer.read(outer.namelist()[0])

        # Nivel 2: inner e um SFX Windows (PE exe). O ZIP real esta embutido nele.
        # Tecnica: busca assinatura PK\x03\x04 (local file header) dentro do binario.
        pk_off = inner_bytes.find(b"PK\x03\x04")
        if pk_off < 0:
            return None
        inner_zip = zipfile.ZipFile(io.BytesIO(inner_bytes[pk_off:]))
        names = inner_zip.namelist()
        # TaxaSwap.txt ou similar — pega o primeiro .TXT encontrado
        target = next((n for n in names if n.upper().endswith(".TXT")), names[0] if names else None)
        if target is None:
            return None
        return inner_zip.read(target).decode("latin-1")
    except Exception:
        return None


def _parsear_curva_pre(txt: str) -> list[tuple[int, float]]:
    """
    Extrai vertices PRE (DI x Pre) do TaxaSwap.txt.
    Retorna lista ordenada de (du, taxa_aa).
    """
    pontos = []
    for linha in txt.splitlines():
        if len(linha) < 67:
            continue
        tipo = linha[21:26].strip()
        if tipo != "PRE":
            continue
        try:
            du = int(linha[41:46].strip())
            sinal = -1 if linha[51] == "-" else 1
            taxa_raw = int(linha[52:66].strip())
            # /1e7 converte para % a.a. (ex: 104000000 -> 10.4) — mesmo formato
            # que sync_b3_curve.py usa (B3 API retorna "10,40" -> float 10.40)
            taxa_aa = sinal * taxa_raw / 10_000_000.0
            if du > 0 and 0 < taxa_aa < 100:  # sanidade: 0-100% a.a.
                pontos.append((du, taxa_aa))
        except (ValueError, IndexError):
            continue
    return sorted(pontos)


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


def importar_historico(ini_iso: str, fim_iso: str, forcar: bool = False) -> int:
    """
    Baixa curvas TaxaSwap para todos os dias uteis entre ini_iso e fim_iso.
    Retorna numero de datas novas adicionadas a _curva_di.csv.
    """
    ini = datetime.date.fromisoformat(ini_iso)
    fim = datetime.date.fromisoformat(fim_iso)
    dias = _dias_uteis(ini, fim)

    curvas = {} if forcar else _ler_curva_csv()
    pendentes = [d for d in dias if d.isoformat() not in curvas or forcar]

    print(f"TaxaSwap B3 historico: {ini_iso} -> {fim_iso}")
    print(f"  {len(dias)} dias uteis, {len(pendentes)} a baixar, {len(dias)-len(pendentes)} ja existem")

    novas = 0
    erros = 0

    for i, d in enumerate(pendentes, 1):
        data_iso = d.isoformat()
        raw = _baixar_taxaswap(data_iso)
        if raw is None:
            erros += 1
            if i <= 5 or i % 50 == 0:
                print(f"  [{i}/{len(pendentes)}] {data_iso}: sem arquivo (feriado ou nao-pregao)")
            time.sleep(DELAY)
            continue

        txt = _extrair_taxaswap_txt(raw)
        if txt is None:
            erros += 1
            print(f"  [{i}/{len(pendentes)}] {data_iso}: falha ao extrair TaxaSwap.txt")
            time.sleep(DELAY)
            continue

        pts = _parsear_curva_pre(txt)
        if pts:
            curvas[data_iso] = pts
            novas += 1
            if novas % 20 == 1 or i == len(pendentes):
                print(f"  [{i}/{len(pendentes)}] {data_iso}: {len(pts)} vertices PRE ok "
                      f"(novas={novas}, erros={erros})")
        else:
            erros += 1
            print(f"  [{i}/{len(pendentes)}] {data_iso}: zero vertices PRE no arquivo")

        time.sleep(DELAY)

    if novas:
        _gravar_curva_csv(curvas)
        print(f"\nSalvo: {CURVA_CSV}")
        print(f"Total: {len(curvas)} datas no arquivo, {novas} adicionadas agora, {erros} erros/ausencias.")
    else:
        print(f"\nNada novo a salvar. Erros/ausencias: {erros}")
    return novas


if __name__ == "__main__":
    args = sys.argv[1:]
    non_flags = [a for a in args if not a.startswith("--")]
    if len(non_flags) < 2:
        print("Uso: python scripts/importar_curva_historica.py INI FIM [--forcar]")
        print("  INI, FIM: datas no formato YYYY-MM-DD")
        print("  --forcar: rebaixa mesmo datas ja existentes")
        print("Exemplo: python scripts/importar_curva_historica.py 2020-01-01 2025-12-31")
        sys.exit(1)
    importar_historico(non_flags[0], non_flags[1], forcar="--forcar" in args)
