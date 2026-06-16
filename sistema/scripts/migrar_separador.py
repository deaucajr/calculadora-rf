#!/usr/bin/env python
"""
Converte TODOS os CSVs de fluxos do separador TAB (legado) para ; (Excel brasileiro).

Uso:
  python migrar_separador.py             # converte todos os CSVs (backup em fluxos_antigo/)
  python migrar_separador.py --dry-run   # mostra o que seria convertido (sem alterar)
  python migrar_separador.py EGIEA6.csv  # converte um arquivo especifico

O script:
  1. Detecta o separador atual do arquivo (TAB ou ;)
  2. Se for TAB, converte para ;
  3. Backup do original vai para fluxos_antigo/ com timestamp
  4. Se ja for ;, pula
"""
import sys
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.paths import fluxos_dir, fluxos_antigo_dir

SEP_NOVO = ";"
SEP_ANTIGO = "\t"


def detectar_sep(linhas: list[str]) -> str:
    """Detecta se o arquivo usa TAB ou ; como separador."""
    tabs = sum(ln.count("\t") for ln in linhas[:20])
    ponto_virg = sum(ln.count(";") for ln in linhas[:20])
    return "\t" if tabs >= ponto_virg else ";"


def converter_arquivo(path: Path, dry_run: bool = False) -> str:
    """Converte um arquivo de TAB para ;. Retorna: 'ok', 'skip', 'erro'."""
    try:
        conteudo = path.read_text(encoding="utf-8")
        linhas = conteudo.splitlines()

        if not linhas:
            return "skip"

        sep_atual = detectar_sep(linhas)

        if sep_atual == SEP_NOVO:
            return "skip"  # ja esta no formato novo

        # Converter: substitui TAB por ;
        novas_linhas = [ln.replace("\t", SEP_NOVO) for ln in linhas]
        novo_conteudo = "\n".join(novas_linhas)

        if dry_run:
            return "ok"

        # Backup
        backup_dir = fluxos_antigo_dir(criar=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{path.stem}_{ts}.csv"
        shutil.copy2(path, backup_path)

        # Escrever novo formato
        path.write_text(novo_conteudo, encoding="utf-8")
        return "ok"

    except Exception as e:
        return f"erro: {e}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv

    fluxos = fluxos_dir(criar=True)
    csvs = sorted(fluxos.glob("*.csv"))

    if args:
        # Arquivo especifico
        alvo = fluxos / args[0]
        if not alvo.exists():
            print(f"Arquivo nao encontrado: {alvo}")
            return
        csvs = [alvo]

    ok, skip, err = 0, 0, 0
    for path in csvs:
        nome = path.name
        if nome.startswith("_"):
            continue  # pula arquivos de sistema
        r = converter_arquivo(path, dry_run)
        if r == "ok":
            ok += 1
        elif r == "skip":
            skip += 1
        else:
            err += 1
            print(f"  [ERRO] {nome}: {r}")

    acao = "SERIAM convertidos" if dry_run else "convertidos"
    print(f"\n{acao}: {ok} | pulados: {skip} | erros: {err}" +
          (" (DRY RUN — nada alterado)" if dry_run else ""))

    if dry_run and ok > 0:
        print("\nExecute sem --dry-run para converter.")


if __name__ == "__main__":
    main()
