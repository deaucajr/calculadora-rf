# RF_Calc — Calculadora de Renda Fixa para Excel

O **RF_Calc** é uma solução profissional para precificação de títulos de renda fixa (Debêntures, CRIs e CRAs) diretamente no Excel. Ele utiliza um Add-in VBA que consome fluxos de caixa e indicadores (CDI, IPCA, Curva DI) armazenados em CSVs locais, garantindo cálculos instantâneos e funcionamento offline.

---

## 1. Estrutura de Pastas

```text
sistema/
├── addin/                  # Código-fonte e ferramentas do Add-in Excel
│   ├── RF_Calc.bas         # Código VBA principal (UDFs e Macros)
│   └── build_xlam.py       # Script que compila o .bas em .xlam e instala
├── bat/                    # Atalhos de uso diário (clique duplo ou terminal)
│   ├── rotina/             # Rotinas matinais (sem custo de API)
│   │   ├── atualizar_curva.bat   # Curva DI/PRE da B3 (endpoint público)
│   │   └── atualizar_ipca.bat    # IPCA histórico (BACEN) + projeção ANBIMA
│   ├── verificar/          # Manutenção e migração
│   │   ├── verificar_ativos_b3.bat  # Ativos B3 sem CSV local
│   │   └── migrar_formato_csvs.bat  # Converte CSVs do formato legado
│   └── README.md           # Descrição de cada script
├── src/                    # Núcleo do sistema (Python)
│   ├── api_client.py       # Cliente para integração com a API externa
│   ├── db.py               # Gerenciamento do banco SQLite local (rf.db)
│   ├── paths.py            # Centralização de caminhos e pastas de dados
│   └── sync_*.py           # Scripts de sincronização de indicadores e fluxos
├── scripts/                # Scripts utilitários e operacionais
│   ├── rotina_diaria.py    # Atualiza CDI, Curva DI e IPCA (rodar toda manhã)
│   ├── importar_fluxos.py  # Importa fluxos de ativos específicos
│   ├── importar_todos.py   # Download em massa de debêntures, CRIs e CRAs
│   ├── migrar_csvs.py      # Migra CSVs do formato legado para o novo
│   ├── validar.py          # Compara cálculos locais vs. API oficial
│   └── gerar_planilha_swap.py # Gera análise de swap CDI vs. IPCA
├── dist/                   # Distribuição e templates
│   ├── RF_Calc.xlam.bin    # Add-in compilado pronto para uso
│   └── CADASTRO_ATIVO.xlsx # Template para inserção manual de ativos
├── data/                   # Dados locais (Não versionado)
│   ├── rf.db               # Banco de dados de indicadores e histórico
│   └── fluxos/             # CSVs de cada ativo e indicadores de mercado
├── requirements.txt        # Dependências do projeto (requests, pywin32, etc.)
├── setup.py                # Script de configuração inicial (vazio p/ pronto)
└── README.md               # Esta documentação
```

---

## 2. Instalação

### Com Internet (Git)
1. Certifique-se de ter o **Python 3.8+** instalado e o **Excel fechado**.
2. Clone o repositório e execute o setup:
   ```bash
   python setup.py
   ```
3. O setup instalará dependências, criará o banco e configurará o Add-in no seu Excel.

### Sem Internet (Manual)
1. Copie a pasta do projeto para a máquina destino.
2. No Excel, vá em `Arquivo > Opções > Suplementos > Ir...` e selecione o arquivo `dist/RF_Calc.xlam.bin` (após renomear para `.xlam`).
3. Alternativamente, execute `python addin/build_xlam.py` se o Python estiver disponível.

---

## 3. Uso Diário

Clique duplo nos atalhos em `bat/rotina/` para atualizar os indicadores:

| Atalho | O que faz | Custo |
| :--- | :--- | :--- |
| `bat\rotina\atualizar_curva.bat` | Curva DI/PRE da B3 (endpoint público) | Grátis |
| `bat\rotina\atualizar_ipca.bat` | IPCA (BACEN) + projeção ANBIMA | Grátis |

Ou pelo terminal na raiz do projeto:
```bash
python scripts/rotina_diaria.py    # CDI + curva DI + IPCA de uma vez
```

**Scripts avulsos:**
*   **Importar um ativo:** `python scripts/importar_fluxos.py TICKER`
*   **Ver o que falta:** `bat\verificar\verificar_ativos_b3.bat`
*   **Cadastrar ausentes:** `bat\verificar\verificar_ativos_b3.bat --baixar` (usa API paga)
*   **Ajustar amortização:** `python scripts/atualizar_amortpct.py` (ativos IPCA)

---

## 4. Funções RF_* (Excel)

As funções aceitam taxas em **% a.a.** e datas no formato nativo do Excel.

| Função | Descrição |
| :--- | :--- |
| `=RF_PU(ticker; taxa; data)` | Preço Unitário do ativo na data à taxa informada. |
| `=RF_TAXA(ticker; pu; data)` | Taxa implícita (% a.a.) dado o preço de mercado. |
| `=RF_DURATION(ticker; taxa; data)` | Duration de Macaulay (anos úteis). |
| `=RF_DV01(ticker; taxa; data)` | Sensibilidade financeira para 1 bp de variação na taxa. |
| `=RF_VNA(ticker; data)` | Valor Nominal Atualizado (corrigido por IPCA se aplicável). |
| `=RF_FLUXO(ticker; taxa; data)` | Tabela completa de fluxos projetados e descontados. |
| `=RF_INFO(ticker; campo)` | Retorna dados cadastrais (EMISSOR, VENCIMENTO, etc). |
| `=RF_LISTAR()` | Lista todos os ativos com dados locais disponíveis. |
| `=RF_YTW(ticker; pu; data)` | Yield to Worst (mínimo entre YTM e YTC). |
| `=RF_DI_CURVA(venc; data)` | Taxa interpolada da curva B3 para o vencimento. |

**Dica:** Use a macro `RF_ATUALIZAR` (Alt+F8) para limpar o cache do Excel após rodar os scripts Python.

---

## 5. Formato dos CSVs (Modelo de Dados)

Os arquivos em `data/fluxos/<TICKER>.csv` usam separador **TAB** e decimal **ponto**.

**IPCA / PRE** — cabeçalho chave-valor + tabela de fluxo:
```
ticker	EGIEA6
tipo	DEB
indexador	IPCA
emissor	ENGIE BRASIL ENERGIA SA
method	IPCA
inicio_rentabilidade	2026-03-13
vencimento	2038-02-15
vne	1000.0
taxa_emissao	6.2474
taxa_ref	6.2474
data_fluxo	2026-06-12
vna	1021.550460
fonte	B3

DATA	FLUXO_TAI	TIPO
2028-02-15	0.1231646600	J
2036-02-15	0.3955515300	J+A

AMORT	2036-02-15	0.33333300
```
`TIPO` = `J` (juros), `A` (amortização) ou `J+A` (ambos na mesma data).
`FLUXO_TAI` = fração do VNA; `AMORT` = % do VNE amortizado nessa data.

**CDI / %CDI** — mesmo cabeçalho + blocos `CDI` por data de cálculo:
```
ticker	XYZEA6
...
data_fluxo	2026-06-13
fonte	B3

CDI	2026-06-13	2026-12-15	105.230000	102.450000	126
```
Campos CDI: `data_calc | data_evento | vf | pv | du` (um bloco por data importada).

O Add-in lê **ambos os formatos** (novo e legado). Para migrar CSVs antigos:
```bash
python scripts/migrar_csvs.py --dry-run   # simulação
python scripts/migrar_csvs.py             # migração efetiva
```

---

## 6. Rebuild do Add-in

Caso o código VBA em `addin/RF_Calc.bas` seja alterado, recompile o Add-in:
```bash
python addin/build_xlam.py
```
O script gera o arquivo `.xlam` limpo, configura o auto-load no Excel e propaga o caminho da pasta de dados.

---
*RF_Calc — Precisão e agilidade na precificação de Renda Fixa.*
