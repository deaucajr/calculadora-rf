"""
Formatacao padrao brasileiro: separador de colunas = ;  decimal = ,  BOM + UTF-8.

Uso:
    from src.fmt_br import fmt, fmt_pct, SEP
    csv = f"ticker{SEP}EGIEA6\nvna{SEP}{fmt(1448.562894)}\n"
"""
SEP = ";"
DECIMAL = ","
BOM = "﻿"  # Byte Order Mark — Excel reconhece UTF-8 e abre colunas corretas


def fmt(valor: float, decimais: int = 6) -> str:
    """Formata numero com virgula decimal. Ex: fmt(1448.562894) -> '1448,562894'"""
    if valor == int(valor) and decimais > 0:
        # Inteiro: nao precisa de tantos zeros
        return f"{valor:.{decimais}f}".replace(".", DECIMAL)
    return f"{valor:.{decimais}f}".replace(".", DECIMAL)


def fmt_pct(valor: float, decimais: int = 10) -> str:
    """Formata percentual (ja em %). Ex: fmt_pct(6.5) -> '6,5000000000'"""
    return f"{valor:.{decimais}f}".replace(".", DECIMAL)


def fmt_int(valor: int) -> str:
    """Formata inteiro. Ex: fmt_int(125) -> '125'"""
    return str(valor)


def parse_br(s: str) -> float:
    """Converte string brasileira ('1448,56') -> float (1448.56)."""
    if not s or not s.strip():
        return 0.0
    return float(s.strip().replace(DECIMAL, "."))


def csv_header(*colunas: str) -> str:
    """Cabecalho CSV. Ex: csv_header('DATA', 'VF', 'PV') -> 'DATA;VF;PV'"""
    return SEP.join(colunas)


def csv_row(*valores) -> str:
    """Linha CSV com formatacao automatica.
    Ex: csv_row('2026-12-15', 65.0, 1448.562894) -> '2026-12-15;65,000000;1448,562894'
    """
    parts = []
    for v in valores:
        if isinstance(v, float):
            parts.append(fmt(v))
        elif isinstance(v, int):
            parts.append(fmt_int(v))
        else:
            parts.append(str(v))
    return SEP.join(parts)


def csv_write(path, linhas: list[str]):
    """Escreve arquivo CSV com BOM + UTF-8."""
    path.write_text(BOM + "\n".join(linhas), encoding="utf-8")
