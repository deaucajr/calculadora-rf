#!/usr/bin/env python
"""
Migra CSVs de fluxo do formato legado (META/FLUXO/VNA/FLUXOD/AMORTPCT)
para o formato novo (chave-valor simples + tabela DATA/FLUXO_TAI/TIPO).

Uso:
  python migrar_csvs.py             # migra todos os CSVs em data/fluxos/
  python migrar_csvs.py EGIEA6.csv  # migra um arquivo especifico
  python migrar_csvs.py --dry-run   # mostra o que seria migrado (sem alterar)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.paths import fluxos_dir

SEP = ";"


def _eh_legado(linhas: list[str]) -> bool:
    """Retorna True se o CSV precisa de conversao (formato antigo ou intermediario)."""
    for ln in linhas:
        ln = ln.rstrip()
        if ln.startswith("META\t") or ln.startswith("FLUXO\t"):
            return True          # formato original com prefixo META/FLUXO
        if ln == "DATA\tFLUXO_TAI\tTIPO":
            return True          # formato intermediario (coluna TIPO)
        if ln == "DATA\tJUROS_TAI\tAMORT_TAI":
            return False         # ja no formato final
    return False


def _converter(linhas: list[str]) -> list[str] | None:
    """Converte linhas do formato legado para o novo. Retorna None se ja eh novo."""
    if not _eh_legado(linhas):
        return None

    meta: dict[str, str] = {}
    fluxos: list[tuple[str, str, float, int]] = {}  # date -> {tipos, vf, du}
    vna_pts: dict[str, float] = {}
    cdi_blocos: dict[str, list[str]] = {}
    amort: list[tuple[str, float]] = []

    from collections import defaultdict
    grupos: dict = defaultdict(lambda: {"juros": 0.0, "amort": 0.0})

    for ln in linhas:
        ln = ln.rstrip()
        if not ln:
            continue
        p = ln.split(SEP)
        tag = p[0]
        if tag == "META" and len(p) >= 3:
            meta[p[1].upper()] = p[2]
        elif tag == "FLUXO" and len(p) >= 7:
            # formato original: FLUXO date tipo vf pv du fc_pct
            d, ev, vf = p[1], p[2], float(p[3])
            if ev == "A":
                grupos[d]["amort"] += vf
            else:
                grupos[d]["juros"] += vf
        elif tag == "VNA" and len(p) >= 3:
            vna_pts[p[1]] = float(p[2])
        elif tag == "FLUXOD" and len(p) >= 7:
            dc = p[1]
            cdi_blocos.setdefault(dc, []).append(
                SEP.join(["CDI", p[1], p[2], p[4], p[5], p[6]])
            )
        elif tag == "AMORTPCT" and len(p) >= 3:
            amort.append((p[1], float(p[2])))
        elif tag == "DATA":
            pass  # cabecalho da tabela, ignora
        elif len(tag) == 10 and tag[4] == "-" and tag[7] == "-":
            if len(p) >= 3:
                d = p[0]
                try:
                    # novo formato JUROS_TAI/AMORT_TAI: 3a coluna e numerica
                    juros_tai = float(p[1])
                    amort_tai = float(p[2])
                    grupos[d]["juros"] += juros_tai
                    grupos[d]["amort"] += amort_tai
                    vna_pts.setdefault("_tai", 1.0)
                except ValueError:
                    # formato intermediario: date\tFLUXO_TAI\tTIPO (3a col e string)
                    fc_pct, tipo_str = float(p[1]), p[2]
                    if tipo_str == "A":
                        grupos[d]["amort"] += fc_pct
                    elif tipo_str == "J+A":
                        # split perdido: total vai para juros (correto p/ calculo PU)
                        grupos[d]["juros"] += fc_pct
                    else:
                        grupos[d]["juros"] += fc_pct
                    vna_pts.setdefault("_tai", 1.0)
        elif tag not in ("CDI", "AMORT", ""):
            # formato chave-valor novo: ticker, tipo, indexador, vna, ...
            if len(p) == 2:
                meta[p[0].upper().replace("INICIO_RENTABILIDADE", "INICIO_RENT")] = p[1]
                if p[0].lower() == "vna":
                    vna_pts["_header"] = float(p[1])

    indexador = meta.get("INDEXADOR", "PRE")
    ticker = meta.get("TICKER", "")
    tipo_ativo = meta.get("TIPO", "DEB")
    emissor = meta.get("EMISSOR", "")
    method = meta.get("METHOD", "")
    inicio = meta.get("INICIO_RENT", "")
    vencimento = meta.get("VENCIMENTO", "")
    vne = meta.get("VNE", "")
    taxa_emissao = meta.get("TAXA_EMISSAO", "")
    taxa_ref = meta.get("TAXA_REF", "")
    data_fluxo = meta.get("DATA_FLUXO", "")
    fonte = meta.get("FONTE", "B3")

    out = [
        SEP.join(["ticker", ticker]),
        SEP.join(["tipo", tipo_ativo]),
        SEP.join(["indexador", indexador]),
        SEP.join(["emissor", emissor]),
        SEP.join(["method", method]),
        SEP.join(["inicio_rentabilidade", inicio]),
        SEP.join(["vencimento", vencimento]),
        SEP.join(["vne", vne]),
        SEP.join(["taxa_emissao", taxa_emissao]),
        SEP.join(["taxa_ref", taxa_ref]),
        SEP.join(["data_fluxo", data_fluxo]),
        SEP.join(["fonte", fonte]),
        "",
    ]

    if cdi_blocos:
        for d in sorted(cdi_blocos):
            out.extend(cdi_blocos[d])
    else:
        # IPCA/PRE: recupera VNA mais recente
        # _header: vna do cabecalho chave-valor (formato intermediario)
        # _tai: flag de que valores ja sao TAI (nao precisa dividir por VNA)
        # chaves ISO: pontos VNA por data (formato original)
        vna_mais_recente = 0.0
        if "_header" in vna_pts:
            vna_mais_recente = vna_pts["_header"]
        elif vna_pts:
            datas_iso = [k for k in vna_pts if not k.startswith("_")]
            if data_fluxo in vna_pts:
                vna_mais_recente = vna_pts[data_fluxo]
            elif datas_iso:
                vna_mais_recente = vna_pts[sorted(datas_iso)[-1]]

        # insere vna no cabecalho (antes da linha em branco)
        out.insert(-1, SEP.join(["vna", f"{vna_mais_recente:.6f}"]))

        out.append(SEP.join(["DATA", "JUROS_TAI", "AMORT_TAI"]))
        tai_mode = "_tai" in vna_pts  # valores ja sao fracao do VNA
        divisor = 1.0 if tai_mode else (vna_mais_recente if vna_mais_recente > 0 else 1.0)
        for d in sorted(grupos):
            g = grupos[d]
            juros_pct = g["juros"] / divisor
            amort_pct = g["amort"] / divisor
            out.append(SEP.join([d, f"{juros_pct:.10f}", f"{amort_pct:.10f}"]))

        if amort:
            out.append("")
            for d_iso, pct in sorted(amort):
                out.append(SEP.join(["AMORT", d_iso, f"{pct:.8f}"]))

    return out


def migrar_arquivo(path: Path, dry_run: bool = False) -> str:
    linhas = path.read_text(encoding="utf-8").splitlines()
    novo = _converter(linhas)
    if novo is None:
        return f"PULAR  {path.name} (ja no formato novo)"
    if dry_run:
        return f"MIGRAR {path.name} ({len(linhas)} -> {len(novo)} linhas) [dry-run]"
    path.write_text("\n".join(novo), encoding="utf-8")
    return f"OK     {path.name} ({len(linhas)} -> {len(novo)} linhas)"


def main():
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        paths = []
        fd = fluxos_dir()
        for a in args:
            p = Path(a) if Path(a).is_absolute() else fd / a
            if p.exists():
                paths.append(p)
            else:
                print(f"NAO ENCONTRADO: {a}")
    else:
        fd = fluxos_dir()
        paths = sorted(fd.glob("*.csv"))
        # exclui arquivos especiais
        paths = [p for p in paths if not p.name.startswith("_")]

    print(f"{'[DRY-RUN] ' if dry_run else ''}Migrando {len(paths)} CSV(s)...")
    ok = skip = erro = 0
    for path in paths:
        try:
            msg = migrar_arquivo(path, dry_run)
            print(f"  {msg}")
            if msg.startswith("OK"):
                ok += 1
            else:
                skip += 1
        except Exception as e:
            print(f"  ERRO   {path.name}: {e}")
            erro += 1

    print(f"\nTotal: {ok} migrado(s), {skip} pulado(s), {erro} erro(s).")
    if dry_run:
        print("Rode sem --dry-run para aplicar as mudancas.")


if __name__ == "__main__":
    main()
