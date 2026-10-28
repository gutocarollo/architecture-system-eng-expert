# Evidência de catálogo da Story de arquitetura

Esta análise prepara a publicação de uma Story no projeto FBI. Ela não publicou nem alterou nenhum card. O curso usa MakersHub, Airflow, PostgreSQL e FazGraph como fontes de exemplos; o trabalho material pertence ao repositório `gutocarollo/architecture-system-eng-expert`. A busca padrão Nextra/Pagefind foi acrescentada ao escopo e torna `frontend` uma camada material, junto de `documentation`.

A classificação recomendada é `blocked`. O repositório material não consta no contrato instalado, e nenhum objeto canônico do curso foi confirmado. O contrato permite explicar a lacuna no `Catalog Waiver`, mas a explicação não cria um valor canônico. A Story pode registrar esse bloqueio de catálogo de forma explícita. Esse registro não equivale a uma classificação `verified`, nem prova que o trabalho esteja pronto para implementação.

## O que foi reutilizado

O pacote canônico `jira-fbi` fornece a tabela de campos, o export fixado do FazGraph, o contrato das opções e o gate. Foram lidos integralmente a skill e os onze arquivos obrigatórios de referência, incluindo os dois contratos terminais. O JSON do export foi integralmente parseado; o arquivo `registry-parse-evidence.json` guarda todos os objetos, hashes e contagens. Nenhum campo, opção ou objeto alternativo foi criado.

## Decisões independentes

| Dimensão | Estado | Valores e motivo |
| --- | --- | --- |
| System / Components | not_applicable | Vazio. Os sistemas usados como exemplos não são alterados pelo curso. Nenhum Component canônico representa o curso. |
| Business Contexts | not_applicable | Vazio. A Story entrega ensino de arquitetura, sem alterar produto ou jornada de negócio. |
| Business Capabilities | not_applicable | Vazio. Os exemplos explicam ações de negócio sem alterar essas ações. |
| Affected Repositories | unresolved | Vazio. O remote comprova o alvo real, mas o contrato contém somente cinco repositórios da Faz Capital. |
| Technical Layers | resolved | `documentation` e `frontend`. O conteúdo MDX e a busca padrão Nextra/Pagefind são partes materiais da entrega. |
| Affected Assets | unresolved | Vazio. Nenhum ID canônico do curso foi confirmado. A busca de nome exato retornou zero hits; isso não prova ausência em todas as classes de entidade. |
| Página MakersHub | not_applicable | Vazio. As rotas do curso não são páginas MakersHub. |
| Labels | not_applicable | Vazio. Não há projeção operacional de página MakersHub afetada. |

A nomenclatura de oito decisões no audit é `system`, `businessContexts`, `businessCapabilities`, `repositories`, `technicalLayers`, `affectedAssets`, `page` e `labels`. As seis primeiras são campos de catálogo; página e label registram a projeção operacional independente. `Catalog Version` recebe exatamente `catalog-v4-business-contexts-2026-08-13`; `Catalog Validation Status` recebe `blocked`.

## Campos da Story e preflight restante

A Story usa issue type `10006`, projeto `10003` e descrição ADF em `customfield_10054`. É proibido escrever no campo de sistema `description`. O pacote exige `summary`, `reporter`, `project` e `issuetype` para Story e não define default de assignee ou prioridade. O reporter usa `accountId`. O orquestrador deve resolver requisitos adicionais e defaults contra a metadata viva do CREATE; os IDs de prioridade presentes no pacote são um baseline, não uma decisão atual de prioridade.

O preview fornecido é um exemplo estrutural. Antes de publicar, o orquestrador substitui a descrição pelo texto completo dos requisitos originais, resolve reporter/prioridade/assignee, verifica duplicata por JQL, confere metadata e options ativas, examina reserva de arquivos por cards abertos e executa o gate sobre o payload final. Não há dependência de branch-pai ou card de remoção comprovados nesta análise; por isso não foi inventado Issue Link. Qualquer dependência identificada pelo orquestrador precisa ser escrita e relida conforme o contrato.

## Gate local e seu alcance

Comando executável, a partir do checkout:

```sh
node /Users/augustocarollo/.agents/skills/jira-fbi/scripts/jira-fbi-gate.mjs --input=tasks/architecture-story-2026-10-14/catalog-gate-input.example.json
```

A entrada é um objeto `{tool_name, tool_input: {fields}}`. Os campos multiselect usam objetos `{value: canonicalValue}`; Components usam `{id: jiraComponentId}`; os campos Paragraph usam ADF ou `null` onde permitido. `customfield_10521` contém prosa humana e um único bloco `CATALOG_AUDIT_JSON=` seguido do audit JSON. O audit exige `schema_version`, `issue_key`, `registry_sha256`, `proposal_sha256`, `decisions` e `parent_prior`. O hash de proposta do exemplo é calculado sobre JSON compacto e ordenado de todos os campos antes da inclusão do próprio audit; precisa ser recalculado para o preview final.

O resultado do gate do exemplo foi `allow`. Isso comprova a forma e as regras implementadas do exemplo, não o catálogo completo. O código só valida o estado agregado das duas dimensões de negócio; não recusa `repositories=unresolved` e `affectedAssets=unresolved`. A decisão humana registra essas lacunas no audit e mantém `blocked`.

O caminho `~/.codex/skills/jira-fbi` é um symlink do pacote. A execução literal desse caminho retornou código zero sem stdout ; estou inferindo que o guard de entrada explica o efeito, pois ele compara o caminho de argv com o caminho real de `import.meta.url`. O caminho físico `~/.agents/skills/jira-fbi` executou o gate e produziu a decisão explícita. Nenhum arquivo da skill foi alterado. A ausência de stdout não deve ser aceita como aprovação do gate.

## Segurança e autorização

Esta etapa não leu nem imprimiu credenciais. Nenhuma permissão extra é necessária para os artefatos locais ou para registrar honestamente uma Story com classificação `blocked`. Registrar o novo repositório na autoridade FazGraph ou administrar a opção Jira são mudanças fora deste escopo; exigem autorização do dono e, no Jira, permissão Jira Admin. Um waiver não substitui essas ações.

## Recibos das medições

- [2026-10-14 23:20 UTC] checkout atual — `pwd; git branch --show-current` → `/Users/augustocarollo/.superset/worktrees/architecture-engineer-expert/perfect-citizen-a30f5998`; `perfect-citizen-a30f5998`.
- [2026-10-14 23:20 UTC] checkout atual — `git rev-parse HEAD; git remote -v` → `23d5d158d3a964dceba296296368ec14bcd8970b`; `origin https://github.com/gutocarollo/architecture-system-eng-expert.git`.
- [2026-10-14 23:20 UTC] `/Users/augustocarollo/.codex/skills/jira-fbi/reference/fazgraph-catalog-v4.export.json` — Python `json.loads` + SHA256 dos bytes e JSON ordenado → `770e1b4e13bad6c9eaf0aba6496976c7a95e1043deba55c76620cd85cb4ab6fb`; `8bfdd080b084cd2518b6c118145df7fef7d976ed1d7280971180b52d172d3297`; `contexts 14`; `capabilities 16`; `relations 38`.
- [2026-10-14 23:20 UTC] contrato instalado — leitura de `dimensions.repositories.allowedValues` → `["fazcapital/airflow-dags", "fazcapital/faz-database", "fazcapital/makershub", "fazcapital/salesforce", "fazcapital/scraping"]`.
- [2026-10-14 23:20 UTC] FazGraph MCP — `status({})` → `"status":"ok"`, `"data_dir":"/Users/augustocarollo/Developer.noindex/fazgraph-canonical-v4/data"`, `"graph_source":"full"`, `"source_mode":"built"`, `"graph_mtime_utc":"2026-10-13T03:08:04+00:00"`. A medição do endpoint é atual; o conteúdo do grafo tem o mtime informado.
- [2026-10-14 23:20 UTC] Mac local — Python `Path(...).resolve()` sobre os dois caminhos `Developer/fazgraph-canonical-v4/data` e `Developer.noindex/fazgraph-canonical-v4/data` → ambos `/Users/augustocarollo/Developer.noindex/fazgraph-canonical-v4/data`, `exists=True`.
- [2026-10-14 23:20 UTC] FazGraph MCP — `search({q:"architecture-system-eng-expert",limit:3})` → `# Busca architecture-system-eng-expert — 0 hit(s)`.
- [2026-10-14 23:20 UTC] FazGraph MCP — `business_catalog({kind:"all",q:"architecture"})` → `"contexts":[],"capabilities":[],"relations":[]`. A consulta é filtrada pelo termo; não é inventário de repositórios.
- [2026-10-14 23:20 UTC] checkout atual, `package.json` — leitura do manifest → `"postbuild": "pagefind --site .next/server/app --output-path public/_pagefind"`; `"pagefind": "1.5.2"`. Esta leitura comprova configuração, sem afirmar sucesso de build ou busca no navegador.
- [2026-10-14 23:20 UTC] gate físico do pacote — comando acima sobre o exemplo → `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"jira-fbi catalog-v4 gate passed"}}`, código `0`.

O manifesto do pacote declara aprovação histórica em 2026-08-14, por decisão explícita do usuário após lacuna medida, e empacotamento `verbatim-byte-copy`. A fonte aprovada histórica é `/Users/augustocarollo/Developer/fazgraph/docs/canonical/_ontology/business-catalog.v4.json`. A análise validou o export fixado e seu manifesto; não alegou que esse caminho histórico seja o checkout canônico atual.
