#!/usr/bin/env python
"""
Gera o e-mail-resumo da calculadora (sem precisar de Outlook):
  - total de ativos hoje
  - automaticos (B3) x inseridos manualmente
  - novos adicionados no dia (vs o ultimo snapshot)
  - atualizados no dia (DATA_FLUXO = ultimo pregao)
  - arquivados como 'antigo'

Salva data/email_resumo.html e .txt e abre o HTML p/ voce copiar e colar no webmail.

  python gerar_email.py
"""
import datetime
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.paths import fluxos_dir, fluxos_manual_dir, fluxos_antigo_dir
from importar_todos import ultimo_dia_util


def _tickers(pasta: Path) -> set[str]:
    return {f.stem.upper() for f in pasta.glob("*.csv") if not f.name.startswith("_")}


def _data_fluxo(csv: Path) -> str | None:
    try:
        for ln in csv.read_text(encoding="utf-8").splitlines()[:15]:
            c = ln.split("\t")
            if c[0] == "META" and len(c) >= 3 and c[1] == "DATA_FLUXO":
                return c[2].strip()
    except Exception:
        pass
    return None


def gerar():
    auto, man, ant = fluxos_dir(), fluxos_manual_dir(), fluxos_antigo_dir()
    t_auto, t_man, t_ant = _tickers(auto), _tickers(man), _tickers(ant)
    total = t_auto | t_man
    ref = ultimo_dia_util()
    atualizados = sum(1 for f in auto.glob("*.csv")
                      if not f.name.startswith("_") and _data_fluxo(f) == ref)

    # novos no dia: diferenca vs o ultimo snapshot
    snap = ROOT / "data" / "_email_snapshot.json"
    prev = None
    if snap.exists():
        try:
            prev = set(json.loads(snap.read_text(encoding="utf-8")).get("tickers", []))
        except Exception:
            prev = None
    if prev is None:
        novos_txt = "(baseline — primeiro resumo)"
    else:
        novos = sorted(total - prev)
        ex = ", ".join(novos[:10]) + ("..." if len(novos) > 10 else "")
        novos_txt = f"{len(novos)}" + (f" ({ex})" if novos else "")
    snap.write_text(json.dumps({"date": datetime.date.today().isoformat(),
                                "tickers": sorted(total)}), encoding="utf-8")

    hoje = datetime.date.today().strftime("%d/%m/%Y")
    itens = [
        ("Total de ativos na calculadora", str(len(total))),
        ("&nbsp;&nbsp;• Automáticos (B3)", str(len(t_auto))),
        ("&nbsp;&nbsp;• Inseridos manualmente", str(len(t_man))),
        ("Novos adicionados hoje", novos_txt),
        (f"Atualizados (pregão {ref})", str(atualizados)),
        ("Arquivados como antigos", str(len(t_ant))),
    ]
    assunto = f"Resumo Renda Fixa - {hoje}"
    txt = assunto + "\n\n" + "\n".join(f"{k.replace('&nbsp;',' ').replace('•','-')}: {v}"
                                       for k, v in itens) + "\n"
    linhas_html = "".join(f"<tr><td>{k}</td><td style='text-align:right'><b>{v}</b></td></tr>"
                          for k, v in itens)
    html = (f"<html><head><meta charset='utf-8'></head><body style='font-family:Segoe UI,Arial'>"
            f"<h3>{assunto}</h3><table cellpadding='4' style='border-collapse:collapse'>"
            f"{linhas_html}</table></body></html>")

    (ROOT / "data" / "email_resumo.txt").write_text(txt, encoding="utf-8")
    (ROOT / "data" / "email_resumo.html").write_text(html, encoding="utf-8")
    print(txt)
    print(f"Assunto: {assunto}")
    print(f"\nArquivos gerados:\n  {ROOT/'data'/'email_resumo.txt'}\n  {ROOT/'data'/'email_resumo.html'}")
    try:
        os.startfile(str(ROOT / "data" / "email_resumo.html"))   # abre p/ copiar (Windows)
    except Exception:
        pass


if __name__ == "__main__":
    gerar()
