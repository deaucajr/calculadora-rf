---
tipo: tema
tags: [curva-di, juros, DI-futuro, taxaswap, historico, interpolacao, bloomberg]
fontes: []
atualizado: 2026-06-14
---

# Curva DI×PRÉ Histórica — Metodologia e Fontes

Como obter a curva de juros DI×PRÉ para qualquer data de pregão (presente ou passada)
e populá-la em `data/fluxos/_curva_di.csv` para uso no [[projeto-addin-fluxos]].

---

## O que é a curva DI×PRÉ

A curva PRE (chamada "DI x Pré" pela B3) mapeia prazos (du = dias úteis até vencimento)
em taxas prefixadas anuais, construída a partir dos contratos de DI Futuro negociados na B3.
É a estrutura a termo de juros de mercado usada para:
- Precificar ativos CDI a taxas distintas das importadas
- Projetar a curva forward implícita para %CDI (DI-PERC)
- Calcular métricas de risco (DV01, duration)

Formato no `_curva_di.csv` (TSV, 3 colunas):
```
data_iso    du    taxa_pct_aa
2024-06-10  1     10.400000
2024-06-10  2     10.411000
2024-06-10  7     10.417000
...
```
`taxa_pct_aa` = taxa em % a.a. (ex: `10.40` = 10,40% a.a.)

---

## Fonte 1 — API B3 Portal Angular (apenas ~20 pregões recentes)

**Script:** `src/sync_b3_curve.py`

**URL:** `https://sistemaswebb3-derivativos.b3.com.br/referenceRatesProxy/Search/GetList/<b64>`

**Problema:** O parâmetro `date` é ignorado — sempre retorna a curva do dia atual.
Testado com 5 datas (2020–2026): todas retornam `rate=14.40` (jun/2026). Inútil para histórico.

**Uso:** Só para manter os ~20 pregões mais recentes atualizados via `rotina_diaria.py`.

---

## Fonte 2 — TaxaSwap B3 (qualquer data desde ~2006) ✅

**Script:** `scripts/importar_curva_historica.py`

### URL
```
https://www.b3.com.br/pesquisapregao/download?filelist=TS{YYMMDD}.ex_,
```
Onde `YYMMDD` = ano 2 dígitos + mês + dia (ex: `240610` para 2024-06-10).
Disponível para qualquer pregão histórico. Retorna 200 para dias úteis, sem arquivo para
feriados/fins de semana.

### Estrutura do arquivo (double-nested)

```
HTTP response body
└── ZIP normal (PK\x03\x04)
    └── TS{YYMMDD}.ex_   (Windows PKSFX self-extracting executable)
        ├── MZ header (PE)
        └── ZIP embutido (encontrar via busca de PK\x03\x04 no binário)
            └── TaxaSwap.txt   (texto, latin-1, ~1400 linhas × 28 tipos)
```

**Extração em Python:**
```python
outer = zipfile.ZipFile(io.BytesIO(r.content))
inner_bytes = outer.read(outer.namelist()[0])       # SFX binário
pk_off = inner_bytes.find(b"PK\x03\x04")           # ZIP embutido no SFX
inner_zip = zipfile.ZipFile(io.BytesIO(inner_bytes[pk_off:]))
txt = inner_zip.read("TaxaSwap.txt").decode("latin-1")
```

### Formato TaxaSwap.txt (largura fixa, latin-1)

| Posição | Campo | Exemplo |
|---------|-------|---------|
| [21:26] | Tipo | `PRE  ` (ou `CDI  `, `USD  `, etc.) |
| [41:46] | du (dias úteis) | `00001` |
| [46:51] | dc (dias corridos) | `00001` |
| [51]    | Sinal | `+` ou `-` |
| [52:66] | Taxa raw (14 dígitos) | `00000104000000` |
| [66]    | Vértice | `F`=futuro, `M`=mercado |

**Conversão para % a.a.:** `taxa = sinal × int(taxa_raw) / 1e7`
- Exemplo: `00000104000000` → 104.000.000 / 1e7 = **10,4000%**

Filtrar: `tipo == 'PRE'` e `0 < taxa < 100`.

### Uso

```bash
# 1 ano
python scripts/importar_curva_historica.py 2024-01-01 2024-12-31

# Backfill completo (anos, lento ~0.5s/pregão)
python scripts/importar_curva_historica.py 2006-01-01 2025-12-31

# Forçar rebaixar datas já existentes
python scripts/importar_curva_historica.py 2024-01-01 2024-12-31 --forcar
```

**Performance:** ~0,5s por pregão = ~125 pregões/min = ~1 ano em ~2 min.

---

## Fonte 3 — Bloomberg DI Futuro (formato OD*)

**Script:** `scripts/importar_curva_bloomberg.py`

Para quem tem acesso ao Bloomberg Terminal: série diária de preços (PU) de todos os
contratos de DI Futuro, exportada como planilha.

### Convenção de nomes

| Bloomberg | B3 | Significado |
|-----------|-----|-------------|
| OD | DI1 | Prefixo para DI Futuro |
| ODF21 | DI1F21 | DI Futuro Janeiro 2021 |
| ODH24 | DI1H24 | DI Futuro Março 2024 |

**Código de mês (padrão B3/Bloomberg):**
F=Jan, G=Fev, H=Mar, J=Abr, K=Mai, M=Jun, N=Jul, Q=Ago, U=Set, V=Out, X=Nov, Z=Dez

### Vencimento dos contratos DI

Os contratos vencem no **primeiro dia útil do mês do contrato** (calendário B3).
O script computa o vencimento com os feriados nacionais fixos do Brasil:
(1/1, 21/4, 1/5, 7/9, 12/10, 2/11, 15/11, 20/11, 25/12).
Feriados móveis (Carnaval, Corpus Christi) e municipais não estão incluídos —
impacto na contagem de du é de ±1 dia, irrelevante para taxas.

### Conversão PU → taxa

```
du = dias úteis de T+1 até o vencimento (inclusive)
taxa_pct = ((100000 / PU)^(252/du) - 1) × 100
```

PU normalmente em torno de 100.000 (ex: 93518,45 para ~10% por 1 ano).
O script aceita PU em formato centesimal (93,51) e normaliza automaticamente.

### Formato do arquivo de entrada

```
data,ODF24,ODG24,ODH24,ODJ24,...
2023-01-02,92350.45,92280.12,...
2023-01-03,92401.20,92330.88,...
```

A coluna de data pode ser o índice, a primeira coluna, ou especificada com `--coldata`.

### Uso

```bash
python scripts/importar_curva_bloomberg.py serie_di.csv
python scripts/importar_curva_bloomberg.py serie_di.xlsx --forcar
python scripts/importar_curva_bloomberg.py arquivo.csv --coldata "Data Pregao"
```

---

## Metodologia de interpolação (flat-forward)

Quando se precisa de um prazo `du` que não é um vértice da curva, usa-se
interpolação **flat-forward** (constante entre nós no espaço log do fator de desconto):

```
FD(du) = FD(d1) × (FD(d2)/FD(d1))^((du-d1)/(d2-d1))
```

Onde `FD(d) = 1/(1 + taxa_d/100)^(d/252)`.

Isso garante taxa forward constante entre dois vértices consecutivos (condição de
não-arbitragem nos mercados de juros).

O VBA no RF_Calc implementa isso implicitamente via interpolação na taxa (função `TaxaParaDu`)
usando a curva carregada do `_curva_di.csv` para a data mais próxima disponível.

---

## Investigação: endpoints mortos

Durante o desenvolvimento (jun/2026) testaram-se estas fontes sem sucesso:

| Endpoint | Status | Motivo |
|----------|--------|--------|
| `referenceRatesProxy/Search/GetList` com data histórica | ❌ | Ignora parâmetro `date`; sempre retorna data atual |
| `www2.bmf.com.br/pages/.../lum-ajustes-do-pregao-ptBR.asp` | ❌ | 301 redirect para JS |
| `www2.bmf.com.br/pages/.../lum-taxas-referenciais-bmf-ptBR.asp` | ❌ | 302 sem conteúdo |

A fonte TaxaSwap (pesquisapregao) permanece o único endpoint público funcional para histórico.

---

## Conexões

- [[projeto-addin-fluxos]] — Projeto que consome a curva para precificação
