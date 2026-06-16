# RF_Calc — GUIA COMPLETO (nível: analfabeto digital)

**O que é:** Uma calculadora de renda fixa dentro do Excel. Precifica debêntures, CRIs, CRAs, NTN-B e DI Futuro.

**Como funciona:** Os dados dos ativos ficam em arquivos CSV numa pasta. O Excel lê esses arquivos e calcula preços, taxas, durations, etc.

---

## SUMÁRIO

1. [Pré-requisitos](#1-pré-requisitos)
2. [Estrutura de pastas](#2-estrutura-de-pastas)
3. [Instalação — PRIMEIRA VEZ](#3-instalação--primeira-vez)
4. [Importar os ativos](#4-importar-os-ativos)
5. [Instalar o Add-in no Excel](#5-instalar-o-add-in-no-excel)
6. [Uso diário](#6-uso-diário)
7. [Transferir para outro PC](#7-transferir-para-outro-pc)
8. [Solução de problemas](#8-solução-de-problemas)

---

## 1. PRÉ-REQUISITOS

Você precisa ter instalado no computador:

| Programa | Como verificar | Onde baixar |
|----------|---------------|-------------|
| **Python 3.11+** | Abra o Prompt de Comando e digite `python --version` | https://www.python.org/downloads/ |
| **Excel** (2016 ou mais novo) | Já vem no Office | — |
| **Git** (opcional) | Digite `git --version` no Prompt | https://git-scm.com/download/win |

> ⚠️ **Na instalação do Python, MARQUE a caixa "Add Python to PATH"** (Add Python 3.x to PATH). Se não marcar, os comandos abaixo não funcionarão.

---

## 2. ESTRUTURA DE PASTAS

Após instalar, a pasta do projeto fica assim:

```
Codigo_Fluxo/
├── PASSO_A_PASSO.md           ← VOCÊ ESTÁ AQUI
├── README.md                  ← Visão geral do projeto
├── DOCUMENTACAO_FORMULAS.md   ← Todas as fórmulas com exemplos
├── sistema/
│   ├── config/
│   │   └── tokens.txt         ← SUAS senhas (NÃO compartilhar!)
│   ├── bat/                   ← Scripts .bat para automação
│   │   ├── LEIA_ME.txt
│   │   ├── 1_sincronizar_completo.bat
│   │   ├── 2_sincronizar_rapido.bat
│   │   ├── 3_instalar_addin.bat
│   │   └── 4_validar.bat
│   ├── scripts/
│   │   └── importar_tudo.py   ← Script PRINCIPAL
│   ├── src/                   ← Código-fonte Python
│   ├── addin/                 ← Código VBA do Excel
│   ├── data/
│   │   └── fluxos/            ← PASTA DOS DADOS (CSVs)
│   └── requirements.txt       ← Dependências Python
└── wiki/                      ← Documentação técnica
```

---

## 3. INSTALAÇÃO — PRIMEIRA VEZ

### 3.1 Abra o Prompt de Comando

1. Aperte a tecla **Windows** (⊞) no teclado
2. Digite `cmd`
3. Aperte **Enter**
4. Vai abrir uma janela preta

### 3.2 Navegue até a pasta do projeto

No Prompt de Comando, digite:

```bash
cd "C:\Users\Nitro 5\OneDrive\Documentos\Claude_code\Projeto_calculadora_excel\Codigo_Fluxo\sistema"
```

> 💡 **Dica:** Copie o caminho acima (Ctrl+C), clique com o botão direito na janela preta para colar.

Aperte **Enter**.

### 3.3 Instale as dependências Python

Digite:

```bash
pip install requests pandas openpyxl scipy python-dateutil pywin32
```

Aperte **Enter**. Vai baixar e instalar os pacotes (~2 minutos).

### 3.4 Configure suas senhas (TOKENS)

1. No Explorador de Arquivos, navegue até:
   ```
   Codigo_Fluxo\sistema\config\
   ```

2. Abra o arquivo `tokens_template.txt` com o Bloco de Notas (botão direito → Abrir com → Bloco de Notas)

3. Preencha com seus dados reais:

   ```
   FI_API_KEY=SUA_API_KEY_AQUI
   FI_USER_EMAIL=seu.email@empresa.com
   FI_USER_PASSWORD=sua_senha_aqui
   ```

4. Salve como `tokens.txt` na mesma pasta (Arquivo → Salvar como → Nome: `tokens.txt`)

> ⚠️ **IMPORTANTE:** Nunca envie o arquivo `tokens.txt` para ninguém. Ele contém suas senhas.

### 3.5 Inicialize o banco de dados

No Prompt de Comando (ainda na pasta `sistema`), digite:

```bash
python -c "from src.db import init_db; init_db()"
```

Vai aparecer: `DB inicializado em ...`

### 3.6 Atualize os dados do BACEN

```bash
python -c "from src import sync_bacen; sync_bacen.sync_cdi(); sync_bacen.sync_ipca(); sync_bacen.sync_anbima_ipca_projection()"
```

Isso baixa o CDI e IPCA oficiais (~30 segundos).

---

## 4. IMPORTAR OS ATIVOS

Agora você vai baixar os dados de TODOS os ativos do FI Analytics.

### 4.1 Teste com 5 ativos primeiro

```bash
python scripts/importar_tudo.py --max 5
```

Isso importa 5 ativos para testar (~10 segundos).

Se aparecer `CONCLUIDO: ok=5`, está funcionando!

### 4.2 Importar TUDO (~30-60 minutos)

```bash
python scripts/importar_tudo.py
```

Vai aparecer:

```
[1/4] Atualizando BACEN...
[2/4] Listando bonds do FI Analytics...
  3500 ativos encontrados
[3/4] Importando 3500 ativos...
  [50/3500] ok=45 skip=5 err=0 | ~45min
  ...
[4/4] CONCLUIDO: ok=3400 skip=50 err=50 | 48.2 min
```

> ⏰ Pode demorar até 1 hora. Deixe o computador ligado e conectado à internet.
> 
> 💡 Se quiser parar no meio, aperte **Ctrl+C**. Depois rode de novo — ele pula os que já foram baixados.

### 4.3 Verificar se deu certo

```bash
python scripts/importar_tudo.py --validar 10
```

Isso compara o PU calculado localmente vs FI Analytics para 10 ativos.
O erro deve ser menor que 0,01 (1 centavo).

---

## 5. INSTALAR O ADD-IN NO EXCEL

### 5.1 FECHE o Excel

Se o Excel estiver aberto, feche AGORA. Isso é importante.

### 5.2 Execute o instalador

No Explorador de Arquivos, navegue até:

```
Codigo_Fluxo\sistema\bat\
```

Dê **duplo-clique** em `3_instalar_addin.bat`.

> Se aparecer "O Windows protegeu seu PC", clique em **Mais informações** → **Executar mesmo assim**.

### 5.3 Teste no Excel

1. Abra o Excel
2. Em qualquer célula, digite:
   ```
   =RF_LISTAR()
   ```
3. Aperte Enter

Deve aparecer uma lista de tickers (ex: EGIEA6, VALE33, etc).

### 5.4 Teste um PU

Em outra célula, digite:

```
=RF_PU("EGIEA6";6,5;HOJE())
```

Deve retornar um número (~1400-1500).

---

## 6. USO DIÁRIO

### Todo dia de manhã:

**Opção A — Clique no .bat** (mais fácil):

1. Abra a pasta `Codigo_Fluxo\sistema\bat\`
2. Dê **duplo-clique** em `2_sincronizar_rapido.bat`
3. Aguarde 2-5 minutos
4. Abra o Excel e use normalmente

**Opção B — Agendamento automático**:

```bash
cd "C:\Users\Nitro 5\OneDrive\Documentos\Claude_code\Projeto_calculadora_excel\Codigo_Fluxo\sistema"
python scripts/importar_tudo.py --max 99999
```

> Para agendar no Windows: procure "Agendador de Tarefas" no menu Iniciar.

### Funções do Excel disponíveis:

| Função | Exemplo | Resultado |
|--------|---------|-----------|
| `RF_PU` | `=RF_PU("EGIEA6";6,5;HOJE())` | Preço em R$ |
| `RF_TAXA` | `=RF_TAXA("EGIEA6";1447;HOJE())` | Yield % a.a. |
| `RF_VNA` | `=RF_VNA("EGIEA6";HOJE())` | VNA em R$ |
| `RF_FLUXO` | `=RF_FLUXO("EGIEA6";6,5;HOJE())` | Tabela com %TAI |
| `RF_DURATION` | `=RF_DURATION("EGIEA6";6,5;HOJE())` | Duration anos |
| `RF_DV01` | `=RF_DV01("EGIEA6";6,5;HOJE())` | DV01 em R$ |
| `RF_GROSSUP` | `=RF_GROSSUP("EGIEA6";1447;HOJE())` | Taxa c/ gross-up |
| `RF_LISTAR` | `=RF_LISTAR()` | Lista tickers |

---

## 7. TRANSFERIR PARA OUTRO PC

Se você quiser copiar TUDO para outro computador:

### 7.1 No PC de origem (seu PC atual)

1. Copie a pasta INTEIRA `Codigo_Fluxo` para um pen drive:
   - Abra o Explorador de Arquivos
   - Vá para `C:\Users\Nitro 5\OneDrive\Documentos\Claude_code\Projeto_calculadora_excel\`
   - Clique com botão direito em `Codigo_Fluxo` → **Copiar**
   - Cole no pen drive

2. Copie também a pasta de dados (se for diferente):
   - A pasta `sistema\data\fluxos\` já está dentro de `Codigo_Fluxo`
   - Mas se você configurou uma pasta separada em `tokens.txt`, copie ela também

### 7.2 No PC de destino (PC novo)

1. **Instale o Python 3.11+** (veja seção 1)

2. Cole a pasta `Codigo_Fluxo` em qualquer lugar (ex: `C:\Users\SeuUsuario\Documentos\`)

3. Abra o Prompt de Comando e navegue até a pasta `sistema`:
   ```bash
   cd "C:\Users\SeuUsuario\Documentos\Codigo_Fluxo\sistema"
   ```

4. Instale as dependências:
   ```bash
   pip install requests pandas openpyxl scipy python-dateutil pywin32
   ```

5. Configure o `tokens.txt` (veja seção 3.4)

6. Inicialize o banco:
   ```bash
   python -c "from src.db import init_db; init_db()"
   ```

7. Instale o add-in no Excel (veja seção 5)

8. **PRONTO!** Os dados dos ativos já estão nos CSVs copiados. Não precisa reimportar.

---

## 8. SOLUÇÃO DE PROBLEMAS

### "Python não é reconhecido como comando interno"

- Você não marcou "Add Python to PATH" na instalação
- Solução: Reinstale o Python e **MARQUE A CAIXA**

### "Não foi possível encontrar o módulo requests"

- As dependências não foram instaladas
- Solução: Rode `pip install requests pandas openpyxl scipy python-dateutil pywin32`

### "#N/D no Excel"

- A pasta de fluxos não está acessível
- Solução: Pressione **Alt+F8** no Excel, selecione `RF_ATUALIZAR`, clique **Executar**

### "Erro ao conectar no FI Analytics"

- API key ou email errados no `tokens.txt`
- Solução: Verifique se `tokens.txt` tem os valores corretos

### "VNA=1.0 nos CSVs"

- CSVs antigos com VNA quebrado
- Solução: Rode `python scripts/corrigir_vna_rapido.py`

---

**FIM DO GUIA**

Se tiver dúvidas, volte à seção relevante acima. Todos os comandos podem ser copiados e colados diretamente no Prompt de Comando.
