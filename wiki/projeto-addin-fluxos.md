---
tipo: projeto
tags: [renda-fixa, excel, vba, addin, debentures, cri, cra, B3]
fontes: []
atualizado: 2026-06-14
---

# Add-in Excel de Renda Fixa (RF_Calc)

Sistema local para precificar debentures, CRIs e CRAs (IPCA, PRE, CDI, %CDI) sem bater na API da B3 a cada consulta. Funcoes `RF_*` no Excel via add-in VBA leve.

## Arquitetura

```
sistema/
├── importar_fluxos.py    ← importa 1 ticker da API B3 -> fluxos/<TICKER>.csv
├── importar_todos.py     ← importacao em massa (deb+cri+cra) com resume/delays
├── rotina_diaria.py      ← detecta novos ativos + atualiza (agendavel 7h30)
├── validar.py            ← compara calculo local vs API (replica o VBA em Python)
├── keep_awake.py         ← impede hibernacao (trabalho noturno)
├── fluxos/               ← 1 CSV por ativo (lazy load) + _feriados.csv
└── excel/
    ├── RF_Calc.bas       ← modulo VBA do add-in
    └── build_xlam.py     ← gera RF_Calc.xlam limpo via COM + registra auto-load
```

Add-in instalado: `%APPDATA%\Microsoft\AddIns\RF_Calc.xlam` (~35KB, so codigo).
Auto-load via chave de registro `...\Excel\Options\OPEN = /R "RF_Calc.xlam"`.

## Leveza (lazy load)

O add-in NAO carrega nada ao abrir (`Auto_Open` so registra as dicas de funcao).
Cada `RF_PU(ticker,...)` le `fluxos/<TICKER>.csv` sob demanda e cacheia em memoria.
Abertura instantanea mesmo com milhares de ativos; cada CSV ~3KB.

## Formato do CSV (TAB, decimal = ponto)

```
META   CHAVE   VALOR        (TICKER, TIPO, INDEXADOR, EMISSOR, METHOD, VENCIMENTO, TAXA_REF, DATA_FLUXO...)
FLUXO  data  evento  vf  pv  du  fc_pct     (IPCA/PRE: 1 conjunto, FC% data-independente)
VNA    data  vna                            (IPCA: 1 ponto por data importada)
FLUXOD data_calc  data_evento  evento  vf  pv  du   (CDI: 1 bloco por data importada)
```

## Modelo de calculo

- **IPCA/PRE**: `PU(data,taxa) = [Σ FC_i% / (1+taxa/100)^(du_i/252)] × VNA(data)`.
  FC% = VF/VNA e' data-independente → 1 download serve p/ qualquer taxa/data.
  VNA(data): exato nas datas importadas, interpola geometricamente entre elas.
  PRE = mesmo modelo com VNA constante → exato em qualquer data com 1 ponto.
- **CDI**: B3 embute o CDI nos fluxos projetados. Guardamos VF e PV por data (FLUXOD,
  multi-data) e reajustamos a taxa. Distincao por **magnitude da TAXA_REF** (robusto,
  independe do method):
  - **DI-SPREAD** (taxa ~0,5-3 = spread aditivo): `PV_i × ((1+y0/100)/(1+taxa/100))^(du_i/252)`.
  - **DI-PERC / %CDI** (taxa >=50, ex 98 = % do CDI): **curva DI implicita**. O fator de
    desconto de cada vertice e' `FD_i = VF_i/PV_i` (ja vem da B3 no PV). Deriva-se o CDI
    forward diario por segmento entre vertices e reaplica-se o percentual `taxa`:
    `g = (FD_i/FD_{i-1})^(1/Δdu) → 1`, em fracao do CDI; `FD_i(taxa) = Π(1+g·taxa/100)^Δdu`;
    `PV_i = VF_i/FD_i(taxa)`. Funcao `PvCdi` no VBA / `_pu_perc_curva` no validador.
  Exato (~1e-5) nas datas importadas; `#NUM` em datas nao importadas (importe a data).
  A curva DI vem dos PROPRIOS fluxos do papel — nao precisa baixar a curva da B3.

- **Classificacao (IMPORTANTE)**: o INDEXADOR vem do **`calcPU.method`** (metodologia de
  precificacao), NAO do `getbonddetails.method` (que e' o indice de correcao do VNA e
  diverge: ex VNA corrige por IPCA mas precifica como DI-SPREAD). `corrigir_csvs.py`
  detecta e conserta isso localmente sem API (compara Σ PV vs Σ VF/(1+t)^du).
- Truncamento T|06 (B3): `Int(PU*1e6)/1e6`.
- DV01 analitico: `duration/(1+taxa/100) × PU × 0,0001`.

## Funcoes (taxa em % a.a.; data obrigatoria)

`RF_PU` `RF_TAXA` `RF_DURATION` `RF_DV01` `RF_VNA` `RF_FLUXO`(array) `RF_INFO`(campo ou "DATAS") `RF_LISTAR`.
Macros: `RF_ATUALIZAR` (limpa cache), `RF_EXPORTAR` (planilha VF→PV p/ enviar).

## Armadilhas resolvidas (NAO repetir)

- **Excel fechava sozinho**: chave `OPEN` apontava p/ `DEB-CALC3.xlam` inexistente.
  Diagnostico: `HKCU\...\Excel\Options` valor OPEN. Limpar referencias fantasma.
- **Locale pt-BR**: `CDbl("100.0")` = 1000 (ponto vira milhar)! Usar `Val(CStr(...))`
  para ler numeros de arquivo (sempre ponto). `CDate`/`CDbl` so p/ input do usuario.
- **FileFormat .xlam** = 55 (`xlOpenXMLAddIn`); 18 gera `.xla` antigo que nao abre.
- **ByRef type mismatch**: arrays vindos de `Array(...)`/dicionario sao `Variant`;
  parametros que os recebem devem ser `Variant`, nao `Double()`.
- **Add-in duplicado**: nunca abrir o .xlam via File→Open com ele instalado. Regerar
  com `build_xlam.py` (requer AccessVBOM=1 temporario; reverter p/ 0 depois).
- **Break on All Errors** (VBA Options): deixa o editor abrir no meio da macro;
  usar "Break on Unhandled Errors".

## Importacao e atualizacao

- `python importar_fluxos.py TICKER [data]` — 1 ativo (CDI acumula blocos por data).
- `python importar_todos.py [deb cri cra]` — universo: 2212 deb + 625 cri + 646 cra.
  Resume (pula os ja feitos hoje), delay 0.4s, log em data/import_massa.log.
- `python rotina_diaria.py --agendar` — tarefa 7h30 seg-sex (detecta novos + atualiza).

## VNA com amortizacoes (IPCA+)

Debentures IPCA+ amortizantes (ex: 18H0193630) tem eventos tipo "A" na B3 que reduzem o VNE
(valor nominal de emissao). A formula exata de VNA para datas distintas da ancora e':

```
VNA(d) = VNA_ancora × (1 - cumul_d%) / (1 - cumul_ancora%) × IPCA(d)/IPCA(ancora)
```

Onde `cumul_x%` = soma dos yields dos eventos A com data ≤ x (em % do VNE, soma total = 100%).
Implementado em VBA via `gAmortD`/`gAmortP` (arrays module-level, seguro pois VBA e' single-thread).
Linhas `AMORTPCT\tdata\tpct_vne` nos CSVs. `atualizar_amortpct.py` popula ativos antigos.
Erro antes: ~-1% para datas passadas. Depois: +0.19% (limite do IPCA interpolado; 0.000% na ancora).

## Curva DI — Fontes e Estrategias

Ver [[tema-curva-di-historica]] para detalhes completos. Resumo:

**Data atual (apenas ultimos ~20 pregoes):**
- `sync_b3_curve.py`: API `referenceRatesProxy/Search/GetList` da B3 (portal Angular).
  Salva em `data/fluxos/_curva_di.csv` (TSV: `data\tdu\ttaxa_pct_aa`).
  Taxa no formato percentagem: `10.40` = 10,40% a.a.
  Limitacao: endpoint ignora o parametro `date` para datas historicas (sempre retorna hoje).

**Historico (qualquer data desde ~2006):**
- `importar_curva_historica.py INI FIM`: baixa arquivo TaxaSwap (TS) da B3.
  URL: `https://www.b3.com.br/pesquisapregao/download?filelist=TS{YYMMDD}.ex_,`
  Formato: outer ZIP → inner SFX (exe) → busca `PK\x03\x04` → inner ZIP → `TaxaSwap.txt`.
  Taxa PRE (DI×PRE) em largura fixa: `[52:66] / 1e7` = % a.a. Amostra: du=1 dia = 10.40%.
  Delay 0.5s por data; ~5-10 min para 1 ano.

**Historico via Bloomberg (se disponivel):**
- `importar_curva_bloomberg.py arquivo.csv`: importa serie ODF21/ODH21 (PU B3 por contrato).
  OD→DI1, codigo de mes F/G/H/J/K/M/N/Q/U/V/X/Z, vencimento = 1o dia util do mes.
  `taxa_aa_pct = ((100000/PU)^(252/du) - 1) × 100`. Aceita .csv ou .xlsx.

**Curva implicita (DI-PERC sem curva externa):**
- `FD_i = VF_i/PV_i` (ja vem da B3 em cada papel DI-PERC). Curva forward por segmento.
  Exato (~1e-5) para a data importada; impraticavel para datas nao importadas.

## Conexoes

- [[tema-curva-di-historica]] — Metodologia detalhada: TaxaSwap, Bloomberg DI, interpolacao
