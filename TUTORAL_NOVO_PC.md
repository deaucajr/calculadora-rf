# COPIAR TUDO PARA UM COMPUTADOR NOVO — GUIA COMPLETO

**Público-alvo:** Pessoa que NUNCA usou Python, nunca mexeu com prompt de comando, e quer ter exatamente a mesma calculadora de renda fixa funcionando em outro PC.

**Tempo estimado:** 20 minutos (fora a importação dos ativos que pode levar ~1h)

---

## ANTES DE COMEÇAR

Você vai precisar de:
- O arquivo `RF_Calc_PORTABLE.zip` (está na pasta do projeto)
- Internet no PC novo (só para baixar Python e importar os ativos)

---

## PASSO 1 — COPIAR O ARQUIVO .ZIP PARA O PC NOVO

### 1.1

Pegue o arquivo `RF_Calc_PORTABLE.zip`. Ele está em:

```
C:\Users\Nitro 5\OneDrive\Documentos\Claude_code\Projeto_calculadora_excel\Codigo_Fluxo\RF_Calc_PORTABLE.zip
```

### 1.2

Copie esse arquivo para o PC novo. Pode ser por:
- Pen drive (recomendado)
- Email (envie para você mesmo)
- OneDrive / Google Drive
- WhatsApp Web

### 1.3

No PC novo, cole o arquivo na pasta `Documentos`:

1. Abra o **Explorador de Arquivos** (ícone da pastinha amarela na barra de tarefas)
2. Clique em **Documentos** no menu da esquerda
3. Cole o arquivo `RF_Calc_PORTABLE.zip` aqui (Ctrl+V)

---

## PASSO 2 — EXTRAIR O .ZIP

### 2.1

Dentro da pasta Documentos, clique com o **botão DIREITO** do mouse em cima de `RF_Calc_PORTABLE.zip`.

### 2.2

No menu que aparecer, clique em **"Extrair Tudo..."** (ou "Extract All...").

### 2.3

Vai abrir uma janela. Clique no botão **"Extrair"** (ou "Extract").

### 2.4

Vai aparecer uma pasta nova chamada `Codigo_Fluxo`. É aqui que está tudo.

---

## PASSO 3 — INSTALAR O PYTHON

### 3.1

Abra o navegador de internet (Chrome, Edge, Firefox, qualquer um).

### 3.2

Na barra de endereço (onde você digita sites), escreva:

```
python.org
```

Aperte **Enter**.

### 3.3

Vai abrir o site do Python. Procure um botão amarelo escrito **"Download Python 3.x.x"** (os números podem variar). Clique nele.

### 3.4

Vai baixar um arquivo chamado `python-3.x.x-amd64.exe`. Quando terminar o download:

### 3.5

Clique no arquivo baixado (pode estar no canto inferior do navegador ou na pasta Downloads).

### 3.6

**🚨 MUITO IMPORTANTE — NÃO PULE ESTA ETAPA 🚨**

Na primeira tela da instalação, tem uma caixinha de seleção (checkbox) escrito:

```
☐ Add Python 3.x to PATH
```

**MARQUE essa caixinha!** Clique nela para aparecer o ✓.

Se você não marcar, NADA vai funcionar depois.

### 3.7

Depois de marcar a caixinha, clique em **"Install Now"** (Instalar Agora).

### 3.8

Aguarde a instalação terminar (barra verde). Quando terminar, clique em **"Close"**.

---

## PASSO 4 — INSTALAR AS DEPENDÊNCIAS

### 4.1

Abra o **Prompt de Comando**:

1. Aperte a tecla **Windows** (⊞) — fica entre o Ctrl e o Alt, no canto inferior esquerdo do teclado
2. Comece a digitar: `cmd`
3. Vai aparecer "Prompt de Comando". Clique nele.
4. Abre uma janela preta com letras brancas

### 4.2

Na janela preta, digite exatamente o comando abaixo (ou copie e cole):

```bash
cd "%USERPROFILE%\Documents\Codigo_Fluxo\sistema"
```

Aperte **Enter**.

> 💡 Para colar na janela preta: clique com o botão DIREITO do mouse dentro da janela. O texto será colado automaticamente.

### 4.3

Agora digite (ou copie e cole):

```bash
pip install requests pandas openpyxl scipy python-dateutil pywin32
```

Aperte **Enter**.

Vai começar a baixar várias coisas. Vai aparecer um monte de texto branco descendo a tela. Isso é normal. Aguarde até aparecer:

```
Successfully installed ...
```

Pode levar de 1 a 3 minutos.

---

## PASSO 5 — CONFIGURAR OS TOKENS

### 5.1

No Explorador de Arquivos, navegue até:

```
Documentos → Codigo_Fluxo → sistema → config
```

### 5.2

Você vai ver dois arquivos:
- `tokens_template.txt` — modelo genérico
- `tokens.txt` — **já tem seus dados!**

### 5.3

(Opcional) Se quiser verificar se os dados estão corretos:

1. Clique com botão DIREITO em `tokens.txt`
2. **Abrir com** → **Bloco de Notas**
3. Verifique se as linhas estão assim:

```
FI_API_KEY=SUA_API_KEY_AQUI
FI_USER_EMAIL=seu.email@empresa.com
FI_USER_PASSWORD=sua_senha_aqui
```

4. Feche o Bloco de Notas

> ⚠️ **NUNCA** envie este arquivo para ninguém. Ele contém a chave da API.

---

## PASSO 6 — CRIAR O BANCO DE DADOS E BAIXAR CDI/IPCA

### 6.1

Volte para a janela preta (Prompt de Comando). Se você fechou, abra de novo e repita o passo 4.2.

### 6.2

Digite:

```bash
python -c "from src.db import init_db; init_db()"
```

Aperte **Enter**. Vai aparecer:

```
DB inicializado em C:\Users\...\rf.db
```

### 6.3

Agora baixe os dados do BACEN (CDI diário e IPCA mensal):

```bash
python -c "from src import sync_bacen; sync_bacen.sync_cdi(); sync_bacen.sync_ipca(); sync_bacen.sync_anbima_ipca_projection()"
```

Aperte **Enter**. Aguarde ~30 segundos. Vai aparecer algo como:

```
CDI: 4500 registros salvos
IPCA: 280 registros salvos
```

---

## PASSO 7 — IMPORTAR OS ATIVOS

Agora vem a parte mais demorada. Você vai baixar os dados de todos os ativos do FI Analytics.

### 7.1 — TESTE RÁPIDO (5 ativos)

Na janela preta, digite:

```bash
python scripts/importar_tudo.py --max 5
```

Aguarde ~15 segundos. Se aparecer:

```
[4/4] CONCLUIDO: ok=5 skip=0 err=0
```

**Funcionou!** Continue para o próximo passo.

Se aparecer ERRO, veja a seção "PROBLEMAS" no final.

### 7.2 — IMPORTAÇÃO COMPLETA (todos os ativos)

Agora digite:

```bash
python scripts/importar_tudo.py
```

**Isso vai demorar de 30 a 90 minutos**, dependendo da sua internet. Você vai ver algo assim:

```
============================================================
  RF_CALC — IMPORTACAO COMPLETA (FI Analytics)
  Data: 2026-06-15
============================================================

[1/4] Atualizando BACEN (CDI + IPCA + projecoes)...
  OK

[2/4] Listando bonds do FI Analytics...
  3500 ativos encontrados

[3/4] Importando 3500 ativos...
  [50/3500] ok=48 skip=2 err=0 | ~45min restantes
  [100/3500] ok=95 skip=5 err=0 | ~42min restantes
  ...
  [3500/3500] ok=3400 skip=50 err=50 | 0min restantes

[4/4] CONCLUIDO: ok=3400 skip=50 err=50 | 48.2 min
```

> ⚠️ **IMPORTANTE:**
> - Não feche a janela preta durante a importação
> - Mantenha o computador conectado à internet
> - Configure o Windows para NÃO hibernar (Iniciar → Configurações → Sistema → Energia → Suspender: Nunca)
> - Se quiser parar no meio, aperte **Ctrl+C**. Quando rodar de novo, ele pula o que já foi baixado.

### 7.3 — VALIDAR

Depois que terminar, teste se os preços estão batendo:

```bash
python scripts/importar_tudo.py --validar 10
```

O ideal é que o erro seja menor que 0,01 (1 centavo). Se aparecer:

```
TICKER          PU_LOCAL      PU_FI        ERRO     STATUS
-----------------------------------------------------------------
EGIEA6         1448.562894  1448.562894  0.00000000 OK
VALE33         1120.345000  1120.345100  0.00010000 OK
...
```

Está funcionando!

---

## PASSO 8 — INSTALAR O ADD-IN NO EXCEL

### 8.1

**FECHE o Excel** se ele estiver aberto. Isso é obrigatório.

### 8.2

No Explorador de Arquivos, navegue até:

```
Documentos → Codigo_Fluxo → sistema → bat
```

### 8.3

Dê **duplo-clique** no arquivo `3_instalar_addin.bat`.

### 8.4

Pode aparecer uma mensagem do Windows: "O Windows protegeu seu PC". Clique em **"Mais informações"** e depois em **"Executar mesmo assim"**.

### 8.5

Aguarde a janela preta terminar. Vai aparecer "INSTALAÇÃO CONCLUÍDA". Aperte qualquer tecla para fechar.

### 8.6

Abra o Excel.

### 8.7

Clique em qualquer célula (quadradinho) e digite:

```
=RF_LISTAR()
```

Aperte **Enter**. Deve aparecer uma lista de tickers (tipo EGIEA6, VALE33, etc.).

### 8.8

Teste calcular um preço:

```
=RF_PU("EGIEA6";6,5;HOJE())
```

Deve aparecer um número em torno de 1400-1500.

**PRONTO! 🎉**

---

## PASSO 9 — USO DIÁRIO

### Todo dia de manhã (atualizar os dados):

**Opção FÁCIL:** Vá na pasta `Documentos → Codigo_Fluxo → sistema → bat` e dê duplo-clique em `2_sincronizar_rapido.bat`.

**Opção PROFISSIONAL:** Na janela preta (Prompt de Comando):

```bash
cd "%USERPROFILE%\Documents\Codigo_Fluxo\sistema"
python scripts/importar_tudo.py
```

(Isso só atualiza os ativos novos ou que mudaram. Rápido, ~2-5 min.)

---

## CADASTRAR ATIVOS MANUALMENTE

Use isso para ativos que **não estão no FI Analytics** ou são lançamentos muito recentes.

### Método 1 — Template Excel

#### 1. Gerar o template

Na janela preta:

```bash
cd "%USERPROFILE%\Documents\Codigo_Fluxo\sistema"
python scripts/gerar_template_ativo.py
```

Isso gera o arquivo `data/CADASTRO_ATIVO.xlsx`.

#### 2. Preencher o template

Abra o arquivo no Excel. Você verá 2 abas:

**Aba "Identificacao":** Preencha os campos amarelos:

| Campo | Significado | Exemplo |
|-------|------------|---------|
| Ticker | Código do ativo | `MEU_TICKER` |
| Indexador | IPCA, PRE, CDI+, ou %CDI | `IPCA` |
| Taxa (% a.a.) | Taxa contratual | `7,5` |
| Data de Emissão | Quando foi emitido | `15/04/2024` |
| Data de Vencimento | Quando vence | `15/04/2030` |
| VNE (R$) | Valor Nominal de Emissão | `1000,00` |
| Emissor | Nome da empresa | `EMPRESA EXEMPLO SA` |

**Aba "Fluxo_de_Caixa":** Preencha uma linha para cada pagamento:

| Data | Paga Juros? | % Amortização | Taxa (% a.a.) |
|------|-------------|---------------|---------------|
| 15/04/2025 | S | 0 | 7,5 |
| 15/10/2025 | S | 0 | 7,5 |
| 15/04/2026 | S | 25 | 7,5 |
| 15/10/2026 | S | 25 | 7,5 |
| 15/04/2027 | S | 50 | 7,5 |

- **Data:** Dia do pagamento (formato DD/MM/AAAA)
- **Paga Juros?:** `S` se paga cupom de juros naquela data, `N` se não
- **% Amortização:** Percentual do principal que é pago (0 se não amortiza)
- **Taxa (% a.a.):** Taxa de juros contratual

#### 3. Importar o template

```bash
python scripts/importar_planilha.py data/CADASTRO_ATIVO.xlsx
```

#### 4. Testar no Excel

Abra o Excel e digite:

```
=RF_PU("MEU_TICKER";7,5;HOJE())
```

---

### Método 2 — Inserção rápida via comando

Para ativos simples (PRE, sem amortização, fluxo constante):

```bash
cd "%USERPROFILE%\Documents\Codigo_Fluxo\sistema"
python scripts/inserir_manual.py
```

Siga as instruções na tela (vai pedir ticker, taxa, datas dos pagamentos, etc.).

---

### Método 3 — Criar CSV manualmente

Se você sabe mexer com arquivos, pode criar o CSV direto.

1. Vá até `sistema\data\fluxos_manual\`
2. Crie um arquivo chamado `MEU_TICKER.csv`
3. Escreva no formato:

```
ticker;MEU_TICKER
tipo;MANUAL
indexador;IPCA
emissor;EMPRESA EXEMPLO
method;IPCA
inicio_rentabilidade;2024-04-15
vencimento;2030-04-15
vne;1000,0
taxa_ref;7,5
data_fluxo;2026-06-15
vna;1125,654400
fonte;MANUAL

DATA;EVENTO;VF;PV;DU;TAI_PCT;AMORT_PCT
2026-10-15;J;7,500000;7,200000;85;0,666400;0,000000
2027-04-15;J;7,500000;7,000000;210;0,666400;0,000000
2027-10-15;J;7,500000;6,800000;335;0,666400;0,000000
2028-04-15;JA;257,500000;240,000000;460;0,666400;22,200000
```

> ⚠️ **Importante:**
> - Separador de colunas: `;` (ponto-e-vírgula)
> - Separador decimal: `,` (vírgula)
> - O arquivo precisa ser salvo em UTF-8 com BOM
> - DU = dias úteis entre hoje e a data do evento
> - TAI_PCT = percentual da VNA que é pago como juros
> - AMORT_PCT = percentual da VNA que é pago como amortização

Para calcular DU e TAI_PCT automaticamente a partir de datas e valores, use o template Excel (Método 1).

---

## PROBLEMAS COMUNS

### "Python não é reconhecido"

**Causa:** Você não marcou "Add Python to PATH" na instalação.

**Solução:**
1. Vá em Iniciar → Configurações → Aplicativos
2. Procure "Python" na lista
3. Clique → Modificar
4. Na tela de reparo, marque "Add Python to PATH"
5. Clique em Repair
6. Reinicie o Prompt de Comando

### "Não foi possível encontrar o módulo X"

**Causa:** Dependências não instaladas.

**Solução:** Rode o passo 4.3 novamente:
```bash
pip install requests pandas openpyxl scipy python-dateutil pywin32
```

### "#N/D no Excel"

**Causa:** Pasta de fluxos não encontrada.

**Solução:**
1. Pressione **Alt+F8** no Excel
2. Selecione `RF_ATUALIZAR`
3. Execute

### "Erro ao conectar FI Analytics"

**Causa:** Internet ou token errado.

**Solução:**
1. Verifique se está conectado à internet
2. Confira o arquivo `tokens.txt` (passo 5.3)
3. Teste: abra o navegador e acesse `https://endpoint.fi-analytics.com.br`

### "VNA=1.0 nos arquivos"

**Causa:** Dados antigos com VNA quebrado.

**Solução:**
```bash
cd "%USERPROFILE%\Documents\Codigo_Fluxo\sistema"
python scripts/corrigir_vna_rapido.py
```

---

## RESUMO — COMANDOS MAIS IMPORTANTES

```bash
# Navegar até a pasta do projeto
cd "%USERPROFILE%\Documents\Codigo_Fluxo\sistema"

# Importar TUDO (1a vez, ~1h)
python scripts/importar_tudo.py

# Importar só 5 ativos (teste ~15s)
python scripts/importar_tudo.py --max 5

# Validar preços (20 ativos)
python scripts/importar_tudo.py --validar 20

# Corrigir VNA quebrado
python scripts/corrigir_vna_rapido.py

# Atualizar CDI/IPCA do BACEN
python -c "from src import sync_bacen; sync_bacen.sync_cdi(); sync_bacen.sync_ipca()"

# Criar template para ativo manual
python scripts/gerar_template_ativo.py

# Importar ativo manual
python scripts/importar_planilha.py data/CADASTRO_ATIVO.xlsx
```

---

**FIM DO TUTORIAL**

Copie o arquivo `RF_Calc_PORTABLE.zip` + este tutorial para o PC novo e siga os passos na ordem.
