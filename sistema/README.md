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
├── config.json  # GITIGNORED — credenciais da API (copie de config.example.json)
└── requirements.txt
```

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
baixar também os **fluxos de cada ativo** (precisa de `config.json` com login/senha da
CALC), rode uma vez:

```powershell
copy config.example.json config.json   # edite com seu login/senha
python setup.py --importar
```

<details><summary>Instalação manual (passo a passo)</summary>

```powershell
pip install -r requirements.txt
copy config.example.json config.json   # edite com seu login/senha da CALC
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

# corrigir classificacao IPCA/CDI sem API (apos importacao em massa)
python scripts/corrigir_csvs.py

# validar contra a API (5 de cada tipo x 4 datas)
python scripts/validar.py

# rotina diaria (agendavel no Windows): novos ativos + atualiza + CDI
python scripts/rotina_diaria.py --agendar
```

### Add-in Excel

```powershell
python addin/build_xlam.py   # gera RF_Calc.xlam em %APPDATA%\Microsoft\AddIns e registra auto-load
```
Requer "Confiar no acesso ao modelo de objeto VBA" habilitado temporariamente
(o script avisa). No Excel as funções carregam sozinhas. Veja `docs/REFERENCIA.md`.

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

`config.json` contém credenciais — está no `.gitignore`. A pasta `data/` é regenerável
e também não é versionada. Seja moderado no volume de chamadas à API.
