# Instalar o RF_Calc no trabalho (sem Python, sem Claude)

Este guia deixa qualquer colega usando o add-in `RF_Calc` no Excel **apertando um
botão**. O add-in lê os fluxos de uma **pasta compartilhada** (rede ou OneDrive),
resolvida em **tempo de execução** — então o mesmo `.xlam` funciona em qualquer
máquina, sem recompilar.

---

## Onde guardar os dados (escolha do caminho)

| Opção | Caminho | Quebra o add-in? | Recomendação |
|---|---|---|---|
| **Pasta de rede (UNC)** | `\\servidor\rendafixa\fluxos` | Não | ✅ **Preferida** |
| OneDrive / SharePoint | `C:\Users\voce\OneDrive - Empresa\...\fluxos` | Pode (arquivos "online-only") | ⚠️ Use com pin |
| Cópia local por máquina | `C:\RendaFixa\fluxos` | Não | Ok, mas precisa sincronizar |

**Por que rede (UNC) é a mais segura:**
- O caminho é **idêntico para todos** (no OneDrive ele muda por usuário).
- Não existe o problema de "arquivo online-only / baixar sob demanda" que pode
  fazer a leitura falhar — arquivo de rede é lido direto.
- Um único `rf_fluxos_dir.txt` (commitado) serve para todo mundo.

**Se for OneDrive:** o instalador roda `attrib +P` na pasta para **fixar os
arquivos** (sempre disponíveis offline), evitando o placeholder que quebra o
add-in. Mesmo assim, como o caminho muda por usuário, o instalador pergunta o
caminho a cada colega.

---

## Para o DONO (uma vez)

> **Você escreve a pasta UMA vez, em `sistema/config.json` → `"fluxos_dir"`.**
> Esse é o único lugar: vale para os scripts (gravar/ler) **e** o add-in — o
> `build_xlam` propaga o caminho para onde o add-in lê (`rf_fluxos.txt` desta
> máquina e `dist/rf_fluxos_dir.txt` para os colegas).

1. **Copie a pasta `data/fluxos/`** (os `.csv`, incluindo `_feriados.csv`,
   `_cdi.csv`, `_curva_di.csv`) para a pasta de rede, ex.: `\\servidor\rendafixa\fluxos`.
2. **Defina o caminho oficial** em `sistema/config.json`:
   ```json
   { "fluxos_dir": "\\\\servidor\\rendafixa\\fluxos" }
   ```
   (deixe `""` para usar o padrão local `data/fluxos`).
3. **Gere o add-in distribuível** (com Excel e Python, só você precisa disso):
   ```powershell
   cd sistema
   python addin\build_xlam.py     # gera dist/RF_Calc.xlam E propaga o caminho
   git add sistema/dist/RF_Calc.xlam sistema/dist/rf_fluxos_dir.txt sistema/config.json
   git commit -m "Atualiza add-in distribuivel" && git push
   ```
   Refaça sempre que mudar a lógica do `.bas` ou o caminho dos dados.
4. **Mantenha os dados atualizados** (rotina leve, ~1×/dia) — grava na pasta do
   `config.json`:
   ```powershell
   python sistema\scripts\rotina_diaria.py
   ```

## Para os COLEGAS (uma vez, sem Python)

1. Baixe o repositório do GitHub (botão **Code → Download ZIP**, ou `git clone`).
2. Abra a pasta `sistema/dist/`.
3. **Feche o Excel** e dê **duplo-clique em `instalar.bat`**.
   - Se pedir, cole o caminho da pasta de fluxos (a **mesma** pasta de rede do time).
   - O instalador cria as pastas irmãs `fluxos_manual/` e `fluxos_antigo/`.
4. Abra o Excel e teste numa célula: `=RF_LISTAR()`.

Pronto — as funções `RF_*` carregam sozinhas toda vez que o Excel abrir.

> **Pasta compartilhada (importante):** todos apontam para a **mesma** pasta. Quem
> baixa os dados (o dono) atualiza uma vez e **todos enxergam** — os colegas só leem,
> **não rodam scripts nem batem na API**. E as rotinas de atualização **pulam o que
> já está na pasta** (resume), então o mesmo dado nunca é baixado duas vezes.

---

## Como o add-in acha os dados (precedência)

1. Variável de ambiente `RF_FLUXOS_DIR` (se existir).
2. Arquivo `%APPDATA%\Microsoft\AddIns\rf_fluxos.txt` (escrito pelo instalador).
3. Caminho default embutido (fallback).

## Problemas comuns

- **`#N/D` / `#NUM!` em tudo:** a pasta de fluxos não está acessível (rede/VPN
  desligada, ou OneDrive ainda baixando). Confirme o acesso e, no Excel, rode a
  macro `RF_ATUALIZAR` (Alt+F8) para limpar o cache.
- **Mudou o caminho dos dados:** edite `%APPDATA%\Microsoft\AddIns\rf_fluxos.txt`
  e rode `RF_ATUALIZAR` (ou reabra o Excel).
- **Add-in não aparece:** Arquivo → Opções → Suplementos → Gerenciar "Suplementos
  do Excel" → garanta que `RF_Calc` está marcado.
