#!/usr/bin/env python
"""
Gera data/fluxos/_ipca.csv = fator diario do IPCA (numero-indice com pro-rata por
dias uteis, convencao aniversario dia 15), do BACEN (serie 433, ja no rf.db) +
projecao p/ os meses futuros. O add-in usa esse fator para calcular a VNA dos
ativos IPCA+ em QUALQUER data (passada/futura), ancorando no ultimo ponto gravado:
    VNA(data) = VNA_ancora * fator(data) / fator(data_ancora)

Assim, atualizar so o IPCA (publico) mantem a VNA correta para datas longe tambem.
Formato: data_iso <TAB> fator
"""
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from src.paths import fluxos_dir
import validar_curva as V          # bdays() com o mesmo calendario do add-in


def _addm(y, m, n):
    t = m - 1 + n
    return y + t // 12, t % 12 + 1


def gerar_ipca_csv(anos_futuro: int = 2) -> Path:
    con = sqlite3.connect(str(ROOT / "data" / "rf.db"))
    rows = con.execute("SELECT substr(date,1,7), rate_pct FROM ipca_monthly ORDER BY date").fetchall()
    con.close()
    if not rows:
        raise RuntimeError("rf.db sem ipca_monthly — rode atualizar_ipca primeiro")
    NI, acc = {}, 1.0
    for ym, r in rows:
        acc *= (1 + r / 100)
        NI[ym] = acc
    ult_var = NI[rows[-1][0]] / NI[rows[-2][0]]    # ultima variacao p/ projetar meses futuros

    # estende o numero-indice p/ os meses FUTUROS com a projecao ANBIMA (ou ult. variacao)
    con2 = sqlite3.connect(str(ROOT / "data" / "rf.db"))
    try:
        proj = dict(con2.execute("SELECT month, rate_pct FROM ipca_projections").fetchall())
    except Exception:
        proj = {}
    con2.close()
    uy, um = int(rows[-1][0][:4]), int(rows[-1][0][5:7])
    fim_proj = date.today().year + anos_futuro + 1
    while (uy, um) < (fim_proj, 12):
        uy, um = _addm(uy, um, 1)
        ym = f"{uy:04d}-{um:02d}"
        taxa = proj.get(ym)
        acc *= (1 + taxa / 100) if taxa is not None else ult_var
        NI[ym] = acc

    def fator(d: date):
        ay, am = (d.year, d.month) if d.day >= 15 else _addm(d.year, d.month, -1)
        a1 = date(ay, am, 15)
        a2y, a2m = _addm(ay, am, 1)
        a2 = date(a2y, a2m, 15)
        ry, rm = _addm(ay, am, -1)
        base = NI.get(f"{ry:04d}-{rm:02d}")
        if base is None:
            return None
        nxt = NI.get(f"{ay:04d}-{am:02d}")
        if nxt is None:                            # mes ainda nao divulgado -> projeta
            nxt = base * ult_var
        duT = V.bdays(a1, a2)
        duD = V.bdays(a1, d)
        return base * (nxt / base) ** (duD / duT) if duT > 0 else base

    ini_ano = int(rows[0][0][:4]) + 1              # comeca 1 ano apos o 1o IPCA (base estavel)
    d = date(ini_ano, 1, 1)
    fim = date.today().year + anos_futuro
    linhas = []
    while d.year <= fim:
        f = fator(d)
        if f is not None:
            linhas.append(f"{d.isoformat()}\t{f:.10f}")
        d += timedelta(days=1)
    destino = fluxos_dir() / "_ipca.csv"
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"_ipca.csv: {len(linhas)} dias ({linhas[0].split(chr(9))[0]} a {linhas[-1].split(chr(9))[0]})")
    return destino


if __name__ == "__main__":
    gerar_ipca_csv()
