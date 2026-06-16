# Scripts de Automacao (`bat/`)

Atalhos para as tarefas mais comuns. Execute clicando duas vezes ou via terminal na raiz do projeto.

## `rotina/` — Rodar toda manha

| Arquivo | O que faz | Custo de API |
| --- | --- | --- |
| `atualizar_curva.bat` | Baixa a curva DI/PRE da B3 (endpoint publico) | Gratis |
| `atualizar_ipca.bat` | Atualiza IPCA (BACEN) + projecao ANBIMA | Gratis |

`atualizar_ipca.bat` aceita o argumento `--refresh-ativos` para re-importar a VNA exata dos ativos IPCA+ via API B3 (so quando ha mes novo de IPCA, e consome chamadas pagas).

Sugestao de agendamento diario (Windows Agendador de Tarefas): 9h30 ou apos abertura do mercado.

## `verificar/` — Manutencao e migracao

| Arquivo | O que faz | Custo de API |
| --- | --- | --- |
| `verificar_ativos_b3.bat` | Lista ativos da B3 sem CSV local | Gratis (leitura) |
| `verificar_ativos_b3.bat --baixar` | Cadastra os ativos que faltam | **Pago** (API B3) |
| `migrar_formato_csvs.bat` | Converte CSVs do formato legado para o novo | Gratis |
| `migrar_formato_csvs.bat --dry-run` | Simula a migracao sem alterar arquivos | Gratis |

## Notas

- Nenhum destes scripts usa a API da calculadora B3 para curva/IPCA — esses dados vem de fontes publicas (BACEN e B3 portal).
- Para importar ativos novos manualmente: `python scripts\importar_fluxos.py TICKER`
