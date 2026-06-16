# RF_Calc — Calculadora de Renda Fixa (Excel Add-in) v3

Add-in Excel para precificação offline de QUALQUER ativo de renda fixa brasileiro:
debentures, CRIs, CRAs, NTN-B, NTN-F e DI Futuro.

**Fonte primária: FI Analytics** (juros incorporados, gross-up, DI equivalente).
**VNA: cálculo 100% local** (IPCA via BACEN, CDI via BACEN série 12).

---

## O que faz

- **Precifica qualquer título** com funções diretas em células Excel (`=RF_PU(...)`, `=RF_TAXA(...)`, etc.)
- **Dados locais**: importa fluxos do FI Analytics e calcula offline para qualquer taxa e data
- **VNA local**: calcula VNA de IPCA e CDI sem depender de API externa
- **Juros incorporados**: FI Analytics considera accrued interest (B3 não considera)
- **% Tai por evento**: `RF_FLUXO` mostra % da Tai e % Amortização de cada fluxo
- **Gross-up**: taxa com ajuste tributário (taxedM2MRate)
- **Escala**: suporta 3.000+ ativos com carregamento lazy
- **Exatidão**: erro < 0,01 R$ vs. API para todos os tipos de indexador

---

## Funções Excel disponíveis

### Precificação (funciona para qualquer ticker: debênture, NTN-B, DI Futuro)

| Função | O que retorna |
|--------|--------------|
| `=RF_PU("EGIEA6"; 6,5; "2026-06-14")` | PU para debênture IPCA+ |
| `=RF_PU("NTN-B 30"; 6,5; "2026-06-14")` | PU para NTN-B 2030 |
| `=RF_PU("DI1F30"; 14,4; "2026-06-14")` | PU para DI Futuro Jan/2030 |
| `=RF_TAXA("EGIEA6"; 1447,32; "2026-06-14")` | Taxa implícita (YTM) em % a.a. |
| `=RF_DURATION("EGIEA6"; 6,5; "2026-06-14")` | Duration de Macaulay em anos |
| `=RF_DV01("EGIEA6"; 6,5; "2026-06-14")` | Sensibilidade a 1bp em R$ |
| `=RF_CONVEXIDADE("EGIEA6"; 6,5; "2026-06-14")` | Convexidade (bump 0,1 p.p.) |
| `=RF_VNA("EGIEA6"; "2026-06-14")` | Valor Nominal Atualizado em R$ |
| `=RF_FLUXO("EGIEA6"; 6,5; "2026-06-14")` | Tabela: DATA\|EVENTO\|DU\|VF\|PV\|%TAI\|%AMORT |
| `=RF_GROSSUP("EGIEA6"; 1447; "2026-06-14")` | Taxa com gross-up tributário |
| `=RF_INFO("EGIEA6"; "EMISSOR")` | Metadado (EMISSOR, VENCIMENTO, INDEXADOR...) |
| `=RF_LISTAR()` | Lista todos os tickers disponíveis |

### Funções de Swap / Equivalência entre Indexadores

| Função | O que faz |
|--------|-----------|
| `=RF_INFLA_IMPLICITA(12.5, 6.5)` | Inflação implícita PRÉ vs IPCA+ (Fisher) |
| `=RF_BREAKEVEN_CDI(12.5, 100)` | CDI médio de equilíbrio PRÉ vs %CDI |
| `=RF_PCT_PARA_CDI(98, 13.5)` | %CDI → spread CDI+ equivalente |
| `=RF_CDI_PARA_PCT(0.5, 13.5)` | Spread CDI+ → %CDI equivalente |
| `=RF_CDI_PARA_IPCA(2.0, 13.5, 5.2)` | Spread CDI+ → spread IPCA+ (Fisher) |
| `=RF_IPCA_PARA_CDI(10.0, 13.5, 5.2)` | Spread IPCA+ → spread CDI+ |
| `=RF_PCT_PARA_IPCA(100, 13.5, 5.2)` | %CDI → spread IPCA+ (cadeia completa) |
| `=RF_IPCA_PARA_PCT(8.0, 13.5, 5.2)` | Spread IPCA+ → %CDI |

Cadeia de equivalência: `%CDI ↔ CDI+spread ↔ PRÉ ↔ IPCA+spread`

Documentação completa com exemplos e retornos esperados: [`documentacao_RF_Calc.txt`](documentacao_RF_Calc.txt)

---

## Estrutura do projeto

```
/
├── sistema/
│   ├── addin/
│   │   └── RF_Calc.bas              ← Código-fonte VBA do add-in (v3)
│   ├── bat/                         ← Scripts .bat para automação
│   │   ├── LEIA_ME.txt              ← Guia dos .bat files
│   │   ├── 1_sincronizar_completo.bat ← Baixa TODOS ativos (1a vez)
│   │   ├── 2_sincronizar_rapido.bat   ← Rotina diária incremental
│   │   ├── 3_instalar_addin.bat       ← Instala add-in no Excel
│   │   └── 4_validar.bat              ← Testa cálculos vs API
│   ├── config/
│   │   ├── tokens_template.txt      ← Template para GitHub (valores genéricos)
│   │   └── tokens.txt               ← SEUS tokens reais (GITIGNORED!)
│   ├── scripts/
│   │   ├── rotina_diaria_v2.py      ← Rotina diária (FI Analytics + BACEN + ANBIMA)
│   │   ├── importar_fluxos.py       ← Importa 1 ticker (B3 — legado)
│   │   ├── importar_todos.py        ← Importação em massa (B3 — legado)
│   │   ├── importar_curva_historica.py ← Curva DI histórica (TaxaSwap B3)
│   │   ├── importar_curva_bloomberg.py ← Curva DI via Bloomberg
│   │   ├── gerar_planilha_swap.py   ← Planilha Excel de swap/breakeven
│   │   ├── gerar_template_ativo.py  ← Template Excel de cadastro manual
│   │   ├── importar_planilha.py     ← Converte Excel → CSV
│   │   ├── atualizar_amortpct.py    ← Popula amortizações IPCA+
│   │   ├── validar.py               ← Compara PU local vs. API
│   │   └── migrar_csvs.py           ← Conversor de formato de CSV
│   └── src/
│       ├── __init__.py              ← Pacote Python
│       ├── config.py                ← Carregador de tokens (lê tokens.txt)
│       ├── db.py                    ← SQLite (rf.db)
│       ├── paths.py                 ← Resolve pasta de fluxos
│       ├── fi_client.py             ← Cliente FI Analytics (fonte PRIMÁRIA)
│       ├── sync_engine.py           ← Motor de sincronização principal
│       ├── sync_bacen.py            ← BACEN: CDI, IPCA, projeções ANBIMA
│       ├── sync_flows.py            ← B3 sync (legado)
│       ├── vna_calc.py              ← Cálculo LOCAL de VNA
│       ├── vna.py                   ← VNA legado
│       ├── calc.py                  ← Motor de cálculo local
│       ├── di_futuro.py             ← Cálculo local de DI Futuro
│       └── anbima_scraper.py        ← Scraper ANBIMA Data
├── wiki/                            ← Base de conhecimento
├── DOCUMENTACAO_FORMULAS.md         ← Guia completo de fórmulas com exemplos
├── INSTALAR.md                      ← Guia de instalação para colegas
├── INSTALAR_BANCO.md                ← Guia específico PC do banco
├── README.md                        ← Este arquivo
└── CLAUDE.md                        ← Configuração para LLMs
```

---

## Instalação

**Pré-requisitos:** Python 3.11+, Excel para Windows, pacotes `requests` e `pandas`.

```bash
# 1. Clone o repositório
git clone https://github.com/deaucajr/calculadora-rf.git
cd calculadora-rf

# 2. Instale dependências Python
pip install requests pandas openpyxl

# 3. Configure a pasta de dados em sistema/config.json
# (deixe vazio para usar o padrão local: sistema/data/fluxos/)

# 4. Gere e instale o add-in Excel
cd sistema
python scripts/build_xlam.py

# 5. Importe os ativos (primeira vez — leva ~30 min para universo completo)
python scripts/importar_todos.py
```

Após a instalação, o add-in é carregado automaticamente toda vez que o Excel abre.

---

## Cadastro manual de ativos

Para ativos que não estão na API B3 ou lançamentos novos:

1. Abra `sistema/dist/CADASTRO_ATIVO.xlsx`
2. Aba **Identificacao**: preencha os campos amarelos (Ticker, Indexador, Taxa, datas)
3. Aba **Fluxo_de_Caixa**: apague os exemplos e cole sua tabela de pagamentos:

| Data | Paga Juros? | % Amortização | Taxa (% a.a.) |
|------|-------------|---------------|---------------|
| 15/01/2027 | S | 0 | 6.5 |
| 15/01/2028 | S | 25 | 6.5 |
| 15/01/2029 | S | 25 | 6.5 |
| 15/01/2030 | S | 50 | 6.5 |

4. Salve o arquivo e rode:
```bash
cd sistema
python scripts/importar_planilha.py CADASTRO_ATIVO.xlsx
```
5. Teste no Excel: `=RF_PU("SEU_TICKER"; 6.5; HOJE())`

O script calcula automaticamente os dias úteis (DU) e o FC% de cada evento. Para gerar um novo template em branco: `python scripts/gerar_template_ativo.py`

---

## Uso diário

```bash
# Atualizar dados (rodar toda manhã, ou agendar via rotina_diaria.py)
cd sistema
python scripts/rotina_diaria.py

# Importar um ativo específico
python scripts/importar_fluxos.py EGIEA6

# Atualizar curva DI (últimos ~20 pregões, automático via rotina)
python src/sync_b3_curve.py
```

No Excel, pressione **Alt+F8 → RF_ATUALIZAR** se os dados não refletirem a atualização mais recente.

---

## Curva DI Histórica

A API pública da B3 retorna apenas os ~20 pregões mais recentes da curva DI×PRÉ. Para datas históricas, use:

```bash
# Via TaxaSwap B3 (qualquer data desde ~2006, ~2 min por ano)
python scripts/importar_curva_historica.py 2020-01-01 2025-12-31

# Via planilha Bloomberg com contratos ODF21/ODH21/etc.
python scripts/importar_curva_bloomberg.py minha_serie.csv
```

Metodologia detalhada: [`wiki/tema-curva-di-historica.md`](wiki/tema-curva-di-historica.md)

---

## Planilha de Swap

Gera um arquivo Excel com análise completa de equivalência entre indexadores:

```bash
# Defaults: CDI=13.5%, IPCA=5.2%, CDI+2.0%, nocional=1M, prazo=5 anos
python scripts/gerar_planilha_swap.py

# Customizado
python scripts/gerar_planilha_swap.py --cdi 13.5 --ipca 5.2 --spread-cdi 1.5 --pct-cdi 98 --nocional 5000000 --output meu_swap.xlsx
```

Abas geradas:
- **Equivalencias** — tabela de conversão %CDI/CDI+/IPCA+ para qualquer nível
- **Swap CDI+↔IPCA+** — NII projetado semestral para um swap CDI+ vs IPCA+
- **Swap %CDI↔IPCA+** — mesmo com %CDI e sensibilidade por nível de CDI
- **Breakeven** — PRÉ vs IPCA+ e %CDI vs PRÉ com situação atual marcada
- **Fórmulas** — referência completa das fórmulas e convenções do mercado

---

## Como funciona o cálculo

### IPCA+ e PRÉ
```
PU = [ Σ ( FC_i% / (1 + taxa/100)^(du_i/252) ) ] × VNA(data)
```
`FC%` é data-independente (importado uma vez). `VNA` é corrigido pelo IPCA + ajuste de amortizações.

### CDI+ e %CDI
Os fluxos projetados pela B3 são importados por data. Para %CDI, a curva forward é extraída implicitamente dos próprios fluxos (`FD_i = VF_i/PV_i`) e replicada com a nova taxa — sem precisar baixar a curva de mercado.

### VNA com amortizações (IPCA+ amortizante)
```
VNA(d) = VNA_ancora × (1 − cumul_d%) / (1 − cumul_ancora%) × IPCA(d)/IPCA(ancora)
```

---

## Tipos de ativo suportados

| Indexador | Exemplo | Precisão |
|-----------|---------|----------|
| IPCA+ | EGIEA6 | < 0,01 R$ |
| PRÉ | CSNA15 | < 0,001 R$ |
| CDI+ (spread) | BRMLA9 | < 0,01 R$ |
| %CDI | VLHA11 | < 0,05 R$ |

---

## Dados e privacidade

- `config.json` — credenciais (gitignored)
- `sistema/data/` — CSVs dos ativos (gitignored, regenerável via scripts)
- Os scripts não expõem dados de mercado; apenas consomem a API pública da B3

---

## Wiki

A pasta [`wiki/`](wiki/) contém documentação técnica e decisões de projeto:

- [`wiki/projeto-addin-fluxos.md`](wiki/projeto-addin-fluxos.md) — arquitetura completa, armadilhas resolvidas
- [`wiki/tema-curva-di-historica.md`](wiki/tema-curva-di-historica.md) — metodologia da curva histórica
