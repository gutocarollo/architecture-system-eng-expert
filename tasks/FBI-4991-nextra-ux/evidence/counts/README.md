# Contagem e limites da explicação do curso

A inspeção foi feita no worktree `wt-FBI-4991`, no branch `docs/FBI-4991-arquitetura-aplicada`, a partir de `83150a31c0d27f655b1160570aedd6c3e32e5d63`. O arquivo `catalog-counts.json` fixa o horário e os hashes dos seis arquivos de dados lidos. As cópias `.before` conservam integralmente os textos anteriores, inclusive os estados de revisão retirados das tabelas públicas.

| Número | O que foi contado | Fonte local |
| --- | --- | --- |
| 40 | Entradas prioritárias, que somam 46 associações a 46 conceitos distintos. | `tasks/architecture-course-2026-10-14/evidence/coverage.json`, campo `priority_entries`. |
| 310 | Conceitos distintos na curadoria e no mapa de aprendizado. | `execution/curation/matrix.json`, campo `concepts`, e `execution/learning/concept-matrix.json`, campo `concepts`. |
| 15 | Casos principais que recebem os 310 conceitos. | `execution/learning/concept-matrix.json`, campo `concepts[].case_id`, e `execution/learning/families.json`. |
| 17 | Famílias de assunto da curadoria, cuja soma também é 310. | `content/referencia/curadoria/index.mdx`, tabela de famílias. |
| 18 | União dos 15 casos principais com dois casos PostgreSQL e um caso Airflow. | Registros `execution/learning/families.json`, `execution/postgres-learning/families.json` e `execution/airflow-learning/families.json`. |

Os caminhos abreviados com `execution/` nesta tabela ficam em `tasks/FBI-4991-arquitetura-nextra/`. A soma dos grupos na ordem da tabela pública é 5 + 1 + 1 + 3 + 85 + 16 + 20 + 38 + 55 + 11 + 14 + 12 + 21 + 16 + 12 = 310. Cada conceito tem um único `case_id` no mapa. A associação do conceito ao caso não impede seu uso como comparação em outros materiais.

Os dois registros adicionais de PostgreSQL identificam `query-grain-postgres` e `revision-cas-postgres`. O registro de Airflow identifica `airflow-lock-retry`. As páginas desses casos conservam seus recortes históricos. Esta tarefa não mediu banco, infraestrutura, estado de PR, deploy ou execução dos laboratórios.

## A fronteira entre cobertura e implementação

O mapa de aprendizado registra 310 valores `RELEVANT_BOUNDED_OBSERVATION`. Isso conta observações consideradas pertinentes pelo autor. O mesmo arquivo conserva 310 valores `independent_review: PENDING` e 238 valores `specific_pattern_implementation_gap: true`. Esses campos não foram alterados. Portanto, a conta 310 e o antigo cálculo de zero observações sem associação não demonstram implementação integral dos padrões nem revisão independente concluída dos exercícios.

A revisão de fontes da curadoria tem outro escopo. O texto anterior da página de curadoria descrevia 259 decisões da primeira passada, 14 observações não bloqueantes e 51 recortes reparados; ele permanece no snapshot `.before`. Esse estado interno não foi convertido em promessa sobre a execução das práticas. A tabela prioritária anterior também marcava as 40 linhas como revisão independente pendente; essa coluna foi retirada da interface e preservada no snapshot.

## Alterações e localizadores

O título e o H1 de `content/referencia/prioritarios.mdx`, nas linhas 2 e 7, passam a usar exatamente “Arquitetura na prática: Makershub”. Os parágrafos das linhas 9, 11 e 13 explicam a seleção, o agrupamento dos números e a próxima ação do aluno. As 40 linhas da tabela mantêm os seis campos de conteúdo e todas as referências; somente a coluna de estado interno foi retirada.

Em `content/referencia/curadoria/index.mdx`, as linhas 9 a 13 explicam a consulta e a relação entre 17 famílias, 15 casos e 40 temas. A tabela mantém as 17 famílias e suas contagens; os estados autorais e as pendências ficam no snapshot interno.

Em `content/jornadas/matriz.mdx`, as linhas 9 a 13 explicam os 15 grupos com o exemplo dos 55 conceitos do caso de fila. As linhas 33 e 35 delimitam a prova e explicam por que a lista de jornadas tem 18 itens. A tabela conserva as 15 linhas e todos os destinos. O título da seção dos quarenta prioritários foi preservado para conservar sua âncora.

Somente as strings e a composição das colunas correspondentes foram ajustadas nos geradores `execution/curation/reconcile_references.py`, `execution/curation/build_matrix.py` e `labs/architecture/map_concepts.py`. Nenhum gerador foi executado e nenhuma das demais páginas foi regenerada.

## Inspeção estática

O recibo `content-inspection.json` registra a preservação de todos os destinos de links anteriores, a igualdade das referências externas, o título exato, 40 linhas prioritárias, 15 linhas de casos com soma 310, 17 famílias com soma 310 e a análise de sintaxe dos três geradores. Esse recibo descreve inspeção de conteúdo. O build e a conferência visual pertencem ao orquestrador.

## Ajuste posterior do principal

O principal renomeou também o subtítulo da seleção dentro da matriz para Arquitetura na prática: Makershub. A âncora anterior desse subtítulo mudou; os destinos dos links de conteúdo e das fontes continuam preservados. A verificação do curso encontrou zero links internos inválidos. As páginas índice receberam asIndexPage e os respectivos _meta perderam a entrada index redundante, como prevê o normalizador nativo do Nextra.
