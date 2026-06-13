"""
Add-in Excel via xlwings.

Instalar:
  1. Abra o Excel
  2. Execute: python excel/addin.py install
  3. No Excel: Habilite Macros e acesse via Desenvolvedor > COM Add-ins > xlwings

Funções disponíveis no Excel após instalação:
  =RF_PU(ticker, yield, [data])       → PU
  =RF_TAXA(ticker, PU, [data])        → Yield (% a.a.)
  =RF_DURATION(ticker, yield, [data]) → Duration (anos)
  =RF_INFO(ticker, campo)             → info do papel (method, expiredate, issuer...)
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

try:
    import xlwings as xw
except ImportError:
    print("xlwings não instalado. Execute: pip install xlwings")
    sys.exit(1)


@xw.func
@xw.arg("ticker", str)
@xw.arg("yield_pct", float)
@xw.arg("data", str, default="")
def RF_PU(ticker: str, yield_pct: float, data: str = "") -> float:
    """Retorna o PU do papel dado uma yield (% a.a.)."""
    try:
        from src.calc import calc_pu
        result = calc_pu(ticker.upper().strip(), yield_pct, data or None)
        return result["PU"]
    except Exception as e:
        return f"ERRO: {e}"


@xw.func
@xw.arg("ticker", str)
@xw.arg("pu", float)
@xw.arg("data", str, default="")
def RF_TAXA(ticker: str, pu: float, data: str = "") -> float:
    """Retorna a yield (% a.a.) do papel dado um PU."""
    try:
        from src.calc import calc_yield
        result = calc_yield(ticker.upper().strip(), pu, data or None)
        return result["yield"]
    except Exception as e:
        return f"ERRO: {e}"


@xw.func
@xw.arg("ticker", str)
@xw.arg("yield_pct", float)
@xw.arg("data", str, default="")
def RF_DURATION(ticker: str, yield_pct: float, data: str = "") -> float:
    """Retorna a duration (anos) do papel dado uma yield (% a.a.)."""
    try:
        from src.calc import calc_pu
        result = calc_pu(ticker.upper().strip(), yield_pct, data or None)
        return result["duration"]
    except Exception as e:
        return f"ERRO: {e}"


@xw.func
@xw.arg("ticker", str)
@xw.arg("campo", str)
@xw.arg("data", str, default="")
def RF_INFO(ticker: str, campo: str, data: str = "") -> str:
    """
    Retorna informação do papel.
    Campos da tabela bonds: method | expiredate | issuer | tipo | status | yield_contract
    Campos dinâmicos: vna | n_flows | source
    """
    try:
        from src.calc import bond_info
        from src.db import get_conn
        from datetime import date as dt_date

        tk = ticker.upper().strip()
        campo_lower = campo.lower().strip()
        calc_date = data.strip() or dt_date.today().isoformat()

        # Campos dinâmicos (buscados no flow_cache)
        if campo_lower in ("vna", "n_flows", "source"):
            with get_conn() as conn:
                row = conn.execute(
                    "SELECT vna, COUNT(*) as n FROM flow_cache WHERE ticker=? AND calc_date=?",
                    (tk, calc_date)
                ).fetchone()
            if row and row["n"] > 0:
                if campo_lower == "vna":
                    return str(row["vna"] or "")
                if campo_lower == "n_flows":
                    return str(row["n"])
                if campo_lower == "source":
                    return f"cache:{calc_date}"
            # Fallback: data mais recente
            with get_conn() as conn:
                row2 = conn.execute(
                    "SELECT vna, COUNT(*) as n, MAX(calc_date) as dt FROM flow_cache WHERE ticker=?",
                    (tk,)
                ).fetchone()
            if row2 and row2["n"] > 0:
                if campo_lower == "vna":
                    return str(row2["vna"] or "")
                if campo_lower == "n_flows":
                    return str(row2["n"])
                if campo_lower == "source":
                    return f"cache:{row2['dt']}"
            return "sem dados"

        info = bond_info(tk)
        if not info:
            return "PAPEL NAO ENCONTRADO"
        return str(info.get(campo_lower, "campo invalido"))
    except Exception as e:
        return f"ERRO: {e}"


@xw.func
@xw.arg("ticker", str)
def RF_FETCH(ticker: str) -> str:
    """
    Busca dados do ativo na B3/API e registra no banco local.
    Retorna resumo ou mensagem de erro.
    Uso na aba Cadastrar: =RF_FETCH(C5)
    """
    try:
        from src.sync_bonds import register_bond
        register_bond(ticker.upper().strip())
        return f"OK: {ticker.upper().strip()} registrado"
    except Exception as e:
        return f"ERRO: {e}"


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        xw.Book.caller()
    else:
        xw.serve()
