#!/usr/bin/env python
"""
Conserta CSVs mal classificados SEM chamar a API.

Bug: na massa, o INDEXADOR veio do getbonddetails.method (indice de correcao),
mas a metodologia real e' o calcPU.method. Papeis DI-SPREAD/DI-PERC cujo
getbonddetails dizia "IPCA" foram salvos como IPCA (formato FLUXO+VNA), errado.

Deteccao local (sem API): para IPCA verdadeiro, Sum PV == Sum VF/(1+taxa)^(du/252).
Para CDI (DI-SPREAD/PERC) o PV embute o desconto CDI -> diverge muito. Nesses casos
reescrevemos no formato CDI (FLUXOD) usando os PV/DU ja salvos.

Uso: python corrigir_csvs.py [--dry]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLUXOS_DIR = ROOT / "data" / "fluxos"
SEP = "\t"
TOL_REL = 0.005   # 0,5%: separa IPCA (==0) de CDI (>>)


def processar(path: Path, dry: bool) -> str:
    linhas = path.read_text(encoding="utf-8").splitlines()
    meta, fluxo, vna = {}, [], []
    for ln in linhas:
        p = ln.split(SEP)
        if p[0] == "META" and len(p) >= 3:
            meta[p[1]] = p[2]
        elif p[0] == "FLUXO" and len(p) >= 7:
            fluxo.append(p)
        elif p[0] == "VNA":
            vna.append(p)
    if meta.get("INDEXADOR") != "IPCA" or not fluxo:
        return "skip"

    taxa = float(meta.get("TAXA_REF", 0) or 0)
    spv = sum(float(p[4]) for p in fluxo)
    svf_disc = sum(float(p[3]) / (1 + taxa / 100) ** (int(p[5]) / 252) for p in fluxo)
    if spv <= 0:
        return "skip"
    dif_rel = abs(spv - svf_disc) / spv
    if dif_rel <= TOL_REL:
        return "ipca-ok"   # IPCA verdadeiro

    # E' CDI mal classificado -> reescreve no formato FLUXOD
    if dry:
        return f"CDI (dif_rel={dif_rel:.3f})"
    dc = meta.get("DATA_FLUXO", "")
    out = []
    for k, v in meta.items():
        if k == "INDEXADOR":
            v = "CDI"
        if k == "METHOD":
            v = "DI-SPREAD?"  # reclassificado localmente; modelo CDI vale p/ SPREAD e PERC
        out.append(SEP.join(["META", k, v]))
    for p in fluxo:  # FLUXO: data,evento,vf,pv,du,fc%  ->  FLUXOD: data_calc,data_ev,evento,vf,pv,du
        out.append(SEP.join(["FLUXOD", dc, p[1], p[2], p[3], p[4], p[5]]))
    path.write_text("\n".join(out), encoding="utf-8")
    return f"corrigido CDI (dif_rel={dif_rel:.3f})"


def main(dry: bool):
    arquivos = [f for f in FLUXOS_DIR.glob("*.csv") if not f.name.startswith("_")]
    cont = {"ipca-ok": 0, "corrigido": 0, "skip": 0}
    exemplos = []
    for f in arquivos:
        r = processar(f, dry)
        if r.startswith("corrigido") or r.startswith("CDI"):
            cont["corrigido"] += 1
            if len(exemplos) < 8:
                exemplos.append(f"{f.stem}: {r}")
        elif r == "ipca-ok":
            cont["ipca-ok"] += 1
        else:
            cont["skip"] += 1
    print(f"{'[DRY] ' if dry else ''}Total: {len(arquivos)} CSVs")
    print(f"  IPCA verdadeiro : {cont['ipca-ok']}")
    print(f"  CDI reclassificado: {cont['corrigido']}")
    print(f"  skip (ja CDI/PRE): {cont['skip']}")
    print("Exemplos reclassificados:")
    for e in exemplos:
        print("  ", e)


if __name__ == "__main__":
    main("--dry" in sys.argv)
