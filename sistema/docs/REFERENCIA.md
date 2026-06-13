# Referência das funções do add-in RF_Calc

Referência rápida de todas as fórmulas do add-in. A documentação técnica completa
(modelo matemático, armadilhas, arquitetura) está em `../wiki/projeto-addin-fluxos.md`.
O cabeçalho do código-fonte `excel/RF_Calc.bas` também resume as funções.

> No Excel em português, separe os argumentos com **;** e use **,** decimal.
> Toda função pede a **data** explicitamente. Taxa em **% a.a.** (ex: 6,2474).
> Para ver as dicas de cada argumento: digite `=RF_PU(` e clique no botão **fx**.

---

## Funções (UDF)

| Função | O que retorna | Sintaxe |
|--------|---------------|---------|
| `RF_PU` | Preço Unitário | `=RF_PU(ticker; taxa; data)` |
| `RF_TAXA` | Taxa implícita (% a.a.) dado o PU | `=RF_TAXA(ticker; pu; data)` |
| `RF_DURATION` | Duration de Macaulay (anos) | `=RF_DURATION(ticker; taxa; data)` |
| `RF_DV01` | Sensibilidade em R$ por +1 bp | `=RF_DV01(ticker; taxa; data)` |
| `RF_VNA` | VNA na data | `=RF_VNA(ticker; data)` |
| `RF_FLUXO` | Tabela do fluxo descontado (matriz) | `=RF_FLUXO(ticker; taxa; data)` |
| `RF_INFO` | Campo do cabeçalho ou "DATAS" | `=RF_INFO(ticker; campo)` |
| `RF_LISTAR` | Lista os ativos disponíveis | `=RF_LISTAR()` |

`RF_INFO` campos: `EMISSOR`, `VENCIMENTO`, `INDEXADOR`, `METHOD`, `TAXA_REF`,
`VNE`, `INICIO_RENT`, `DATA_FLUXO`, `DATAS` (datas com dados disponíveis).

`RF_FLUXO` devolve uma matriz (Data | Evento | DU | VF | PV). No Excel 365 ela
"derrama" sozinha; em versões antigas, selecione o intervalo e use Ctrl+Shift+Enter.

Macros (Alt+F8): `RF_ATUALIZAR` (recarrega os dados da pasta) ·
`RF_EXPORTAR` (gera uma planilha formatada VF→PV para enviar a alguém).

---

## A matemática (o que cada número significa)

Notação: `du` = dias úteis (252/ano) da data de cálculo até cada fluxo.

### PU — IPCA e PRÉ
```
PU = [ Σ FC_i% / (1 + taxa/100)^(du_i/252) ] × VNA(data)
```
`FC_i% = VF_i / VNA` é fixo (independe da data); `VNA(data)` carrega a inflação
(IPCA) ou é constante (PRÉ). Exato em qualquer data.

### PU — CDI + spread (DI-SPREAD)
```
PU = Σ PV_i × ((1 + y0/100) / (1 + taxa/100))^(du_i/252)
```
`y0` = taxa de referência da importação; `PV_i` = present value salvo (já embute o
desconto do CDI). Taxa = spread (ex: 1,274). Exato nas datas importadas.

### PU — % do CDI (DI-PERC)
```
PU = Σ PV_i × ((1 + d·y0/100) / (1 + d·taxa/100))^(du_i)
```
`d` = CDI diário (de `fluxos/_cdi.csv`). Taxa = % do CDI (ex: 101,92). O sistema
distingue DI-PERC de DI-SPREAD pela **magnitude da taxa** (≥ 50 ⇒ % do CDI).

### Duration de Macaulay
```
Duration = Σ (t_i × PV_i) / Σ PV_i        (t_i = du_i/252, em anos)
```

### DV01 (sensibilidade a 1 ponto-base)
```
DV01 = duration_modificada × PU × 0,0001
     = duration / (1 + taxa/100) × PU / 10000
```
É quanto o PU varia (em R$) quando a taxa sobe 1 bp (0,01%). Valor positivo.

### Convenções
- Dias úteis: calendário de feriados nacionais ANBIMA (`fluxos/_feriados.csv`).
- Truncamento do PU em 6 casas (padrão B3 "T|06").

---

## Limites e mensagens de erro

- `#N/D` — ticker não encontrado na pasta `fluxos/`.
- `#NÚM!` — CDI numa data **não importada** (importe: `python importar_fluxos.py TICKER AAAA-MM-DD`),
  ou PU fora do intervalo possível no `RF_TAXA`.
- `#VALOR!` — argumento inválido (ex: data em formato errado).
- IPCA/PRÉ funcionam em **qualquer** data. CDI/%CDI são exatos nas datas importadas
  (a rotina diária mantém o dia corrente; outras datas, importe sob demanda).
