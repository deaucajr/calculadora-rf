# addin/ — add-in Excel

| Arquivo | O que é |
|---|---|
| `RF_Calc.bas` | Código-fonte VBA do add-in (funções `RF_PU`, `RF_TAXA`, `RF_DURATION`, `RF_DV01`, `RF_VNA`, `RF_FLUXO`, `RF_INFO`, `RF_LISTAR`). **Fonte de verdade do add-in** — edite aqui, nunca dentro do `.xlam`. |
| `build_xlam.py` | Gera `RF_Calc.xlam` limpo (importa o `.bas` via COM), registra o auto-load no Excel. |

## Gerar/atualizar o add-in

```powershell
python addin/build_xlam.py
```
Pré-requisitos: Excel **fechado** e "Confiar no acesso ao modelo de objeto de projeto do
VBA" habilitado (o script avisa se faltar; reverta depois por segurança). O `.xlam` vai
para `%APPDATA%\Microsoft\AddIns\` e carrega sozinho ao abrir o Excel.

**Importante:** o caminho da pasta de dados (`FLUXOS_DIR`) está hardcoded no `.bas`.
Ajuste-o ao mover o projeto e regenere. Nunca abra o `.xlam` instalado por File→Open
(cria cópia duplicada que trava); para editar, mexa no `.bas` e regenere.

Referência das fórmulas: [`../docs/REFERENCIA.md`](../docs/REFERENCIA.md).
