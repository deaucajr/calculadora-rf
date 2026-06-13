# scripts/ — executáveis

Rode da raiz do projeto: `python scripts/<nome>.py`.

| Script | Função |
|---|---|
| `importar_fluxos.py` | Importa 1 ticker → `data/fluxos/<TICKER>.csv`. Também `--feriados` gera o calendário. CDI acumula 1 bloco por data. |
| `importar_todos.py` | Importação em massa (deb+cri+cra). Resume (pula os já feitos hoje), delays, log. |
| `corrigir_csvs.py` | Conserta classificação IPCA/CDI **sem API** (detecta DI-SPREAD mascarado de IPCA). Rode após a importação em massa. |
| `validar.py` | Compara cálculo local vs API (5 de cada tipo × 4 datas). Replica a lógica do add-in em Python. |
| `rotina_diaria.py` | Detecta ativos novos + atualiza + CDI. `--agendar` cria a tarefa no Windows (7h30 seg-sex). |
| `keep_awake.py` | Impede o PC de hibernar enquanto roda (útil em jobs longos). |

`importar_fluxos.py` também é **biblioteca** (os outros importam suas funções:
`importar_ticker`, `gerar_feriados`, `_iso`).
