# RF_Calc — Calculadora de Renda Fixa (Excel Add-in)

Add-in Excel para precificação offline de debentures, CRIs e CRAs brasileiros, sem depender de API a cada consulta. Suporta IPCA+, PRÉ, CDI+ e %CDI.

---

## O que faz

- **Precifica qualquer título** de renda fixa com funções diretas em células Excel (`=RF_PU(...)`, `=RF_TAXA(...)`, etc.)
- **Dados locais**: importa os fluxos de caixa da B3 uma vez e calcula offline para qualquer taxa e data
- **Escala**: suporta 3.000+ ativos simultaneamente com carregamento lazy (lê só o que precisa)
- **Exatidão**: erro < 0,01 R$ vs. API B3 para todos os tipos de indexador

---

## Funções Excel disponíveis

| Função | O que retorna |
|--------|--------------|
| `=RF_PU("EGIEA6", 6.5, "2026-06-14")` | Preço unitário em R$ |
| `=RF_TAXA("EGIEA6", 1447.32, "2026-06-14")` | Taxa implícita (YTM) em % a.a. |
| `=RF_DURATION("EGIEA6", 6.5, "2026-06-14")` | Duration de Macaulay em anos |
| `=RF_DV01("EGIEA6", 6.5, "2026-06-14")` | Sensibilidade a 1bp em R$ |
| `=RF_VNA("EGIEA6", "2026-06-14")` | Valor Nominal Atualizado em R$ |
| `=RF_FLUXO("EGIEA6", 6.5, "2026-06-14")` | Tabela completa de fluxos (array) |
| `=RF_INFO("EGIEA6", "EMISSOR")` | Metadado do ativo (emissor, vencimento, etc.) |
| `=RF_LISTAR()` | Lista todos os tickers disponíveis |
| `=RF_YTC("EGIEA6", 1447, "2026-06-15", "2028-06-15")` | Yield to Call (taxa na data de call) |
| `=RF_YTW("EGIEA6", 1447, "2026-06-15")` | Yield to Worst (menor entre YTM e todos os YTCs) |

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
├── addin/
│   └── RF_Calc.bas          ← Código-fonte VBA do add-in
├── sistema/
│   ├── scripts/
│   │   ├── importar_fluxos.py          ← Importa 1 ativo da API B3
│   │   ├── importar_todos.py           ← Importação em massa (3.000+ ativos)
│   │   ├── rotina_diaria.py            ← Detecta novos + atualiza (agendável)
│   │   ├── importar_curva_historica.py ← Curva DI histórica via TaxaSwap B3
│   │   ├── importar_curva_bloomberg.py ← Curva DI via planilha Bloomberg (OD*)
│   │   ├── gerar_planilha_swap.py      ← Planilha Excel de analise de swap/breakeven
│   │   ├── atualizar_amortpct.py       ← Popula amortizações em ativos IPCA+
│   │   ├── validar.py                  ← Compara cálculo local vs. API B3
│   │   └── build_xlam.py               ← Gera RF_Calc.xlam via COM
│   └── src/
│       ├── sync_b3_curve.py            ← Baixa curva DI recente da B3
│       ├── api_client.py               ← Cliente da API B3
│       └── paths.py                    ← Configuração de caminhos
├── wiki/                    ← Base de conhecimento do projeto
├── documentacao_RF_Calc.txt ← Referência completa das funções
└── README.md
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
