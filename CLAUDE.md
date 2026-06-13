# Wiki de Negócios — Schema e Instruções para o LLM

Este é o arquivo de configuração da wiki. Leia-o inteiro no início de cada sessão antes de qualquer outra ação.

---

## Propósito

Esta wiki serve como base de conhecimento persistente sobre **negócios e trabalho**: projetos, clientes, decisões, análises competitivas, reuniões, processos e lições aprendidas. O usuário é o curador; o LLM escreve e mantém toda a wiki.

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
