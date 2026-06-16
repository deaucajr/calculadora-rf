#!/usr/bin/env python
"""
Converte ponto decimal (.) para virgula (,) em todos os CSVs de fluxo.
Padrao brasileiro: separador de colunas = ;  decimal = ,

So converte campos NUMERICOS (ex: 1448,562894). Datas e texto ficam intactos.

Uso:
  python migrar_decimal_br.py             # converte todos os CSVs
  python migrar_decimal_br.py --dry-run   # mostra o que seria convertido
  python migrar_decimal_br.py EGIEA6.csv  # converte um arquivo especifico
"""
import re
import sys
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.paths import fluxos_dir, fluxos_antigo_dir

# Regex: captura digitos . digitos (decimal com ponto)
# Ex: "1448.562894" -> "1448,562894"
# Nao pega datas (YYYY-MM-DD) pois o padrao eh digito seguido de ponto seguido de digito
RE_DECIMAL = re.compile(r'(\d)\.(\d)')


def _substituir_ponto_por_virgula(linha: str) -> str:
    """Substitui . por , apenas em campos numericos."""
    # Divide a linha por ; (separador de colunas)
    partes = linha.split(";")
    novas = []
    for p in partes:
        p_strip = p.strip()
        # Verifica se parece numero (contem digitos e possivelmente um . decimal)
        if re.search(r'\d\.\d', p_strip):
            # Campo numerico: troca ponto por virgula
            p = RE_DECIMAL.sub(r'\1,\2', p)
        # Se for so texto ou data, mantem igual
        novas.append(p)
    return ";".join(novas)


def converter_arquivo(path: Path, dry_run: bool = False) -> str:
    """Converte decimais de . para , num arquivo CSV. Retorna: 'ok', 'skip', 'erro'."""
    try:
        conteudo = path.read_text(encoding="utf-8")
        linhas = conteudo.splitlines()

        if not linhas:
            return "skip"

        # Detecta se ja esta no padrao brasileiro (nao tem . decimal nos numeros)
        tem_ponto_decimal = False
        for ln in linhas[:20]:
            if re.search(r'\d\.\d', ln) and not re.search(r'\d{4}-\d{2}-\d{2}', ln):
                # Tem digito.digito que nao eh data
                partes = ln.split(";")
                for p in partes:
                    if re.match(r'^-?\d+\.\d+$', p.strip()):
                        tem_ponto_decimal = True
                        break
            if tem_ponto_decimal:
                break

        if not tem_ponto_decimal:
            return "skip"  # ja esta com virgula

        if dry_run:
            return "ok"

        # Converter
        novas_linhas = [_substituir_ponto_por_virgula(ln) for ln in linhas]
        novo_conteudo = "\n".join(novas_linhas)

        # Backup
        backup_dir = fluxos_antigo_dir(criar=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{path.stem}_dot_{ts}.csv"
        shutil.copy2(path, backup_path)

        # Escrever novo formato
        # Preservar BOM se existir
        bom = ""
        if conteudo.startswith("﻿"):
            bom = "﻿"

        path.write_text(bom + novo_conteudo, encoding="utf-8")
        return "ok"

    except Exception as e:
        return f"erro: {e}"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv

    fluxos = fluxos_dir(criar=True)
    csvs = sorted(fluxos.glob("*.csv"))

    if args:
        alvo = fluxos / args[0]
        if not alvo.exists():
            print(f"Arquivo nao encontrado: {alvo}")
            return
        csvs = [alvo]

    ok, skip, err = 0, 0, 0
    for path in csvs:
        nome = path.name
        if nome.startswith("_"):
            continue
        r = converter_arquivo(path, dry_run)
        if r == "ok":
            ok += 1
        elif r == "skip":
            skip += 1
        else:
            err += 1
            print(f"  [ERRO] {nome}: {r}")
        if ok % 500 == 0 and ok > 0:
            print(f"  ... {ok} convertidos, {skip} pulados ...")

    acao = "SERIAM convertidos" if dry_run else "convertidos"
    print(f"\n{acao}: {ok} | pulados: {skip} | erros: {err}" +
          (" (DRY RUN)" if dry_run else ""))

    if dry_run and ok > 0:
        print("Execute sem --dry-run para converter.")


if __name__ == "__main__":
    main()
