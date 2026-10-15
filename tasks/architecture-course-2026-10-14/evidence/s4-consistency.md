# S4 — Consistência, dados e mensageria

## Escopo e conclusão

Este pacote planeja seis explicações para os grupos 2, 3, 4 e 5. A referência integral contém 38 + 25 + 11 + 29 = 103 ocorrências nesses grupos; elas devem continuar na matriz, mesmo quando não forem um padrão prioritário. O planejamento não comprova MDX escrito ou sistemas implantados.

A composição começa pelo corpus existente: `docs/aplicado/aplicacao-makershub-40-patterns.md` já distingue aplicações propostas, e `docs/consistencia/`, `docs/outbox/` e `docs/saga/` oferecem histórias iniciais. Reutilizaremos o problema da mudança local seguida de integração externa e o caso de captação medido pela raiz. Na redação, cada garantia precisa indicar a fronteira em que vale. Uma tabela histórica não comprova Event Sourcing; uma tabela de relatório não comprova uma materialized view nativa; uma chave local não garante que um serviço externo execute uma operação uma única vez.

O worktree de escrita foi conferido em 14/10/2026: `pwd` devolveu `/Users/augustocarollo/.superset/worktrees/architecture-engineer-expert/perfect-citizen-a30f5998`; branch `perfect-citizen-a30f5998`; SHA `23d5d158d3a964dceba296296368ec14bcd8970b`. O endereço `.superset.noindex` fornecido resolve para esse caminho físico. A única escrita de S4 é este arquivo. Não houve commit, publicação, alteração do banco ou alteração de MakersHub.

## Recibos de código e PR

- [2026-10-14 16:06 UTC] MakersHub, `/Users/augustocarollo/Developer/makershub` — `git rev-parse HEAD; git branch --show-current` → `e233fb046ec333982cd1547171b0f0bd8d8d92ee`, `main`. CodeGraph foi consultado antes de buscas de texto. Consultas amplas retornaram símbolos pouco pertinentes; a continuação usou caminhos e trechos delimitados.
- [2026-10-14 16:08 UTC] Mesmo checkout — `git status --short -- backend/app/services/report_read_service.py backend/app/repositories/report_read_repository.py backend/app/services/report_persistence_service.py backend/app/services/idempotency_store.py backend/app/services/absence_reassignment_service.py backend/app/repositories/lead_pipeline_repository.py` → saída vazia. Esse recibo associa os seis arquivos selecionados ao SHA local; não declara o restante do checkout limpo nem confirma deploy.
- [2026-10-14 16:06 UTC] Bitbucket, `fazcapital/makershub`, PR 362 — `bitbucketPullRequest(action=get, prId=362)` → `state=OPEN`, título `FBI-2753: refactor(api:backend): integrar histórias de arquitetura e entrega`, source `refactor/FBI-2753-integracao-arquitetura-backend@b7889a88fc17`, target `main@c00126e9c513`.
- [2026-10-14 16:08 UTC] Bitbucket — `bitbucketRepoContent(action=commit.get, commitHash=b7889a88fc17)` → `b7889a88fc1764f70442b9f4e332f4d5098cb58a`; `commitHash=c00126e9c513` → `c00126e9c5132d9989caad2b531e31f40d7ffda3`.
- [2026-10-14 16:07 UTC] Bitbucket — `bitbucketPullRequest(action=diff, prId=362)` → 601 cabeçalhos `diff --git`. Entre eles estão `backend/app/repositories/report_read_config.py`, `backend/app/warehouse/executor/query_executor.py`, `backend/app/services/absence_reassignment_service.py` e `backend/app/repositories/user_roles_history_repo.py`. O diff não contém alteração de `report_read_service.py`, `report_read_repository.py` ou `report_persistence_service.py`. A descrição do PR trata principalmente do vocabulário de colaborador e corte de schema. Isso permite citar a refatoração e os arquivos presentes, mas não atribuir a introdução do CQRS a este diff atual nem tratar o PR aberto como produção.

O primeiro conector Bitbucket retornou literalmente `Tunnel-client has not been seen for 300 seconds`. O MCP oficial respondeu em seguida. Não foram consultados votos, tarefas ou checks para emitir review; a leitura foi somente para identificar o artefato do exemplo.

### Implementações delimitadas no checkout

| Fonte | Comportamento observado | Uso didático e limite |
|---|---|---|
| `backend/app/services/report_read_service.py:16-66`, `backend/app/repositories/report_read_repository.py:191-281`, `backend/app/api/v1/report_data.py:59` | A API entrega `ReportReadParams` ao serviço e repositório de leitura; o repositório prepara consultas de total, dados e resumo. | Exemplo de separação de caminho e contratos de consulta. Isso sustenta CQRS local neste fluxo, sem exigir outro banco ou broker e sem classificar todo o MakersHub. |
| `backend/app/services/report_persistence_service.py:127-156` | `persist_report` obtém política e lock de escrita, persiste dados, faz commit se houver sucesso ou rollback no erro. | A alteração de relatório tem regras e transação próprias, diferentes do caminho de leitura. |
| `backend/app/services/idempotency_store.py:70-120,127-214` | `INSERT ... ON CONFLICT` arbitra uma chave; hash identifica payload; uma lease permite reclaim; `finish` exige `owner_token` atual e status `in_progress`. | Repetição, replay e disputa são mecanismos concretos. O token UUID compara ownership dentro deste registro; não é um contador monotônico verificado pelo Salesforce. O próprio código declara a janela entre escrita externa e `finish`. |
| `backend/app/services/absence_reassignment_service.py:337-418` | `_apply` altera o responsável e marca `sf_owner_sync_pending=TRUE` no mesmo UPDATE; exige o responsável anterior no WHERE; grava `stg_salesforce__routing_history`. | Exemplo concreto de intenção durável de sincronização por flag, atualização condicional e auditoria. Não chamar isso de log completo de eventos de domínio, inbox universal ou prova de entrega ao Salesforce. |
| `backend/app/repositories/lead_pipeline_repository.py:485-515` | `claim_pending_for_bot` seleciona trabalho com `FOR UPDATE SKIP LOCKED`, muda `PENDING` para `BOT_PROCESSING` e devolve IDs claimados. | Exemplo de divisão de trabalho usando PostgreSQL. A leitura do código não demonstra quantos workers estão ativos nem recuperação completa após crash. |

Os mtimes e hashes lidos em 16:08 UTC foram: `report_read_service.py`, `2026-09-15T03:35:20.081127+00:00`, SHA256 `8ea29b5adcc5b225c3a54f80ae6857e81bbfc67fc3ff0147471e547903db79a7`; `report_read_repository.py`, `2026-09-15T03:35:20.058571+00:00`, SHA256 `2c2b03a63fd043431b338e386bad0af94b7437f618dfa4a927bd72ed317e2738`; `report_persistence_service.py`, `2026-09-15T03:35:20.080365+00:00`, SHA256 `378dc4b86f3c76eea2a7aac719ce6bb1ee26046cb6c5d66a56bb12b89f8b08dd`; `idempotency_store.py`, `2026-09-04T03:53:42.413972+00:00`, SHA256 `5383b6db3350faba40a65d0d73be929ee866b79a493e3647203fc61704721e12`; `absence_reassignment_service.py`, `2026-09-04T03:53:42.406510+00:00`, SHA256 `4d6cab0034db33fcdbc908f9fdb048a01e17adc1eb31020f65cba967d479d370`; `lead_pipeline_repository.py`, `2026-09-04T03:53:42.393347+00:00`, SHA256 `6f3bd65cf9a401ddae83b8a4c78d7a8196a0f1e3a6207d3a9847b574d04cdaa3`.

## FazGraph primeiro e PostgreSQL depois

- [2026-10-14 16:06 UTC] FazGraph — `pipeline(q='absence_reassignment', max_matches=1)` → `No table id matches 'absence_reassignment'.` A falta de match do termo não foi tratada como ausência da implementação.
- [2026-10-14 16:07 UTC] FazGraph — `pipeline(q='pending_d1', max_matches=2)` → `makershub._pending_d1_routing`, `makershub.pending_d1_routings`; `pipeline(q='idempotency', max_matches=1)` → `makershub._idempotency_key`. O snapshot de runtime vem de `2026-10-13T03:07+00:00` e está marcado stale. O grafo não detecta produtor desses objetos; o código local acima preenche parte dessa lacuna, com outro nível de evidência.
- [2026-10-14 16:07:16 UTC] PostgreSQL `192.168.254.137/32`, `faz_capital` — consulta ao catálogo abaixo → os três objetos têm `relkind=r`; `_idempotency_key` contém `status, owner_token, updated_at, expires_at`; `_pending_d1_routing` contém `processed_employee_id, sf_owner_sync_pending, sf_owner_sync_attempts, sf_owner_sync_at`.

```sql
SELECT clock_timestamp() AT TIME ZONE 'UTC' AS measured_at_utc,
       inet_server_addr()::text AS server_address,
       current_database() AS database_name,
       n.nspname AS schema_name, c.relname AS relation_name,
       c.relkind::text AS relation_kind,
       (SELECT string_agg(a.attname, ', ' ORDER BY a.attnum)
        FROM pg_attribute a
        WHERE a.attrelid=c.oid AND a.attnum>0 AND NOT a.attisdropped
          AND a.attname IN ('status','updated_at','expires_at','owner_token',
            'sf_owner_sync_pending','sf_owner_sync_attempts','sf_owner_sync_at',
            'processed_employee_id','processed_advisor_id')) AS selected_columns
FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
WHERE (n.nspname='makershub'
       AND c.relname IN ('_idempotency_key','_pending_d1_routing'))
   OR (n.nspname='public' AND c.relname='rpt_inflow__movement_adjusted')
ORDER BY schema_name,relation_name;
```

- [2026-10-14 16:08:02 UTC] Mesmo PostgreSQL — consulta agregada abaixo → `server_version=16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)`, `in_recovery=false`, `wal_level=minimal`, `_idempotency_key.status_counts={"done":4771}`, `latest_update=2026-10-14 13:03:26.386202-03:00`; `_pending_d1_routing.status_counts={"row_count":2574,"max_sf_sync_attempts":0,"pending_sf_sync_count":0}`, `latest_update=null`.

```sql
SELECT clock_timestamp() AT TIME ZONE 'UTC' AS measured_at_utc,
       inet_server_addr()::text AS server_address,
       current_database() AS database_name,
       current_setting('server_version') AS server_version,
       pg_is_in_recovery() AS in_recovery,
       current_setting('wal_level') AS wal_level,
       'makershub._idempotency_key' AS source_relation,
       (SELECT jsonb_object_agg(status,row_count)
        FROM (SELECT status,count(*) AS row_count
              FROM makershub._idempotency_key GROUP BY status) counts) AS status_counts,
       (SELECT max(updated_at) FROM makershub._idempotency_key) AS latest_update
UNION ALL
SELECT clock_timestamp() AT TIME ZONE 'UTC', inet_server_addr()::text,
       current_database(),current_setting('server_version'),pg_is_in_recovery(),
       current_setting('wal_level'),'makershub._pending_d1_routing',
       jsonb_build_object('row_count',count(*),'pending_sf_sync_count',
          count(*) FILTER (WHERE sf_owner_sync_pending),
          'max_sf_sync_attempts',max(sf_owner_sync_attempts)),max(sf_owner_sync_at)
FROM makershub._pending_d1_routing;
```

Esses números não demonstram que 4.771 efeitos externos ocorreram uma única vez nem que todas as oportunidades do Salesforce estão sincronizadas. O `wal_level=minimal` medido impede apresentar CDC por decodificação lógica ou streaming físico como capacidades habilitadas neste servidor. A documentação PostgreSQL 16 exige `logical` para decodificação lógica e `replica` ou superior para arquivamento contínuo e streaming. S6 deve manter HA, backups e restauração como propostas até reunir sua própria prova operacional.

A medição de captação feita pela raiz fica reutilizada, sem nova varredura: `postgres-inflow.json`, 14/10 15:56:30 UTC, 557.731 linhas e chaves distintas, 3.380 movimentos em outubro, soma BRL assinada de R$ 18.742.122,16, última `movement_date=2026-10-08`. O valor não é receita, nem fechamento de outubro, nem regra financeira confirmada. O snapshot de linhagem de 13/10 identifica 43 tabelas, 424 cards e 27 endpoints; não confirma consumidores ativos hoje.

## Plano das seis explicações

| Página proposta | Pergunta de estudo e cobertura | Caso e diagrama |
|---|---|---|
| `content/explicacao/consistencia/transacoes-e-integracoes.mdx` | Por que salvar no banco e atualizar outro sistema pode deixar metade do trabalho feita? Aprofunda 5, 7, 8 e 9; cobre dual write, outbox/inbox, CDC, Saga coreografada/orquestrada, compensação, 2PC, 3PC, TCC e reserva. | `_apply` e flag de sincronização fornecem o exemplo real. Um sequence diagram mostra commit local, falha de rede e nova tentativa. Saga e CDC são propostas, com condições e custos. |
| `content/explicacao/consistencia/mensagens-e-entrega.mdx` | Quem recebe uma mensagem, quem divide trabalho e o que acontece quando há falha? Aprofunda 6, 10, 38 e 39; cobre todas as 25 ocorrências do grupo 3, incluindo routers, filtro, tradução, enriquecimento, splitter/aggregator, resequencer, correlação, retries, atraso, prioridade, poison messages e streaming. | `claim_pending_for_bot` oferece trabalho dividido por PostgreSQL. Diagramas comparam três assinaturas e três workers; outro mostra commit do efeito antes do ack, reentrega e deduplicação. DLQ durável é proposta quando não houver evidência. |
| `content/explicacao/consistencia/cqrs-e-projecoes.mdx` | Por que gravar um relatório e mostrar um dashboard usam modelos diferentes? Aprofunda 11 e 13; cobre command/query handlers, read/write models, projeções e eventos de domínio/integração. | `ReportPersistenceService` e `ReportReadService` são exemplos de checkout. O pipeline de captação ilustra resultado derivado, com seu snapshot; um diagrama separa fonte, cálculo e leitura, sem trocar tabela comum por materialized view nativa. |
| `content/explicacao/consistencia/historico-e-event-sourcing.mdx` | Quando um histórico permite reconstruir o estado e quando ele apenas registra mudanças? Aprofunda 12, snapshotting e relação com CQRS. | `stg_salesforce__routing_history` exemplifica auditoria, sem prova de reconstrução completa. Caso financeiro hipotético: aporte de R$ 1.000 seguido de estorno de R$ 200 deixa R$ 800; os eventos, a versão e a política de correção são definidos explicitamente. Isso não é um ledger financeiro já implantado na Faz. |
| `content/explicacao/consistencia/concorrencia-e-acordo.mdx` | Como dois executores sabem quem pode gravar e qual estado é mais recente? Aprofunda 28, 29 e 33; cobre CAS, locks, lease, fencing, RYW, leituras monotônicas, consistência, quórum, version vectors, Lamport/HLC, consenso, Raft/Paxos e gossip. | O claim e owner token local são o caso real limitado. Um sequence diagram mostra A suspenso, B assumindo e A retornando. Fencing monotônico validado no destino e eleição de HA são propostas. S5 complementa o lock de cache e S6 explica operação de HA. |
| `content/explicacao/consistencia/armazenamento-wal-e-distribuicao.mdx` | O que muda quando copiamos dados, repartimos tabelas ou repartimos bancos? Aprofunda 30, 31, 32 e 34; cobre todas as 29 ocorrências do grupo 5, incluindo modalidades de réplica, range/hash/directory/geographic sharding, hashing consistente, append-only, copy-on-write, armazenamento por log, amplificação de escrita, índices, covering index, desnormalização e pré-cálculo. | `wal_level=minimal` é o contraponto real para explicar capacidade e configuração. Diagramas distinguem particionamento local, shard e réplica. S6 possui desenho operacional, falha do primário e cadeia de restore; não afirmar HA implantada. |

A redação permanece explicação Diátaxis: cada página começa pela dor e pelas causas, apresenta ganho, custo e limite e aponta para a referência integral do grupo. Exercícios e comandos de implantação ficam em tutoriais ou guias próprios. Não apresentar uma sequência fixa Outbox → CDC → broker → Saga como evolução obrigatória; não inventar limiar de mensagens por segundo ou latência sem benchmark do cenário.

## Fontes oficiais consultadas em 14/10/2026

- [CQRS, Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/cqrs) sustenta a separação de modelos e suas combinações; [Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing) mantém o stream como fonte de verdade e trata snapshots como otimização.
- [REFRESH MATERIALIZED VIEW, PostgreSQL 18](https://www.postgresql.org/docs/18/sql-refreshmaterializedview.html), também consultada em Context7 `/websites/postgresql_18`, sustenta a substituição do resultado, requisito de índice UNIQUE compatível e uma atualização por view de cada vez. A redação final deve usar a versão 16 para API aplicada ao servidor medido.
- [WAL, PostgreSQL](https://www.postgresql.org/docs/current/wal-intro.html) explica ordem entre registro e páginas; [configuração WAL, PostgreSQL 16](https://www.postgresql.org/docs/16/runtime-config-wal.html) sustenta a interpretação de `minimal`, `replica` e `logical`.
- [Outbox Event Router, Debezium](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html) é a base madura para o exemplo proposto de outbox por CDC, sem exigir que o curso implemente um replicador próprio.
- [Redis Pub/Sub](https://redis.io/docs/latest/develop/pubsub/) documenta perda com subscriber desconectado e entrega at-most-once; [RabbitMQ acknowledgements e confirms](https://www.rabbitmq.com/docs/confirms) separa confirmação do produtor e do consumidor e descreve reentrega, requeue e controle de prefetch.

As tabelas do corpus dão candidatos de frameworks e aplicações OSS, não comprovação de adoção local: Debezium/Eventuate; RabbitMQ/NATS/Redis Streams; EventSourcingDB/Axon/Marten; PostgreSQL; etcd/Raft; Vitess; Loki/memberlist. O auxiliar de referências deve verificar os pares efetivos do catálogo, sua adequação à stack e fontes oficiais, sem transformar estrelas em qualidade nem números antigos em medições atuais.

## Três missões propostas para auxiliares Luna

1. **Ledger e histórico, leitura somente.** Partir dos seis arquivos e SHAs acima, reutilizar os agregados já medidos e consultar CodeGraph antes de texto. Delimitar origem, escrita, leitura e possibilidade de replay de `stg_salesforce__routing_history`, histórico de roles e idempotência. Procurar componentes existentes que sirvam à narrativa antes de procurar colisões. Entregar uma tabela que marque auditoria, estado atual, projeção ou event store; não declarar Event Sourcing por nome de tabela. Não repetir contagens, ler PII ou escrever em MakersHub. A raiz atribui um arquivo de evidência próprio quando despachar.
2. **Referências dos grupos 2–5.** Conferir os 103 itens na matriz e os frameworks/OSS dos prioritários 5–13, 28–34 e 38–39. Usar Context7 e documentos oficiais para garantias e limitações; GitHub para implementações e versões, sem copiar estrelas antigas. Dar atenção a quórum sob concorrência, 3PC e suas suposições, exatamente uma vez dentro de fronteira definida, CAS versus versão monotônica e capacidades WAL por versão. Retornar links, data e claim suportado; dúvidas permanecem explicitadas.
3. **Didática das seis páginas.** Para cada pergunta da tabela, propor história curta, conta feita, analogia limitada e Mermaid que mostre o mecanismo causal. Reutilizar captação com seu horário e rotular números financeiros inventados como hipotéticos. Comparar escolhas por comportamento e custo concreto, sem recomendar CDC, Saga, ES, sharding ou HA como mudança já autorizada. Entregar esboços de explicação, com links para referências e exercícios separados; não gerar MDX antes do despacho de redação.

## Limites restantes

Não foi confirmado Event Sourcing, Saga, CDC ou broker durável implantado no MakersHub. Também não foi demonstrada restauração por WAL, réplica operacional, HA, monotonic reads de ponta a ponta ou fencing no Salesforce. As lacunas limitam o rótulo de exemplo real; não impedem explicar os padrões por casos hipotéticos honestos. Não houve auditoria do PR 362, teste de mutação, escrita externa ou declaração de merge/deploy.

A memória `MEMORY.md:1911-1937` foi usada apenas para localizar a história anterior do PR; os fatos acima foram conferidos nesta execução. Registro associado: `01a0f072-031b-79d0-9cd8-eccb6a2fb808`.
