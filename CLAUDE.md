# RF_Calc v3 — Projeto Definitivo

**Add-in Excel para precificação de renda fixa brasileira. Fonte: FI Analytics. VNA: cálculo próprio.**

---

## Guia rápido para o LLM

### Se o usuário disser "importar ativos" ou "atualizar dados":
```bash
cd sistema && python scripts/importar_tudo.py
```

### Se o usuário disser "validar" ou "testar":
```bash
cd sistema && python scripts/importar_tudo.py --validar 20
```

### Se o usuário disser "importar um ticker específico":
```bash
cd sistema && python scripts/importar_tudo.py --ticker EGIEA6
```

### Se algo quebrar:
1. Verifique `sistema/config/tokens.txt` — API key e email corretos?
2. Verifique internet — consegue acessar https://endpoint.fi-analytics.com.br?
3. Rode `python -c "from src.db import init_db; init_db()"` para recriar o DB
4. Rode `python scripts/corrigir_vna_rapido.py` se VNA estiver 1.0

---

## Arquitetura

```
FI Analytics (API)                    BACEN (SGS)
      │                                     │
      ├─ getuserbonds (lista bonds)         ├─ CDI diário (série 12)
      ├─ debenturecalculator (fluxos)       ├─ IPCA mensal (série 433)
      └─ cricracalculator (CRIs/CRAs)       └─ ANBIMA Focus (projeções)
      │                                     │
      └──────────┬──────────────────────────┘
                 ▼
         importar_tudo.py
                 │
         ┌───────┴────────┐
         ▼                ▼
   fluxos/*.csv       rf.db (SQLite)
         │
         ▼
   RF_Calc.xlam (VBA) → Excel
```

### Arquivos principais

| Arquivo | Função |
|---------|--------|
| `PASSO_A_PASSO.md` | **GUIA PRINCIPAL** — instruções nível iniciante |
| `DOCUMENTACAO_FORMULAS.md` | Todas as fórmulas com exemplos reais |
| `sistema/scripts/importar_tudo.py` | **SCRIPT PRINCIPAL** — importa tudo do FI Analytics |
| `sistema/src/vna_calc.py` | Cálculo próprio de VNA (IPCA/CDI/PRE) |
| `sistema/src/fi_client.py` | Cliente da API FI Analytics |
| `sistema/src/fmt_br.py` | Formatador brasileiro (; e vírgula) |
| `sistema/addin/RF_Calc.bas` | Código VBA do add-in Excel |
| `sistema/config/tokens.txt` | 🔒 SUAS SENHAS (gitignored) |
| `sistema/bat/` | Scripts .bat de automação |

### ⚠️ Segurança

- `tokens.txt` contém API keys reais — **NUNCA comitar no GitHub**
- `tokens_template.txt` tem valores genéricos — **esse sim vai pro GitHub**
- Nunca hardcode senhas no código Python

### Formato dos CSVs

- Separador: `;` (ponto-e-vírgula — Excel brasileiro)
- Decimal: `,` (vírgula — padrão brasileiro)
- Encoding: UTF-8 com BOM
- Colunas: `DATA;EVENTO;VF;PV;DU;TAI_PCT;AMORT_PCT`

### Pipeline de cálculo

1. **VNA**: calculado do zero desde `inicio_rentabilidade`
   - IPCA: VNE × IPCA_index(emissão, hoje) × (1 - amort_acumulada)
   - CDI+: VNE × CDI_factor(emissão, hoje)
   - %CDI: VNE × CDI_factor ^ (pct/100)
   - PRE: VNE (constante)
2. **PU**: Σ FC_i% / (1+taxa)^(du_i/252) × VNA(data)
3. **Erro alvo**: < 0,00001 vs FI Analytics (5ª-6ª casa decimal)

---

## Estrutura de diretórios

```
/                    ← raiz do vault Obsidian
├── raw/             ← fontes brutas (imutáveis — LLM só lê, nunca edita)
├── wiki/            ← páginas geradas e mantidas pelo LLM
├── CLAUDE.md        ← este arquivo
├── index.md         ← índice de conteúdo (atualizar a cada ingestão)
└── log.md           ← log cronológico append-only (atualizar a cada operação)
```

**raw/** — Coloque aqui: transcrições de reuniões, artigos, relatórios, notas brutas, PDFs convertidos em texto, anotações de clientes. Subpastas livres (ex: `raw/reunioes/`, `raw/artigos/`). Nunca edite esses arquivos.

**wiki/** — Todas as páginas da wiki ficam aqui. Subpastas opcionais por categoria se necessário.

---

## Tipos de página na wiki

| Tipo | Prefixo sugerido | Quando criar |
|------|-----------------|--------------|
| Projeto | `projeto-nome.md` | Novo projeto identificado |
| Cliente | `cliente-nome.md` | Nova empresa/pessoa cliente |
| Competidor | `competidor-nome.md` | Empresa concorrente identificada |
| Decisão | `decisao-YYYY-MM-DD-slug.md` | Decisão estratégica relevante |
| Reunião | `reuniao-YYYY-MM-DD-slug.md` | Reunião importante (sumário) |
| Tema/Conceito | `tema-nome.md` | Conceito que aparece em múltiplas fontes |
| Pessoa | `pessoa-nome.md` | Stakeholder, colega, contato relevante |
| Síntese | `sintese-nome.md` | Análise ou resposta a uma pergunta importante |
| Visão Geral | `visao-geral.md` | Único — estado atual de todo o domínio |

---

## Frontmatter padrão

Todo arquivo em `wiki/` deve começar com:

```yaml
---
tipo: projeto | cliente | competidor | decisao | reuniao | tema | pessoa | sintese | visao-geral
tags: [lista, de, tags]
fontes: [lista de arquivos em raw/ que alimentaram esta página]
atualizado: YYYY-MM-DD
---
```

---

## Convenções de escrita

- Escreva em português.
- Use `[[nome-do-arquivo]]` para links internos entre páginas da wiki (sem extensão `.md`).
- Sempre que mencionar um projeto, cliente, pessoa ou conceito que tem página própria, linke.
- No final de cada página, adicione uma seção `## Conexões` com links para páginas relacionadas.
- Se uma nova fonte contradiz algo já na wiki, marque com `> ⚠️ Contradição: ...` e registre ambas as versões.
- Não invente informação. Se não há fonte, diga "não documentado".

---

## Workflows

### 1. Ingestão de fonte

Quando o usuário disser "ingere [arquivo]" ou "processa [arquivo]":

1. Leia o arquivo em `raw/`.
2. Discuta os pontos principais com o usuário (opcional, dependendo da preferência).
3. Crie ou atualize a página de sumário da fonte em `wiki/` (se for uma reunião, artigo, etc.).
4. Identifique entidades mencionadas (projetos, clientes, pessoas, temas) e atualize ou crie suas páginas.
5. Verifique se algo contradiz páginas existentes.
6. Atualize `index.md` com a nova página (se criada).
7. Adicione entrada em `log.md` com formato: `## [YYYY-MM-DD] ingestão | Título da fonte`.

Uma fonte pode tocar 5–15 páginas. Não pule atualizações.

### 2. Consulta / Query

Quando o usuário fizer uma pergunta sobre o conteúdo:

1. Leia `index.md` para identificar páginas relevantes.
2. Leia as páginas identificadas.
3. Sintetize a resposta com citações às páginas wiki.
4. Se a resposta for valiosa, **arquive-a** como uma nova página `sintese-slug.md` e registre no `index.md` e `log.md`.

### 3. Lint / Health Check

Quando o usuário pedir "lint" ou "health check da wiki":

Verifique:
- Páginas sem inbound links (órfãs)
- Contradições não resolvidas
- Frontmatter incompleto
- Entidades mencionadas sem página própria
- Seções `## Conexões` ausentes
- `index.md` desatualizado

Produza uma lista de problemas e proponha correções. Não altere nada sem confirmar com o usuário.

---

## Regras de atualização do index.md

- Uma linha por página: `- [[nome-arquivo]] — descrição em uma frase (tipo)`
- Organizar por categoria: Projetos, Clientes, Competidores, Temas, Pessoas, Decisões, Sínteses, Outros
- Atualizar sempre que uma página for criada ou renomeada
- Nunca remover entradas sem verificar se a página foi deletada

## Regras de atualização do log.md

- Append-only: nunca edite entradas passadas
- Formato de cabeçalho: `## [YYYY-MM-DD] tipo | descrição`
- Tipos válidos: `ingestão`, `consulta`, `lint`, `criação`, `atualização`
- Breve: 3–5 linhas por entrada descrevendo o que foi feito

---

## Estado inicial

Wiki criada em 2026-06-12. Nenhuma fonte ingerida ainda.
Próximos passos sugeridos:
1. Coloque o primeiro documento em `raw/` e peça "ingere [nome do arquivo]".
2. Ou comece criando manualmente uma página `visao-geral.md` com o contexto do seu negócio.

---

# Usando a CLI do Gemini para Análise de Grandes Bases de Código

Ao analisar grandes bases de código ou múltiplos arquivos que podem exceder os limites de contexto, use a CLI do Gemini com sua enorme
janela de contexto. Use `gemini -p` para aproveitar a grande capacidade de contexto do Google Gemini.

## Sintaxe de Inclusão de Arquivos e Diretórios

Use a sintaxe `@` para incluir arquivos e diretórios em seus prompts do Gemini. Os caminhos devem ser relativos a ONDE você executa o
comando gemini:

### Exemplos:

**Análise de um único arquivo:**
```
gemini -p "@src/main.py Explique o propósito e a estrutura deste arquivo"
```

**Múltiplos arquivos:**
```
gemini -p "@package.json @src/index.js Analise as dependências usadas no código"
```

**Diretório inteiro:**
```
gemini -p "@src/ Resuma a arquitetura desta base de código"
```

**Múltiplos diretórios:**
```
gemini -p "@src/ @tests/ Analise a cobertura de testes para o código fonte"
```

**Diretório atual e subdiretórios:**
```
gemini -p "@./ Me dê uma visão geral de todo este projeto"
```

**Ou use a flag --all_files:**
```
gemini --all_files -p "Analise a estrutura e as dependências do projeto"
```

## Exemplos de Verificação de Implementação

**Verifique se um recurso foi implementado:**
```
gemini -p "@src/ @lib/ O modo escuro foi implementado nesta base de código? Mostre-me os arquivos e funções relevantes"
```

**Verifique a implementação da autenticação:**
```
gemini -p "@src/ @middleware/ A autenticação JWT foi implementada? Liste todos os endpoints e middleware relacionados à autenticação"
```

**Verifique padrões específicos:**
```
gemini -p "@src/ Existem React hooks que lidam com conexões WebSocket? Liste-os com os caminhos dos arquivos"
```

**Verifique o tratamento de erros:**
```
gemini -p "@src/ @api/ O tratamento de erros adequado foi implementado para todos os endpoints da API? Mostre exemplos de blocos try-catch"
```

**Verifique a limitação de taxa:**
```
gemini -p "@backend/ @middleware/ A limitação de taxa foi implementada para a API? Mostre os detalhes da implementação"
```

**Verifique a estratégia de cache:**
```
gemini -p "@src/ @lib/ @services/ O cache Redis foi implementado? Liste todas as funções relacionadas ao cache e seu uso"
```

**Verifique medidas de segurança específicas:**
```
gemini -p "@src/ @api/ As proteções contra injeção de SQL foram implementadas? Mostre como as entradas do usuário são sanitizadas"
```

**Verifique a cobertura de testes para recursos:**
```
gemini -p "@src/payment/ @tests/ O módulo de processamento de pagamentos está totalmente testado? Liste todos os casos de teste"
```

## Quando usar a CLI do Gemini

Use `gemini -p` quando:
- Analisar bases de código inteiras ou diretórios grandes
- Comparar múltiplos arquivos grandes
- Precisar entender padrões ou arquitetura em todo o projeto
- A janela de contexto atual for insuficiente para a tarefa
- Trabalhar com arquivos totalizando mais de 100KB
- Verificar se recursos, padrões ou medidas de segurança específicos foram implementados
- Verificar a presença de certos padrões de codificação em toda a base de código

## Notas Importantes

- Os caminhos na sintaxe `@` são relativos ao seu diretório de trabalho atual ao invocar o gemini
- A CLI incluirá o conteúdo dos arquivos diretamente no contexto
- Não há necessidade da flag `--yolo` para análise somente leitura
- A janela de contexto do Gemini pode lidar com bases de código inteiras que iriam sobrecarregar o contexto do Claude
- Ao verificar implementações, seja específico sobre o que você está procurando para obter resultados precisos
