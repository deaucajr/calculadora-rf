#!/usr/bin/env python
"""
Corrige CSVs com VNA=1.0 (quebrado) recalculando VNA localmente via IPCA do BACEN.

Uso:
  python corrigir_vna.py              # corrige todos os ativos IPCA com VNA=1.0
  python corrigir_vna.py --dry-run    # lista quantos seriam corrigidos
  python corrigir_vna.py 22A0253223   # corrige um ticker especifico
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


def _ler_cabecalho(linhas: list[str]) -> dict:
    """Le chave;valor do cabecalho do CSV."""
    hdr = {}
    for ln in linhas:
        ln = ln.strip()
        if not ln or ln.startswith("DATA;"):
            break
        partes = ln.split(SEP)
        if len(partes) >= 2:
            hdr[partes[0].strip().lower()] = partes[1].strip()
    return hdr


def corrigir_csv(path: Path, dry_run: bool = False) -> str:
    """Recalcula VNA e TAI/AMORT para um CSV IPCA com VNA=1.0."""
    try:
        conteudo = path.read_text(encoding="utf-8")
        linhas = conteudo.splitlines()
        hdr = _ler_cabecalho(linhas)

        # So processa IPCA com VNA=1.0
        idx = hdr.get("indexador", "").upper()
        vna_str = hdr.get("vna", "1,0")
        vna_atual = parse_br(vna_str) if vna_str else 1.0

        if "IPCA" not in idx:
            return "skip:nao_ipca"
        if vna_atual > 1.01:
            return "skip:vna_ok"

        # Dados necessarios
        vne = parse_br(hdr.get("vne", "1000,0"))
        inicio = hdr.get("inicio_rentabilidade", "2020-01-01")
        data_fluxo = hdr.get("data_fluxo", datetime.now().strftime("%Y-%m-%d"))

        # Calcular VNA local
        vna_factor = get_ipca_index(inicio, data_fluxo)
        vna_novo = vne * vna_factor

        if vna_novo <= 1.0:
            return "erro:vna_nao_calculado"

        if dry_run:
            return "ok"

        # Backup
        backup_dir = fluxos_antigo_dir(criar=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(path, backup_dir / f"{path.stem}_vna1_{ts}.csv")

        # Reconstruir CSV com VNA corrigido e TAI/AMORT recalculados
        novas = []
        in_fluxos = False

        for ln in linhas:
            ln = ln.strip()
            if not ln:
                novas.append("")
                continue

            partes = ln.split(SEP)

            # Substitui VNA no cabecalho
            if len(partes) >= 2 and partes[0].lower() == "vna":
                novas.append(f"vna{SEP}{fmt(vna_novo)}")
                continue
            if len(partes) >= 2 and partes[0].lower() == "vna_factor":
                novas.append(f"vna_factor{SEP}{fmt_pct(vna_factor, 6)}")
                continue

            # Detecta inicio da tabela de fluxos
            if ln.startswith("DATA;"):
                in_fluxos = True
                novas.append(ln)
                continue

            # Recalcula fluxos (DATA;JUROS_TAI;AMORT_TAI ou DATA;EVENTO;VF;PV;DU;TAI_PCT;AMORT_PCT)
            if in_fluxos and len(partes) >= 3:
                data_ev = partes[0]
                if len(data_ev) == 10 and data_ev[4] == "-":
                    # Formato antigo: DATA;JUROS_TAI;AMORT_TAI
                    if len(partes) == 3 and "JUROS" in linhas[0] if not dry_run else True:
                        # Tenta detectar formato pela linha de cabecalho anterior
                        juros_raw = parse_br(partes[1])
                        amort_raw = parse_br(partes[2])
                        # Os valores antigos sao FC% com VNA=1.0, ou seja, sao = VF em R$
                        # Precisamos recalcular: FC% = VF / VNA_novo
                        # Mas VF = valor_antigo * VNA_antigo(1.0) = valor_antigo
                        juros_novo = juros_raw / vna_novo
                        amort_novo = amort_raw / vna_novo
                        novas.append(f"{data_ev}{SEP}{fmt_pct(juros_novo)}{SEP}{fmt_pct(amort_novo)}")
                    # Formato novo: DATA;EVENTO;VF;PV;DU;TAI_PCT;AMORT_PCT
                    elif len(partes) >= 7:
                        ev = partes[1]
                        vf = parse_br(partes[2])
                        pv = parse_br(partes[3])
                        du = partes[4]
                        tai_antigo = parse_br(partes[5])
                        amort_antigo = parse_br(partes[6])
                        # Recalcular: TAI_PCT = VF_juros / VNA * 100
                        # Como nao temos separacao juros/amort no VF, usamos os % antigos
                        tai_novo = tai_antigo / vna_novo  # tira o fator do VNA antigo
                        amort_novo = amort_antigo / vna_novo
                        novas.append(f"{data_ev}{SEP}{ev}{SEP}{fmt(vf)}{SEP}{fmt(pv)}{SEP}{du}{SEP}{fmt_pct(tai_novo)}{SEP}{fmt_pct(amort_novo)}")
                    continue

            novas.append(ln)

        # Escrever
        bom = "﻿" if conteudo.startswith("﻿") else ""
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
    for path in csvs:
        if path.name.startswith("_"):
            continue
        r = corrigir_csv(path, dry_run)
        if r == "ok":
            ok += 1
        elif r.startswith("skip"):
            skip += 1
        else:
            err += 1
            if err <= 10:
                print(f"  [ERRO] {path.name}: {r}")
        if ok % 500 == 0 and ok > 0:
            print(f"  ... {ok} corrigidos ...")

    acao = "SERIAM corrigidos" if dry_run else "corrigidos"
    print(f"\n{acao}: {ok} | pulados: {skip} | erros: {err}" +
          (" (DRY RUN)" if dry_run else ""))


if __name__ == "__main__":
    main()
