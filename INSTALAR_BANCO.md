# Como instalar o RF_Calc no PC do Banco

> **Leia isso do começo ao fim antes de fazer qualquer coisa.**
> Tempo total: ~10 minutos. Não precisa de Python, não precisa de permissão de TI.

---

## O que você vai precisar

- Acesso à pasta de rede: `\\bbafswcorp\dpt\dfsl\Denis\addin_rf\`
- Excel instalado (qualquer versão a partir de 2016)
- Conexão com a rede do banco (ou VPN ativa)
- 10 minutos

---

## PASSO 1 — Baixar o projeto do GitHub

1. Abra o navegador (Chrome, Edge, tanto faz)

2. Vá para o endereço:
   ```
   https://github.com/deaucajr/calculadora-rf
   ```

3. Procure o botão verde escrito **`< > Code`** (fica perto do topo da página, lado direito)

4. Clique nele. Vai abrir um menu pequeno.

5. Clique em **`Download ZIP`** (última opção do menu)

6. O arquivo `calculadora-rf-main.zip` vai aparecer na sua barra de downloads.
   Clique em **Salvar** se perguntar onde salvar — pode ser em Documentos.

---

## PASSO 2 — Extrair os arquivos para a pasta da rede

1. Abra o **Explorador de Arquivos** (a pastinha amarela na barra de tarefas)

2. No campo de endereço no topo (onde aparece o caminho), clique nele e apague tudo.
   Digite exatamente isso e pressione Enter:
   ```
   \\bbafswcorp\dpt\dfsl\Denis\addin_rf
   ```
   A pasta vai abrir. Se der erro de acesso, chame o suporte de rede.

3. Volte para a pasta onde o ZIP foi baixado. Clique com o **botão direito** no arquivo
   `calculadora-rf-main.zip`.

4. Clique em **"Extrair tudo..."** (ou "Extract All...")

5. Na tela que abrir, clique em **Procurar** e navegue até:
   ```
   \\bbafswcorp\dpt\dfsl\Denis\addin_rf
   ```
   Clique em **OK** e depois em **Extrair**.

6. Vai criar uma pasta chamada `calculadora-rf-main` dentro de `addin_rf`.
   Você precisa **mover** o conteúdo para fora dela:
   - Abra a pasta `calculadora-rf-main`
   - Selecione tudo (Ctrl+A)
   - Recorte (Ctrl+X)
   - Volte um nível para `addin_rf`
   - Cole (Ctrl+V)
   - Delete a pasta vazia `calculadora-rf-main`

   > Resultado final: `\\bbafswcorp\dpt\dfsl\Denis\addin_rf\sistema\`, `README.md`, etc.
   > devem estar diretamente dentro de `addin_rf`, não dentro de uma subpasta.

---

## PASSO 3 — Criar a pasta de dados

1. Ainda no Explorador de Arquivos, dentro de `\\bbafswcorp\dpt\dfsl\Denis\addin_rf\`:

2. Clique com o **botão direito** em um espaço vazio → **Novo** → **Pasta**

3. Dê o nome: `fluxos`

4. Pronto. A pasta `\\bbafswcorp\dpt\dfsl\Denis\addin_rf\fluxos\` vai ficar vazia por enquanto
   (os dados serão copiados no Passo 5).

---

## PASSO 4 — Instalar o add-in no Excel

1. **Certifique-se de que o Excel está FECHADO.** Isso é importante. Se estiver aberto,
   feche agora.

2. No Explorador de Arquivos, navegue até:
   ```
   \\bbafswcorp\dpt\dfsl\Denis\addin_rf\sistema\dist\
   ```

3. Você vai ver os seguintes arquivos:
   - `instalar.bat`  ← **É ESTE que você vai clicar**
   - `instalar.ps1`
   - `RF_Calc.xlam`
   - `rf_fluxos_dir.txt`

4. Dê **duplo-clique** em `instalar.bat`.

5. Vai abrir uma janela preta (Prompt de Comando / PowerShell). Não feche ela.

6. O instalador vai fazer tudo sozinho. Aguarde até aparecer:
   ```
   PRONTO. Feche e abra o Excel: as funcoes RF_* carregam sozinhas.
   ```

7. Se aparecer um aviso de segurança do Windows perguntando se você quer executar
   o arquivo, clique em **Executar** ou **Sim** ou **Permitir** (qualquer um que libere).

8. Pressione qualquer tecla para fechar a janela preta.

---

## PASSO 5 — Copiar os dados de fluxos

Os arquivos CSV com os dados dos ativos ficam no seu PC de casa (na pasta de dados local).
Você precisa copiá-los para a pasta da rede do banco.

**No seu PC de casa:**

1. Abra o Explorador de Arquivos

2. Navegue até a pasta onde estão seus dados. O caminho padrão é algo como:
   ```
   C:\Users\[SEU_USUARIO]\OneDrive\Documentos\Claude_code\Projeto_calculadora_excel\
   Codigo_Fluxo\sistema\data\fluxos\
   ```

3. Selecione **tudo** dentro dessa pasta (Ctrl+A)

4. Copie (Ctrl+C)

5. Navegue até a pasta da rede:
   ```
   \\bbafswcorp\dpt\dfsl\Denis\addin_rf\fluxos\
   ```

6. Cole (Ctrl+V). Pode levar alguns minutos dependendo da velocidade da rede.

> **Dica:** Depois disso, sempre que rodar o `rotina_diaria.py` no PC de casa,
> configure-o para salvar direto na pasta de rede. Assim os dados ficam sempre atualizados
> no banco sem precisar copiar manualmente toda vez.

---

## PASSO 6 — Testar no Excel

1. Abra o Excel

2. Abra qualquer planilha em branco

3. Clique em uma célula (ex: A1)

4. Digite exatamente isso e pressione Enter:
   ```
   =RF_LISTAR()
   ```

5. Se aparecer uma lista de tickers (ex: EGIEA6, VALE23, etc.) → **funcionou!**

6. Teste uma função de preço. Numa célula vazia, digite:
   ```
   =RF_PU("EGIEA6";6,5;HOJE())
   ```
   Deve retornar um número em torno de 1400-1500.

7. Teste uma função de swap. Digite:
   ```
   =RF_CDI_PARA_IPCA(2;13,5;5,2)
   ```
   Deve retornar aproximadamente `10,05`.

---

## Se algo der errado

### "O add-in não carrega / funções RF_ não aparecem"

1. Abra o Excel
2. Vá em **Arquivo** → **Opções** → **Suplementos**
3. Na parte de baixo onde diz "Gerenciar: Suplementos do Excel", clique em **Ir...**
4. Procure **RF_Calc** na lista e marque a caixinha do lado
5. Clique em **OK**
6. Feche e reabra o Excel

### "#N/D ou #N/A em todas as funções"

Os arquivos CSV não foram encontrados. Verifique:
- A pasta `\\bbafswcorp\dpt\dfsl\Denis\addin_rf\fluxos\` existe e tem arquivos .csv
- A VPN / rede do banco está conectada
- No Excel, pressione **Alt+F8**, selecione **RF_ATUALIZAR**, clique em **Executar**

### "Aviso de segurança ao abrir o add-in"

1. Vá em **Arquivo** → **Opções** → **Central de Confiabilidade** → **Configurações...**
2. Clique em **Locais Confiáveis**
3. Clique em **Adicionar novo local**
4. Em "Caminho", coloque: `\\bbafswcorp\dpt\dfsl\Denis\addin_rf\sistema\dist\`
5. Marque **"As subpastas deste local também são confiáveis"**
6. Clique em **OK** em tudo
7. Feche e reabra o Excel

### "O instalar.bat não roda / diz 'acesso negado'"

1. Clique com o **botão direito** em `instalar.bat`
2. Clique em **"Executar como administrador"**
3. Se ainda der erro, fale com o suporte de TI para liberar execução de scripts PowerShell.

---

## Atualização futura (quando houver nova versão)

1. Vá em `https://github.com/deaucajr/calculadora-rf`
2. Baixe o ZIP de novo (Passo 1)
3. **Feche o Excel**
4. Extraia e substitua os arquivos em `\\bbafswcorp\dpt\dfsl\Denis\addin_rf\`
   (pode dizer "Sim para todos" quando perguntar sobre sobrescrever)
5. Dê duplo-clique em `instalar.bat` de novo
6. Reabra o Excel

---

*RF_Calc — Calculadora de Renda Fixa  |  github.com/deaucajr/calculadora-rf*
