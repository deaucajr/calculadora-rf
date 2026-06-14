# Calculadora de Renda Fixa (RF_Calc)

Sistema para **precificar localmente** debêntures, CRIs e CRAs (IPCA, PRÉ, CDI+spread e %CDI)
sem bater na API a cada consulta. Os fluxos de caixa são baixados uma vez da
[calculadorarendafixa.com.br](https://calculadorarendafixa.com.br) (CALC/B3) e o cálculo
roda offline — em Python ou direto no **Excel** via add-in com funções `RF_*`.

Validado contra a API: **80/80** (5 papéis de cada tipo × 4 datas) batendo até ~1e-5.

## Estrutura

```
.
├── src/         # biblioteca Python: api_client, db, sync_bacen, ...
├── scripts/     # executaveis: importar, importar_todos, rotina_diaria, validar, ...
├── addin/       # add-in Excel: RF_Calc.bas + build_xlam.py
├── docs/        # documentacao (arquitetura, referencia das formulas)
├── data/        # GERADO (gitignored): rf.db, fluxos/*.csv, _cdi.csv, _feriados.csv
├── _legado/     # versoes antigas (dashboard, CLI, xlwings) — referencia historica
├── config.json  # GITIGNORED — ajustes (base_url, BACEN, fluxos_dir, ...)
├── credenciais.txt # GITIGNORED — login/senha da CALC (so p/ importar fluxos)
└── requirements.txt
```

### Onde ficam os CSV de fluxo (`fluxos_dir`)

Por padrão, em `data/fluxos/`. Para apontar para **outra pasta sua** (inclusive na
nuvem, ex. OneDrive/Dropbox), defina `"fluxos_dir"` no `config.json` — vale para os
scripts **e** para o add-in (rode `build_xlam.py`/`setup.py` de novo após mudar):

```json
{ "fluxos_dir": "C:/Users/voce/OneDrive/RF/fluxos" }
```
Em branco (`""`) usa o padrão `data/fluxos/`. Assim, quem clonar o código aponta para
a própria pasta sem editar nada no código.

## Instalação — comando único

Depois de clonar o repositório, com o **Excel fechado**, rode **um** comando:

```powershell
cd sistema
python setup.py
```
(ou dê **duplo-clique em `setup.bat`**)

Isso faz tudo sozinho: instala dependências, cria o banco, gera o calendário de
feriados, baixa o **CDI** (BACEN) e a **curva DI×Pré da B3** (`data/fluxos/_curva_di.csv`)
e constrói/instala o add-in `RF_Calc.xlam`. Reabra o Excel e use as funções `RF_*`.

Os dados públicos (feriados, CDI, curva B3) já bastam para o add-in calcular. Para
baixar também os **fluxos de cada ativo** (precisa de login/senha da CALC), coloque
suas credenciais num txt simples e rode uma vez:

```powershell
ren credenciais.txt.exemplo credenciais.txt   # depois edite login/senha nele
python setup.py --importar
```

> O `credenciais.txt` é lido na hora do import e **não vai para o git** (está no
> `.gitignore`). Ele tem prioridade sobre o `config.json`, então o login/senha fica
> só nesse txt — não precisa colocar credenciais no `config.json`.

<details><summary>Instalação manual (passo a passo)</summary>

```powershell
pip install -r requirements.txt
copy config.example.json config.json               # ajustes (base_url, BACEN, ...)
ren credenciais.txt.exemplo credenciais.txt        # login/senha da CALC (so p/ import)
python scripts/importar_fluxos.py --feriados      # gera data/fluxos/_feriados.csv
python -m src.sync_b3_curve                        # baixa a curva DI x Pre da B3
python addin/build_xlam.py                         # gera o .xlam
```
</details>

## Uso

```powershell
# importar 1 ativo (numa data; CDI acumula multiplas datas)
python scripts/importar_fluxos.py EGIEA6 2026-06-12

# importar TODOS da B3 (deb+cri+cra; resume + delays)
python scripts/importar_todos.py

# CONFERIR se todo o universo da CALC/B3 esta cadastrado no seu PC
python scripts/verificar_cadastro.py            # so relata o que falta
python scripts/verificar_cadastro.py --baixar   # baixa SO os que faltam

# DETECTAR fluxos que mudaram (sem re-importar tudo; usa so getbonddetails,
# por rodizio em lotes -> poucas chamadas por execucao)
python scripts/verificar_mudancas.py            # checa um lote e relata mudancas
python scripts/verificar_mudancas.py --atualizar # re-importa SO os que mudaram
python scripts/verificar_mudancas.py --todos    # varre tudo de uma vez (pesado)

# corrigir classificacao IPCA/CDI sem API (apos importacao em massa)
python scripts/corrigir_csvs.py

# validar contra a API (5 de cada tipo x 4 datas)
python scripts/validar.py

# rotina diaria (LEVE por padrao: CDI+curva publicos + ativos novos + refresh
# mensal de IPCA so quando sai mes novo + rodizio de mudanca de fluxo)
python scripts/rotina_diaria.py            # leve (recomendada no dia a dia)
python scripts/rotina_diaria.py --completo # re-importa TODOS p/ hoje (pesado; raro)
python scripts/rotina_diaria.py --agendar  # agenda a leve (7h30, dias uteis)
```

### Add-in Excel

```powershell
python addin/build_xlam.py   # gera RF_Calc.xlam em %APPDATA%\Microsoft\AddIns e registra auto-load
```
Requer "Confiar no acesso ao modelo de objeto VBA" habilitado temporariamente
(o script avisa). No Excel as funções carregam sozinhas. Veja `docs/REFERENCIA.md`.

**Funções disponíveis** (taxa em % a.a.; data obrigatória onde se aplica):
`RF_PU` · `RF_TAXA` · `RF_DURATION` · `RF_DV01` · `RF_CONVEXIDADE` · `RF_VNA` ·
`RF_FLUXO` · `RF_VENCIMENTO(ticker)` · `RF_ATUALIZADO_EM(ticker)` (data do último
import) · `RF_PROXIMO_EVENTO(ticker,data)` · `RF_SPREAD(ticker)` (spread/%CDI/taxa
de referência) · `RF_INFO(ticker,campo)` · `RF_LISTAR()`.

> **Caminho dos dados no add-in**: o `build_xlam.py` reescreve automaticamente a
> constante `FLUXOS_DIR` para a pasta `data/fluxos/` desta máquina no momento do build.
> Ao mover o projeto ou clonar em outra máquina, basta rodar o `setup.py` (ou
> `build_xlam.py`) de novo — não precisa editar o `.bas`.

## Como funciona (resumo)

- **IPCA/PRÉ**: `PU = [Σ FC%/(1+taxa)^(du/252)] × VNA(data)`. FC% independe da data → 1 download serve para qualquer taxa/data.
- **CDI+spread**: ajuste de spread sobre o PV salvo.
- **%CDI (DI-PERC)**: reconstrói a **curva DI implícita** (`FD = VF/PV`) de cada papel e reprecifica — exato, sem baixar curva externa.

Detalhes completos em [`docs/arquitetura.md`](docs/arquitetura.md).

## Aviso

As credenciais ficam em `credenciais.txt` (login/senha da CALC) — está no `.gitignore`,
preenchido à mão, **fora** do `config.json`. A pasta `data/` é regenerável e também não
é versionada. Seja moderado no volume de chamadas à API.
