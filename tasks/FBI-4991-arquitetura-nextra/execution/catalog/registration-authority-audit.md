# Autoridade de registro do curso

O repositório existe e é privado. A API oficial do GitHub confirmou `gutocarollo/architecture-system-eng-expert`, repository ID `1417536174`, node ID `R_kgDOVH3irg`, branch padrão `main` e `archived=false`. A identidade do provedor está comprovada; isso não equivale a registro no catálogo FazGraph.

## Composição: o fluxo que já serve para o objeto do curso

`Affected Assets` recebe IDs de entidades canônicas; ele não exige que o tipo da entidade se chame `Asset`. O FazGraph já registra documentos como `Document`, com padrão `doc:<kind>/<slug>`. A proposta usa `doc:architecture/architecture-system-eng-expert` e `kind: document`, seguindo o template e o contrato de perguntas existentes.

O fluxo é: documento autoral em `docs/canonical/operations/architecture-system-eng-expert.md`; geração dos três índices por `scripts/docs/regen_index.py`; leitura por `parser/canonical_docs.py`; inclusão em `Graph.canonical_docs`; resolução por `helpers/ai.py::search_entities` e pela API de documentos. O loader mantém `entity_key=None` quando não existe nó nativo, portanto esse documento não fabrica uma Repository, linhagem de código ou vínculo com tabelas.

O diff concreto está em `asset-document-registration.patch`. O documento tem evidência `partially_verified` e lifecycle `active_candidate`; ele identifica a fonte e explicita que não prova entrega, deploy ou registro de repositório. O parser real aceitou o candidato em diretório temporário dentro desta frente; o renderer real gerou somente os índices do corpus candidato. Esses índices de preview não devem substituir os índices completos.

Não usar `asset:https://github.com/gutocarollo/architecture-system-eng-expert` apenas porque a ontologia declara a gramática `asset:<uri>`. Não foi localizado loader, registry ou modelo que registre esse tipo. Além disso, `kind: document` com prefixo `asset:` viola o padrão de ID conferido pelo lint existente.

## Fronteira: o registro de Repository não foi localizado

O contrato `jira-fbi/reference/catalog-contract.json` declara `FazGraph Repository registry`, mas a autoridade executável encontrada para esse campo é apenas sua lista literal de cinco `allowedValues`. Não há ponteiro para um arquivo Repository nessa dimensão. A ontologia consultada não tem `Repository` em `entity_types`; seus únicos `registry:` explícitos pertencem às duas classes de negócio. O modelo Graph consultado não tem coleção repositories e não há classe Repository no arquivo de modelos.

`parser/config.py` tem descoberta automática de checkouts. `parser/builder.py::persist_repos_discovery` salva triplas de diretório, família de parser e schema padrão. Esse snapshot não identifica provedor, slug completo, repository ID ou autorização semântica para a opção Jira. Sincronizar o curso nesse espelho não resolve o contrato do catálogo.

`docs/canonical/_governance/source-refs.yaml` é uma declaração histórica de fontes do programa. A busca nos leitores de parser, API, scripts e helpers não localizou consumidor desse arquivo. Não é correto promovê-lo silenciosamente a Repository registry. `business-catalog.v4.json` registra contexts, capabilities e relações supports; inserir o curso ali confundiria as dimensões.

Por isso não foi produzido um patch aplicável que apenas acrescente o slug ao whitelist global. O campo `required_contract_change` do arquivo anterior `registration-proposal.json` descreve uma alteração de projeção, que seria insuficiente como registro semântico. O arquivo anterior foi preservado; esta análise corrige a interpretação dele.

A fronteira exata é estabelecer a autoridade Repository e o contrato que a projeta no Jira. O dono precisa autorizar essa mudança de escopo em FazGraph e no pacote global. Depois disso, o diff deve mostrar a fonte, identidade por provedor, validação de unicidade, leitor e atualização de projeção. Criar um nome de arquivo novo aqui e tratá-lo como autoridade existente seria inventar a solução que a investigação deveria localizar.

## Colisão e escopo concreto da proposta do documento

Os três arquivos abaixo já estavam modificados no checkout FazGraph medido. Nenhum deles foi escrito nesta análise:

- `docs/canonical/INDEX.md`;
- `docs/canonical/_index/entity-document-map.csv`;
- `docs/canonical/_index/section-map.csv`.

A aplicação futura do documento afeta um arquivo autoral e esses três índices existentes. Deve preservar as alterações anteriores e gerar os índices sobre o corpus completo. Não se deve ampliar a mudança para adicionar sistema, contexto, capability ou página MakersHub ao curso.

`register_doc.py` não registra um objeto isolado: ele é alias para o renderer completo. Seu argumento de arquivo é ignorado. O modo seguro de conferência disponível é `--check`; não há `--dry-run` nesse alias. A publicação do grafo é outra etapa: `build.py` também escreve projeção de glossário, snapshots e constantes do frontend; portanto não executar esse comando sobre o checkout vivo presumindo que só gera um arquivo de dados. A execução deve usar o procedimento de build em candidato com caches e `publish_guard.py` antes de promover qualquer artefato. Esta análise não fez build nem publicação.

## Prova local produzida

```sh
git -C /Users/augustocarollo/Developer/fazgraph-canonical-v4 apply --check /Volumes/tank/Developer/makershub-workspaces/wt-FBI-4991/tasks/FBI-4991-arquitetura-nextra/execution/catalog/asset-document-registration.patch
```

O comando retorna zero e não aplica o diff. `asset-document-dry-run.json` contém a saída do parser real, e `asset-index-dry-run.json` contém a saída do renderer reutilizado. `asset-resolve-dry-run.json` demonstra a resolução exata em um Graph apenas em memória, sem alterar o grafo servido. Essas são verificações do candidato; a prova de registro será um read-back do ID na API servida depois da aplicação e publicação autorizadas.

## Recibos de fonte

- [2026-10-15 02:48 UTC] worktree — `pwd; git branch --show-current` → `/Volumes/tank/Developer/makershub-workspaces/wt-FBI-4991`; `docs/FBI-4991-arquitetura-aplicada`.
- [2026-10-15 02:48 UTC] FazGraph local — `git rev-parse HEAD` → `8f7dc0e1dd927ed3b5c2437337840b52c466b19e`; `.codegraph.is_dir()` → `false`.
- [2026-10-15 02:48 UTC] GitHub — `gh api repos/gutocarollo/architecture-system-eng-expert --jq '{id,node_id,full_name,private,html_url,default_branch,archived}'` → `id=1417536174`, `node_id=R_kgDOVH3irg`, `full_name=gutocarollo/architecture-system-eng-expert`, `private=true`, `default_branch=main`, `archived=false`.
- [2026-10-15 02:48 UTC] FazGraph, `ontology.yaml` — `rg -n '^  Repository:|^  Asset:|registry:'` → linhas `13` e `18`: `registry: business-catalog.v4.json`; linha `42`: `Asset:`; nenhuma linha Repository.
- [2026-10-15 02:48 UTC] FazGraph, `models.py` — inspeção AST de classes Repository/Asset e campos Graph repositories/assets → `[]`; `[]`.
- [2026-10-15 02:48 UTC] FazGraph MCP — `search(q="architecture-system-eng-expert",limit=2)` e `search(q="asset:https://github.com/gutocarollo/architecture-system-eng-expert",limit=2)` → ambas `0 hit(s)`. As consultas não são prova de inventário global.
- [2026-10-15 02:49 UTC] parser real no candidato local — `load_canonical_docs(candidate)` → ID `doc:architecture/architecture-system-eng-expert`, kind `document`, `entity_key=null`, lifecycle `active_candidate`; regex de Document → `true`.
- [2026-10-15 02:49 UTC] renderer real sobre corpus candidato — `render_all()` → três índices, `candidate_entity_count=1`, `global_index_writes=false`.
- [2026-10-15 02:49 UTC] FazGraph local — `git apply --check <patch>` → código `0`, stdout/stderr vazios; `git status --porcelain -- <três índices>` → ` M` nos três arquivos.

- [2026-10-15 02:50 UTC] resolver existente sobre Graph em memória com o candidato — `search_entities(Graph(canonical_docs=docs), "doc:architecture/architecture-system-eng-expert", limit=2)` → `kind=canonical_doc`, `match=exact`, `detail=/api/doc/doc:architecture/architecture-system-eng-expert`; `served_graph_mutated=false`.

Os hashes das fontes, as buscas executadas e a identidade GitHub completa estão em `registration-authority-receipts.json`. Os limites do registro Repository e a proposta estruturada estão em `registration-authority-proposal.json`. Nenhuma opção Jira, fonte global, catálogo ou grafo servido foi alterado.
