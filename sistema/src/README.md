# src/ — biblioteca Python

Módulos reutilizáveis (importados pelos `scripts/`).

| Arquivo | O que faz |
|---|---|
| `api_client.py` | Autenticação (token cacheado) e chamadas à API CALC: `list_tickers`, `get_bond_details`, `calc_pu_api`, `calc_yield_api` |
| `db.py` | SQLite (`data/rf.db`): `init_db`, `get_conn` e o schema das tabelas |
| `sync_bacen.py` | Baixa CDI (série 12) e IPCA (série 433) do BACEN; usado pela rotina diária |

**Núcleo usado pelo fluxo atual:** `api_client`, `db`, `sync_bacen`.
Os demais módulos (`calc.py`, `vna.py`, `sync_bonds.py`, `sync_flows.py`,
`sync_b3_curve.py`) são do desenho antigo baseado em SQLite e não fazem parte do
fluxo CSV atual — mantidos por enquanto, podem migrar para `_legado/`.
