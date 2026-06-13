# data/ — dados gerados (não versionado)

Tudo aqui é **regenerável** a partir da API e do BACEN, por isso está no `.gitignore`
(exceto este README). Ao clonar o repositório, esta pasta vem vazia — popule com os
scripts.

| Conteúdo | Origem |
|---|---|
| `fluxos/<TICKER>.csv` | `scripts/importar_fluxos.py` / `importar_todos.py` — 1 arquivo por ativo |
| `fluxos/_feriados.csv` | `importar_fluxos.py --feriados` |
| `fluxos/_cdi.csv` | `scripts/rotina_diaria.py` (CDI diário do BACEN) |
| `rf.db` | SQLite (CDI/IPCA históricos) via `src/db.py` |
| `universo.json` | lista de tickers da B3 (cache) |
| `*.log`, `*.reg` | logs e backups locais |

### Repovoar do zero
```powershell
python scripts/importar_fluxos.py --feriados
python scripts/importar_todos.py
python scripts/corrigir_csvs.py
```
