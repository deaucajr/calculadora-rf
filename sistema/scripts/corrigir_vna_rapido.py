#!/usr/bin/env python
"""
Corrige RAPIDO (sem API) CSVs IPCA com VNA=1.0.
So recalcula o VNA via IPCA do BACEN localmente.
Os valores de TAI/AMORT ja estao corretos (FC% data-independente).

Uso:
  python corrigir_vna_rapido.py             # corrige todos
  python corrigir_vna_rapido.py --dry-run   # lista quantos
  python corrigir_vna_rapido.py 22A0253223  # ticker especifico
"""
import re
import sys
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.paths import fluxos_dir, fluxos_antigo_dir
from src.vna_calc import get_ipca_index
from src.fmt_br import SEP, fmt, fmt_pct, parse_br


def _ler_header(linhas: list[str]) -> dict:
    """Extrai chave;valor das linhas META do CSV."""
    h = {}
    for ln in linhas:
        ln = ln.strip()
        if not ln or ln.startswith("DATA;") or ln.startswith("CDI;"):
            break
        p = ln.split(SEP)
        if len(p) >= 2:
            h[p[0].strip().lower()] = p[1].strip()
    return h


def corrigir(path: Path, dry_run: bool = False) -> str:
    """Recalcula VNA e atualiza o CSV (sem alterar TAI/AMORT)."""
    try:
        raw = path.read_text(encoding="utf-8")
        linhas = raw.splitlines()
        hdr = _ler_header(linhas)

        # So IPCA com VNA=1.0
        if "ipca" not in hdr.get("indexador", "").lower():
            return "skip:nao_ipca"
        vna_antigo = parse_br(hdr.get("vna", "1,0"))
        if vna_antigo > 1.01:
            return "skip:vna_ok"

        # Dados para calculo
        vne = parse_br(hdr.get("vne", "1000,0"))
        inicio = hdr.get("inicio_rentabilidade", "2020-01-01")
        data_ref = hdr.get("data_fluxo", datetime.now().strftime("%Y-%m-%d"))

        # Calcular VNA localmente
        vna_factor = get_ipca_index(inicio, data_ref)
        vna_novo = vne * vna_factor

        if vna_novo <= 1.0:
            return "erro:vna_nao_calculado"

        if dry_run:
            return "ok"

        # Backup
        bk_dir = fluxos_antigo_dir(criar=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(path, bk_dir / f"{path.stem}_vna1_{ts}.csv")

        # Atualizar linhas: so troca vna e adiciona vna_factor
        novas = []
        tem_vna_factor = False
        for ln in linhas:
            ln = ln.strip()
            if not ln:
                novas.append("")
                continue
            p = ln.split(SEP)
            if len(p) >= 2:
                k = p[0].lower()
                if k == "vna":
                    novas.append(f"vna{SEP}{fmt(vna_novo)}")
                    continue
                if k == "vna_factor":
                    tem_vna_factor = True
                    novas.append(f"vna_factor{SEP}{fmt_pct(vna_factor, 6)}")
                    continue
            novas.append(ln)

        # Adiciona vna_factor se nao existia
        if not tem_vna_factor:
            # Insere depois da linha do vna
            for i, ln in enumerate(novas):
                if ln.startswith(f"vna{SEP}"):
                    novas.insert(i + 1, f"vna_factor{SEP}{fmt_pct(vna_factor, 6)}")
                    break

        bom = "﻿" if raw.startswith("﻿") else ""
        path.write_text(bom + "\n".join(novas), encoding="utf-8")
        return "ok"

    except Exception as e:
        return f"erro:{e}"


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

    ok = skip = err = 0
    for i, path in enumerate(csvs):
        if path.name.startswith("_"):
            continue
        r = corrigir(path, dry_run)
        if r == "ok":
            ok += 1
        elif r.startswith("skip"):
            skip += 1
        else:
            err += 1
            if err <= 5:
                print(f"  [ERRO] {path.name}: {r}", flush=True)
        if (i + 1) % 500 == 0:
            print(f"  ... {i+1} processados (ok={ok} skip={skip}) ...", flush=True)

    acao = "SERIAM corrigidos" if dry_run else "corrigidos"
    print(f"\n{acao}: {ok} | pulados: {skip} | erros: {err}" +
          (" (DRY RUN)" if dry_run else ""), flush=True)


if __name__ == "__main__":
    main()
