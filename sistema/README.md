# RF_Calc — Calculadora de Renda Fixa

Add-in Excel para precificar debentures, CRIs e CRAs diretamente na planilha,
sem depender de sistemas externos no momento do calculo.
Os dados sao importados uma vez (ou atualizados pela rotina diaria) e ficam
armazenados localmente em CSVs; o add-in le esses arquivos em milissegundos.

---

## Estrutura de pastas

```
sistema/
├── README.md               # este arquivo
├── requirements.txt        # dependencias Python
├── credenciais.txt.exemplo # modelo para criar credenciais.txt (nunca versionar)
├── config.example.json     # modelo para config.json            (nunca versionar)
├── setup.py                # setup inicial apos git clone
│
├── addin/                  # Add-in Excel (VBA + builder)
│   ├── RF_Calc.bas         # codigo VBA completo do add-in
│   └── build_xlam.py       # compila RF_Calc.bas -> dist/RF_Calc.xlam.bin
│
├── src/                    # Biblioteca Python (nucleo do sistema)
│   ├── api_client.py       # cliente da API calculadorarendafixa.com.br
│   ├── calc.py             # calculo de PU/taxa/duration em Python
│   ├── db.py               # banco SQLite (esquema e helpers)
│   ├── paths.py            # resolucao de caminhos (fluxos_dir, etc.)
│   ├── sync_bacen.py       # baixa CDI diario do BACEN (publico)
│   ├── sync_b3_curve.py    # baixa curva DI x Pre da B3 (publico)
│   ├── sync_bonds.py       # sincroniza cadastro de ativos
│   ├── sync_flows.py       # sincroniza fluxos de ativos
│   └── vna.py              # calculo de VNA (IPCA, CDI, PRE)
│
├── scripts/                # Scripts operacionais (uso direto no terminal)
│   ├── rotina_diaria.py         # ** roda todo dia ** -- atualiza CDI, curva, IPCA
│   ├── importar_fluxos.py       # importa fluxos de um ticker especifico
│   ├── importar_todos.py        # importa todos os DEB/CRI/CRA de uma vez
│   ├── atualizar_pela_b3.py     # re-importa ativos com mudanca na B3
│   ├── atualizar_ipca.py        # atualiza historico IPCA (BACEN + projecao ANBIMA)
│   ├── atualizar_amortpct.py    # recalcula AMORTPCT dos ativos IPCA amortizantes
│   ├── gerar_ipca.py            # gera _ipca.csv com fatores diarios de correcao
│   ├── verificar_cadastro.py    # lista ativos B3 que ainda nao foram importados
│   ├── verificar_mudancas.py    # detecta ativos com fluxo alterado na B3
│   ├── corrigir_csvs.py         # corrige inconsistencias nos CSVs locais
│   ├── inserir_manual.py        # adiciona ativo manualmente (sem API)
│   ├── importar_planilha.py     # importa fluxos de uma planilha Excel
│   ├── gerar_template_ativo.py  # gera planilha-template para inserir ativo manual
│   ├── importar_curva_bloomberg.py  # importa curva DI de arquivo Bloomberg
│   ├── importar_curva_historica.py  # importa curva DI historica (varios dias)
│   ├── breakeven.py             # analise de breakeven IPCA vs PRE vs CDI
│   ├── gerar_planilha_swap.py   # gera planilha de swap CDI x IPCA
│   ├── validar.py               # valida PU local vs API (amostra)
│   ├── validar_massa.py         # valida PU de 50 tickers x 5 datas vs API
│   └── validar_curva.py         # valida curva DI local vs API
│
├── dist/                   # Arquivos de distribuicao (versionados)
│   ├── RF_Calc.xlam.bin    # add-in compilado (renomeado de .xlam para passar pelo Gmail)
│   ├── CADASTRO_ATIVO.xlsx # planilha-template para inserir ativos manualmente
│   └── instalar.py         # instalador rapido (requer internet/GitHub)
│
└── data/                   # Dados locais -- NAO versionados (git-ignored)
    ├── rf.db               # banco SQLite com cadastro e historico
    ├── fluxos/             # CSVs de cada ativo + arquivos globais:
    │   ├── _feriados.csv       # calendario de feriados ANBIMA
    │   ├── _cdi.csv            # CDI diario (BACEN)
    │   ├── _ipca.csv           # fatores diarios de correcao IPCA
    │   ├── _curva_di.csv       # curva DI x Pre da B3
    │   └── <TICKER>.csv        # fluxo de cada ativo (ex: EGIEA6.csv)
    └── fluxos_manual/      # CSVs inseridos manualmente (nao sobrescritos pela API)
```

---

## Instalacao rapida (com internet / GitHub)

Pre-requisitos: Python 3.8+, Excel instalado, Excel **fechado**.

```
# 1. Clone o repositorio
git clone https://github.com/deaucajr/calculadora-rf.git
cd calculadora-rf/sistema

# 2. Execute o setup (instala deps, banco, CDI, curva, add-in)
python setup.py

# 3. Reabra o Excel -- as funcoes RF_* ja aparecem
```

Para importar os fluxos de todos os ativos (requer credenciais da API):

```
# Configure as credenciais (copie e renomeie o exemplo)
copy credenciais.txt.exemplo credenciais.txt
# edite credenciais.txt com seu login e senha

python setup.py --importar
```

---

## Instalacao sem internet (ambientes restritos)

Use o instalador autossuficiente gerado pelo script `tools/gerar_instalador_offline.py`.
Ele empacota o add-in + todos os CSVs + scripts num unico arquivo `.py` de ~4 MB
que nao precisa de GitHub, internet, nem APIs.

```
# No computador que TEM internet:
python tools/gerar_instalador_offline.py
# Gera: Downloads/instalar_offline.py  (~4 MB, autossuficiente)

# Copie instalar_offline.py para o computador sem internet e execute:
python instalar_offline.py
```

---

## Uso diario

**Atualizar dados toda manha (antes de abrir o Excel):**

```
python scripts/rotina_diaria.py
```

O que a rotina faz:
- Baixa o CDI do dia do BACEN
- Atualiza a curva DI x Pre da B3
- Atualiza projecao IPCA (ANBIMA)
- Gera novos fatores diarios `_ipca.csv`
- Reimporta ativos com mudanca de fluxo detectada na B3

**Importar um ativo novo:**

```
python scripts/importar_fluxos.py EGIEA6
```

**Ver quais ativos ainda nao foram importados:**

```
python scripts/verificar_cadastro.py
python scripts/verificar_cadastro.py --baixar   # baixa os que faltam
```

---

## Funcoes do add-in Excel

Todas as funcoes recebem `taxa` em **% a.a.** e `data` no formato da sua planilha
(numero serial de data ou texto DD/MM/AAAA).

| Funcao | Descricao |
|--------|-----------|
| `=RF_PU(ticker; taxa; data)` | PU do ativo na data dada a taxa |
| `=RF_TAXA(ticker; pu; data)` | Taxa implicita dado o PU |
| `=RF_DURATION(ticker; taxa; data)` | Duration de Macaulay (anos) |
| `=RF_DV01(ticker; taxa; data)` | DV01 em R$ por 1 bp |
| `=RF_CONVEXIDADE(ticker; taxa; data)` | Convexidade |
| `=RF_VNA(ticker; data)` | VNA na data (corrigido por IPCA quando aplicavel) |
| `=RF_FLUXO(ticker; taxa; data)` | Tabela de fluxos descontados |
| `=RF_VENCIMENTO(ticker)` | Data de vencimento |
| `=RF_ATUALIZADO_EM(ticker)` | Data da ultima importacao de fluxos |
| `=RF_PROXIMO_EVENTO(ticker; data)` | Proximo cupom/amortizacao apos a data |
| `=RF_SPREAD(ticker)` | Spread/taxa de emissao contratual |
| `=RF_INFO(ticker; campo)` | Campo do cabecalho (EMISSOR, INDEXADOR...) |
| `=RF_LISTAR()` | Lista todos os ativos com CSV disponivel |
| `=RF_YTC(ticker; pu; data; dataCall)` | Yield to Call |
| `=RF_YTW(ticker; pu; data)` | Yield to Worst |
| `=RF_DI_PU(venc; taxa; data)` | PU do DI futuro |
| `=RF_DI_TAXA(venc; pu; data)` | Taxa do DI futuro dado o PU |
| `=RF_NTNB_PU(venc; taxa; data; vna)` | PU da NTN-B |
| `=RF_NTNB_TAXA(venc; pu; data; vna)` | Taxa real da NTN-B dado o PU |

**Macro utilitaria:** `Alt+F8 -> RF_ATUALIZAR` limpa o cache do add-in e forca
releitura dos CSVs (use apos rodar a rotina diaria ou importar novos ativos).

---

## Modelo de dados -- formato do CSV

Cada ativo tem um arquivo `data/fluxos/<TICKER>.csv` com tres tipos de linha:

```
META    TICKER      EGIEA6
META    INDEXADOR   IPCA
META    EMISSOR     EGL INDUSTRIA E COMERCIO SA
META    VENCIMENTO  2031-06-15
META    TAXA_REF    6.2474
META    DATA_FLUXO  2026-06-13
FLUXO   2026-12-15  CUPOM   6.2474  0  252  0.030463
FLUXO   2027-06-15  CUPOM   6.2474  0  504  0.030463
VNA     2026-06-13  1234.567890
```

Para ativos CDI ha tambem linhas `FLUXOD` (fluxo com desconto DI embutido)
e `AMORTPCT` (percentual de amortizacao para IPCA amortizantes).

---

## Reconstruir o add-in apos editar o VBA

```
# 1. Edite addin/RF_Calc.bas
# 2. Feche o Excel
python addin/build_xlam.py
# 3. Reabra o Excel
```

O `build_xlam.py` gera `dist/RF_Calc.xlam.bin` (versionado) e instala o
add-in em `%APPDATA%\Microsoft\AddIns\RF_Calc.xlam` automaticamente.

---

## Credenciais

A API `calculadorarendafixa.com.br` requer login/senha.

```
copy credenciais.txt.exemplo credenciais.txt
# Edite credenciais.txt com seu login e senha (arquivo fica fora do git)
```

O `config.json` (tambem fora do git) substitui `credenciais.txt` com
configuracoes adicionais. Veja `config.example.json` para o formato.

---

## Validacao

Para confirmar que os PUs calculados batem com a B3:

```
python scripts/validar.py               # amostra de 5 ativos por tipo
python scripts/validar_massa.py         # 50 tickers x 5 datas por tipo
python scripts/validar_massa.py --tipo DEB --n 20
```

Resultado esperado: >= 99% dos PUs dentro de R$ 0,01 de tolerancia.
