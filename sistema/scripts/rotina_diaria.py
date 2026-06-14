#!/usr/bin/env python
"""
Rotina diaria: detecta ativos novos na B3, atualiza os existentes e mantem
os CSV de fluxo do dia. Pensada para o Agendador de Tarefas do Windows.

O que faz:
  1. Recarrega o universo (list deb/cri/cra) -> detecta novos ativos.
  2. Importa/atualiza todos para o ultimo dia util (resume: pula os ja feitos).
  3. Loga resumo em data/rotina_diaria.log.

Passos: CDI (BACEN) + curva DI x Pre (B3) publicos; ativos novos; e um RODIZIO
de deteccao de mudanca de fluxo (getbonddetails) que re-importa so o que mudou.

Modos:
  python rotina_diaria.py            -> LEVE (PADRAO): CDI+curva publicos + ativos
                                        novos + refresh mensal de IPCA (so quando
                                        sai IPCA novo) + rodizio de mudanca de
                                        fluxo. Poucas chamadas a API.
  python rotina_diaria.py --completo -> re-importa TODOS p/ hoje (pesado; raramente
                                        necessario, o add-in ja preca CDI por curva
                                        e IPCA/PRE independem da data alem da VNA)
  python rotina_diaria.py --agendar [--completo]  -> agenda no Windows (7h30, uteis)
"""
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
sys.path.insert(0, str(ROOT))


def agendar(completo=False):
    """Cria tarefa no Agendador do Windows: 7h30, seg-sex (leve por padrao)."""
    py = sys.executable
    script = str(BASE / "rotina_diaria.py")
    alvo = f'"{py}" "{script}"' + (" --completo" if completo else "")
    cmd = [
        "schtasks", "/Create", "/TN", "RF_RotinaDiaria", "/SC", "WEEKLY",
        "/D", "MON,TUE,WED,THU,FRI", "/ST", "07:30",
        "/TR", alvo, "/F", "/RL", "LIMITED",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout or r.stderr)


def atualizar_cdi():
    """Atualiza CDI do BACEN e reexporta fluxos/_cdi.csv (p/ DI-PERC no add-in)."""
    from src.sync_bacen import sync_cdi
    from src.db import get_conn
    from importar_todos import log
    try:
        sync_cdi(start="01/01/2026")
    except Exception as e:
        log(f"  sync_cdi: {e}")
    with get_conn() as c:
        rows = c.execute("SELECT date, rate_annual FROM cdi_daily ORDER BY date").fetchall()
    out = [f'{r["date"]}\t{float(r["rate_annual"]) / 100:.10f}' for r in rows]
    from src.paths import fluxos_dir
    (fluxos_dir() / "_cdi.csv").write_text("\n".join(out), encoding="utf-8")
    log(f"  _cdi.csv: {len(out)} dias (ultimo {rows[-1]['date']})")


def atualizar_curva_di():
    """Baixa a curva DI x Pre da B3 (ultimos pregoes) -> fluxos/_curva_di.csv."""
    from src.sync_b3_curve import sync_curva_di
    from importar_todos import log
    try:
        novas = sync_curva_di()
        log(f"  _curva_di.csv: {novas} datas novas")
    except Exception as e:
        log(f"  curva DI: {e}")


# quantos ativos checar por mudanca de fluxo a cada execucao (rodizio leve)
LOTE_MUDANCAS = 250


def verificar_mudancas_lote(atualizar=True):
    """Rodizio leve: checa LOTE_MUDANCAS ativos (getbonddetails) e re-importa
    so os que mudaram de fluxo. Poucas chamadas; cobre o universo em ~dias."""
    from importar_todos import log
    from verificar_mudancas import rodar
    try:
        res = rodar(max_lote=LOTE_MUDANCAS, atualizar=atualizar, log=lambda m: log(m))
        log(f"  mudancas de fluxo: {len(res['mudou'])} mudaram, "
            f"{res['novos']} baseline, {res['verificados']} verificados, "
            f"{res['restantes']} restantes no rodizio")
    except Exception as e:
        log(f"  verificar_mudancas: {e}")


def _novos_do_universo():
    """Refresh do universo e retorna o conjunto de tickers novos (por tipo)."""
    from importar_todos import carregar_universo, log
    import json
    antes = {}
    try:
        uni_path = ROOT / "data" / "universo.json"
        if uni_path.exists():
            antes = json.loads(uni_path.read_text(encoding="utf-8"))
    except Exception:
        pass
    uni = carregar_universo(refresh=True)
    novos = {}
    for t in ("deb", "cri", "cra"):
        n = sorted(set(uni.get(t, [])) - set(antes.get(t, [])))
        if n:
            novos[t] = n
            log(f"  novos {t}: {len(n)} -> {n[:10]}")
    return novos


IPCA_MARK = ROOT / "data" / "_ipca_refresh.txt"


def atualizar_ipca():
    """Sincroniza IPCA mensal (BACEN) + projecao ANBIMA -> rf.db."""
    from src.sync_bacen import sync_ipca, sync_anbima_ipca_projection
    from importar_todos import log
    try:
        sync_ipca(start="01/01/2020")
        sync_anbima_ipca_projection()
    except Exception as e:
        log(f"  IPCA sync: {e}")


def _ultimo_ipca_ref():
    """Mes de referencia (YYYY-MM-DD) do IPCA mais recente no rf.db."""
    from src.db import get_conn
    try:
        with get_conn() as c:
            r = c.execute("SELECT MAX(date) FROM ipca_monthly").fetchone()
        return r[0] if r and r[0] else None
    except Exception:
        return None


def _ativos_ipca():
    """Tickers locais cujo INDEXADOR = IPCA (le so o cabecalho META)."""
    from src.paths import fluxos_dir
    out = []
    for p in fluxos_dir().glob("*.csv"):
        if p.name.startswith("_"):
            continue
        try:
            for ln in p.read_text(encoding="utf-8").splitlines()[:15]:
                c = ln.split("\t")
                if c[0] == "META" and len(c) >= 3 and c[1] == "INDEXADOR":
                    if c[2].upper() == "IPCA":
                        out.append(p.stem.upper())
                    break
        except Exception:
            pass
    return out


def refresh_ipca_se_novo():
    """Se saiu IPCA novo (ref > ultima marca), re-importa os ativos IPCA para
    atualizar a VNA. Roda ~1x/mes — o que mantem o IPCA correto sem import diario."""
    from importar_todos import log, ultimo_dia_util
    from importar_fluxos import importar_ticker
    ref = _ultimo_ipca_ref()
    if not ref:
        return
    marca = IPCA_MARK.read_text(encoding="utf-8").strip() if IPCA_MARK.exists() else ""
    if ref <= marca:
        log(f"  IPCA sem mes novo (ref {ref}); VNA ja atualizada")
        return
    ativos = _ativos_ipca()
    data = ultimo_dia_util()
    log(f"  IPCA novo (ref {ref}): atualizando VNA de {len(ativos)} ativos IPCA...")
    ok = err = 0
    for tk in ativos:
        try:
            importar_ticker(tk, data)
            ok += 1
        except Exception as e:
            err += 1
            log(f"    {tk}: ERRO {e}")
        time.sleep(0.4)
    IPCA_MARK.write_text(ref, encoding="utf-8")
    log(f"  IPCA refresh: {ok} ok, {err} erro (marca={ref})")


def _marcar_ipca():
    """Marca o IPCA como ja refrescado (usado apos o import completo)."""
    ref = _ultimo_ipca_ref()
    if ref:
        IPCA_MARK.write_text(ref, encoding="utf-8")


def run(leve=True):
    """leve=True (padrao): dados publicos (CDI/curva) + ativos novos + refresh
    mensal de IPCA (so quando sai mes novo) + rodizio de mudanca de fluxo — poucas
    chamadas. leve=False: re-importa TODOS p/ hoje (pesado). Viavel ser leve pois
    o add-in preca CDI por curva e IPCA/PRE so dependem da VNA (refrescada no IPCA)."""
    from importar_todos import main as importar_main, log, ultimo_dia_util
    from importar_fluxos import importar_ticker
    log(f"=== ROTINA DIARIA{' (leve)' if leve else ' (completa)'} ===")
    atualizar_cdi()
    atualizar_ipca()
    atualizar_curva_di()
    novos = _novos_do_universo()

    if leve:
        data = ultimo_dia_util()
        for t, lst in novos.items():                 # importa so os ativos novos
            for tk in lst:
                try:
                    log(f"  novo {tk}: {importar_ticker(tk, data)}")
                except Exception as e:
                    log(f"  novo {tk}: ERRO {e}")
        refresh_ipca_se_novo()                        # VNA do IPCA ~1x/mes
    else:
        importar_main(["deb", "cri", "cra"])          # refresh completo
        _marcar_ipca()                                # tudo ja foi reimportado

    verificar_mudancas_lote(atualizar=True)           # rodizio de mudanca de fluxo
    log("=== ROTINA DIARIA FIM ===")


if __name__ == "__main__":
    completo = "--completo" in sys.argv
    if "--agendar" in sys.argv:
        agendar(completo=completo)
    else:
        run(leve=not completo)
