# Curadoria GitHub: skills e referências de arquitetura

## Recorte e resultado

Consultei o brief e as três referências locais no checkout `perfect-citizen-a30f5998`, SHA `23d5d158d3a964dceba296296368ec14bcd8970b`. A curadoria contém 60 registros, ordenados por estrelas atuais apenas dentro deste conjunto. O JSON guarda, para cada registro, a URL canônica retornada pelo GitHub (ou a URL tentada quando o caminho recebeu 404), estrelas, SPDX, arquivo, data do último push, branch padrão, horário de observação e status HTTP.

Os oito skill packs são `wshobson/agents`, `j4flmao/agent-skills`, `wondelai/skills`, `mblode/agent-skills`, `addyosmani/agent-skills`, `obra/superpowers`, `redpanda-data/skills` e `diagrid-labs/dapr-skills`. Os dois últimos nomes foram resolvidos a partir das menções a Redpanda e Dapr nas referências. `agentskills/agentskills` entrou como fonte da especificação Agent Skills, não como nono pack.

Para os padrões, dei prioridade a implementações canônicas e aplicações de referência que os três documentos associam a Saga, Outbox, CQRS, Event Sourcing, CDC, resiliência, cache, mensageria, implantação progressiva, coordenação e state machines. Também resolvi nomes de frameworks citados sem owner/repo explícito, como Spring Modulith, Redis, Caffeine, Apache Beam, PostgreSQL, RocksDB, RabbitMQ, Apache Kafka, Airbyte, ArchUnit e MediatR. A lista foi limitada a 60; ficaram fora cinco referências de leitura geral, `papers-we-love/papers-we-love`, `ept/ddia-references`, `theanalyst/awesome-distributed-systems`, `binhnguyennus/awesome-scalability` e `donnemartin/system-design-primer`.

O caminho `vert-x3/vertical-slice-dotnet`, escrito de forma ambígua em `repositorios.md`, recebeu HTTP 404. Mantive o registro com campos sem metadados e não substituí por outro repositório de nome parecido, porque as fontes não identificam qual alternativa pretendiam. O 404 confirma a resposta para esse caminho exato, não a inexistência de exemplos de Vertical Slice.

## Como ler a classificação

A adequação vem da associação feita nas referências: skill pack para ensinar um procedimento; framework ou biblioteca para estudar a implementação do padrão; aplicação ou demo para observar o padrão em contexto. Isso mede correspondência ao material de estudo, não prontidão para produção. A manutenção aparece apenas como `archived` e `pushed_at`: um repositório não arquivado não fica automaticamente classificado como ativo. A licença aparece somente como SPDX devolvido pela API; `null` significa que o GitHub não forneceu SPDX, e `NOASSERTION` foi preservado literalmente. Esses campos ajudam uma revisão de compatibilidade e não substituem a leitura da licença.

Os dez primeiros por estrelas, nesta coleta, são: `obra/superpowers` (299042), `kubernetes/kubernetes` (128212), `addyosmani/agent-skills` (106575), `redis/redis` (76806), `apache/superset` (75141), `traefik/traefik` (65210), `etcd-io/etcd` (52359), `wshobson/agents` (40732), `istio/istio` (38439) e `apache/kafka` (33951). O ranking completo está no JSON. Os valores aproximados dos documentos de origem não foram tratados como atuais.

## Busca rápida de comunidade

GitHub e a organização da especificação confirmam os endereços dos packs e o formato: [j4flmao/agent-skills](https://github.com/j4flmao/agent-skills), [Redpanda Skills](https://github.com/redpanda-data/skills), [Dapr Skills da Diagrid Labs](https://github.com/diagrid-labs/dapr-skills) e [Agent Skills spec](https://github.com/agentskills/agentskills). Diretórios como [junminhong/awesome-agent-skills](https://github.com/junminhong/awesome-agent-skills) e [kodustech/awesome-agent-skills](https://github.com/kodustech/awesome-agent-skills) ajudam a descobrir exemplos; sua presença numa lista não comprova qualidade técnica.

No Reddit encontrei conversas sobre padrões para estruturar skills e sobre a adoção de packs ([discussão de padrões](https://www.reddit.com/r/agentdevelopmentkit/comments/1rqq414/5_design_patterns_for_structuring_agent_skills/), [opinião sobre skills no ecossistema](https://www.reddit.com/r/AI_Agents/comments/1tvo738/half_of_github_trending_ai_repos_are_skills_packs/)). No Hacker News, a busca `skill.md architecture` retornou 9 itens e `agent skills architecture` retornou 139 na API Algolia em 2026-10-14 17:14 UTC; entre eles estão [JIT Skill Architecture](https://news.ycombinator.com/item?id=49509511) e [OpenSkills](https://news.ycombinator.com/item?id=46716016). Esses resultados registram conversa e descoberta, não evidência de que uma técnica funciona.

## Verificações ao vivo

- [2026-10-14 17:12–17:13 UTC] GitHub REST API — `GET /repos/{owner}/{repo}` para os 60 IDs consultados → `59 HTTP 200; 1 HTTP 404`. O único 404 foi `https://github.com/vert-x3/vertical-slice-dotnet`; os demais valores estão no snapshot.
- [2026-10-14 17:12–17:13 UTC] GitHub REST API — campos selecionados → `59 archived=false; 1 archived=null`. Três registros têm `licenseSPDX=null`: Redpanda, demo de Argo Rollouts e o caminho de Vertical Slice com 404.
- [2026-10-14 17:10 UTC] GitHub Trending daily — `GET https://github.com/trending?since=daily` → `HTTP 200; 12 linhas de repositório renderizadas`. Nenhum dos 60 registros apareceu nessas 12 linhas. `K-Dense-AI/scientific-agent-skills` apareceu, mas não está nas três referências e não entrou no snapshot. Uma página diária de trending não forma uma série histórica de estrelas nem prova qualidade.
- [2026-10-14 17:14 UTC] Hacker News Algolia — `search(query="skill.md architecture", tags=story)` e `search(query="agent skills architecture", tags=story)` → `nbHits=9` e `nbHits=139`.

Consultei somente metadados públicos de repositório e páginas públicas de busca. Não consultei campos de e-mail nem chaves. Nenhum skill foi instalado e nenhum sistema externo foi alterado.

## Adendo — fontes aplicadas aos 40 prioritários

Atualizei `content/referencia/prioritarios.mdx` sem mudar os nomes ou a ordem dos 40 conceitos. Cada linha agora tem link para uma base técnica e para o arquivo, manifesto ou exemplo que mostra o mecanismo. Reutilizei `github-snapshot.json`, `github-snapshot-supplement.json`, os mapas de âncoras dos relatórios S2, S4, S5 e S6, e as fontes de `l4b-messaging.md`, `l5c-references.md`, `l6a-platform.md` e `l6c-release-security.md`. Nenhuma tabela de estrelas ou horários foi alterada.

Os rótulos separam uma demonstração de um produto OSS. `REF` identifica código de exemplo; `produto OSS` identifica código que pertence a um produto. Nenhum rótulo afirma que o produto esteja implantado no MakersHub. O item 40 aponta para o capítulo `distributed-work` sem hash de seção, porque o relatório S3 não fornece uma âncora prioritária própria. Nos demais itens, usei as âncoras dos relatórios de autoria.

### Correções e limites

- O antigo caminho `vert-x3/vertical-slice-dotnet` recebeu 404 no snapshot anterior. Agora o item 3 aponta para `mehdihadeli/vertical-slice-api-template`, cujo `CreateProductEndpoint.cs` retornou HTTP 200 e organiza a criação do produto dentro da feature `CreatingProduct`.
- Superset continua como fonte de cache-aside no item 14 e de workers Celery no item 38. O item 6 usa o sample Dapr/Azure com publicador e assinante; o item 39 usa o subscriber Python que configura `dead_letter_topic`. Isso segue a correção de `l4b-messaging.md`: o exemplo Superset/Celery não demonstra Pub/Sub.
- O item 8 agora aponta para o código CDC do conector PostgreSQL do Airbyte, que integra operações Debezium. O item 7 usa o serviço de pedidos do sample Debezium, que dispara eventos dentro de `@Transactional`.
- O item 17 aponta para o cálculo de Airflow que usa um hash determinístico de DAG, tarefa, data lógica e tentativa para espalhar os horários de retry. Não o descrevi como jitter aleatório.
- O item 23 usa uma fachada de roteamento em `facade_router.py`, classificada como **REF didática**; seu próprio código descreve endpoints e dados fictícios.
- O item 24 liga o guia de migração do GitLab e uma migração post-deploy que remove colunas antigas. O arquivo prova a fase de contração. Não localizei um arquivo pareado de expansão e backfill para essas mesmas colunas, então a tabela não afirma que o par completo foi verificado.
- O item 37 limita o Wild Workouts a um adaptador que converte representação gRPC. Esse arquivo, isoladamente, não prova uma ACL semântica completa.
- No item 15, a página oficial Caffeine `Refresh` fornece um exemplo direto de `refreshAfterWrite`, mas não localizei uma aplicação consumidora verificada. O arquivo de configuração do GeoServer Cloud consultado tem `#refreshAfterWrite=[duration]` comentado e não demonstra uso ativo. A linha mantém o exemplo como REF e mostra a lacuna.

### Verificações ao vivo

- [2026-10-14 19:02–19:04 UTC] GitHub REST API — `GET /repos/{owner}/{repo}/contents/{path}?ref={branch}` para os links GitHub extraídos da página → `81 endpoints verificados; 81 HTTP 200; 0 não-200`. Os dois links de wiki foram abertos separadamente no GitHub: [Caffeine Refresh](https://github.com/ben-manes/caffeine/wiki/Refresh) e [RxJava Backpressure](https://github.com/ReactiveX/RxJava/wiki/Backpressure).
- [2026-10-14 19:04 UTC] Airflow — `GET /repos/apache/airflow/contents/airflow-core/src/airflow/models/taskinstance.py?ref=main` → `HTTP 200; next_retry_datetime calcula retry_exponential_backoff e modded_hash a partir da identidade da tentativa`.
- [2026-10-14 19:04 UTC] GitLab — `GET /repos/gitlabhq/gitlabhq/contents/db/post_migrate/20260420174610_remove_unencrypted_value_columns.rb?ref=master` → `HTTP 200; remove_column para quatro colunas de value`.
- [2026-10-14 19:04 UTC] GeoServer Cloud — `GET /repos/geoserver/geoserver-cloud-config/contents/geoserver.yml?ref=master` → `HTTP 200; linha 23: #refreshAfterWrite=[duration]`.
- [2026-10-14 19:04 UTC] Caffeine Wiki — `open(https://github.com/ben-manes/caffeine/wiki/Refresh)` → página `Refresh`, exemplo `refreshAfterWrite` e regra de que uma leitura elegível inicia a atualização assíncrona.
- [2026-10-14 19:04 UTC] RxJava Wiki — `open(https://github.com/ReactiveX/RxJava/wiki/Backpressure)` → página `Backpressure`, exemplo em que o assinante pede um item e solicita outro após processá-lo.

A contagem da página final é de 40 linhas, IDs 1–40. Não rodei testes, build ou renderização MDX nesta atualização.

## Adendo — quatro referências com código aplicado

Substituí as referências somente documentais dos itens 15, 19, 21 e 40 por fontes de código primárias, mantendo os 40 conceitos, a ordem e as âncoras dos capítulos. Este adendo complementa a nota anterior do item 15.

- **15 — Refresh Ahead:** Trino instala `refreshAfterWrite` no `CachingHiveMetastore` somente quando `refreshMillis` está configurado, existe executor e a expiração não vence antes do intervalo de refresh. O loader é envolvido por `asyncReloading`; a semântica do Caffeine inicia a atualização quando uma entrada elegível é consultada. Isso demonstra atualização assíncrona disparada por leitura. Superset fornece outra implementação: uma tarefa Celery aquece periodicamente dashboards; o exemplo de native filters agenda uma execução diária e a documentação pede que o intervalo não seja mais longo que o TTL efetivo. O mesmo trecho exige cache persistente e timeout positivo. Links usados na tabela: [código Trino](https://github.com/trinodb/trino/blob/f93c619637a4aede00b3ba329de03e4c9e62bcb8/lib/trino-metastore/src/main/java/io/trino/metastore/cache/CachingHiveMetastore.java#L1136-L1146), [tarefa Superset](https://github.com/apache/superset/blob/b411454508c49ba4780047582ab61ccababa856c/superset/tasks/cache.py#L352-L361), [exemplo de agenda e relação com TTL](https://github.com/apache/superset/blob/b411454508c49ba4780047582ab61ccababa856c/docs/admin_docs/configuration/cache.mdx#L237-L262) e [semântica Caffeine](https://github.com/ben-manes/caffeine/wiki/Refresh).
- **19 — Backpressure:** `ConnectableTask` verifica uma fila de saída cheia durante o lote e encerra a invocação atual; `AbstractFlowFileQueue.isFull()` compara a quantidade de FlowFiles e o total de bytes aos limites configurados. As fontes estão em [ConnectableTask](https://github.com/apache/nifi/blob/9e6c18893f1b1df713dac55d98c2b2944d235844/nifi-framework-bundle/nifi-framework/nifi-framework-core/src/main/java/org/apache/nifi/controller/tasks/ConnectableTask.java#L165-L172) e [AbstractFlowFileQueue](https://github.com/apache/nifi/blob/9e6c18893f1b1df713dac55d98c2b2944d235844/nifi-framework-bundle/nifi-framework/nifi-framework-core/src/main/java/org/apache/nifi/controller/queue/AbstractFlowFileQueue.java#L147-L168).
- **21 — API Gateway:** `apisix/init.lua` executa o match da rota HTTP e trata rota não encontrada; o plugin `limit-count` contém a aplicação de uma política de limite no mesmo gateway. Fontes: [roteador APISIX](https://github.com/apache/apisix/blob/2e43b6c605566d383378a45ef1f06f3debf48a42/apisix/init.lua#L919-L948) e [implementação `limit-count`](https://github.com/apache/apisix/blob/2e43b6c605566d383378a45ef1f06f3debf48a42/apisix/plugins/limit-count/init.lua).
- **40 — State Machine:** `statelyai/sketch/examples/inspect/src/main.ts` é uma demo executável: define uma máquina de semáforo, cria e inspeciona um actor e liga eventos de interface a transições. Mantive `REF` para identificar a demonstração, sem classificá-la como produto consumidor. Fonte: [exemplo de inspeção do Stately Sketch](https://github.com/statelyai/sketch/blob/a29bbd11662e1a64efca9e14e604adf25e9705a4/examples/inspect/src/main.ts#L1-L43).

### Verificações ao vivo deste adendo

- [2026-10-14 19:14–19:17 UTC] GitHub REST API — `gh api --include 'repos/trinodb/trino/contents/lib/trino-metastore/src/main/java/io/trino/metastore/cache/CachingHiveMetastore.java?ref=f93c619637a4aede00b3ba329de03e4c9e62bcb8' | sed -n '1p'` → `HTTP/2.0 200 OK`; linhas 1136–1146 verificadas no conteúdo do commit.
- [2026-10-14 19:14–19:17 UTC] GitHub REST API — `gh api --include 'repos/apache/superset/contents/superset/tasks/cache.py?ref=b411454508c49ba4780047582ab61ccababa856c' | sed -n '1p'` → `HTTP/2.0 200 OK`; tarefa `cache-warmup` verificada nas linhas 352–361.
- [2026-10-14 19:14–19:17 UTC] GitHub REST API — `gh api --include 'repos/apache/superset/contents/docs/admin_docs/configuration/cache.mdx?ref=b411454508c49ba4780047582ab61ccababa856c' | sed -n '1p'` → `HTTP/2.0 200 OK`; exemplo diário, requisitos e relação com o TTL verificados nas linhas 237–262.
- [2026-10-14 19:14–19:17 UTC] GitHub REST API — `gh api --include 'repos/apache/nifi/contents/nifi-framework-bundle/nifi-framework/nifi-framework-core/src/main/java/org/apache/nifi/controller/tasks/ConnectableTask.java?ref=9e6c18893f1b1df713dac55d98c2b2944d235844' | sed -n '1p'` → `HTTP/2.0 200 OK`; verificação de backpressure nas linhas 165–172.
- [2026-10-14 19:14–19:17 UTC] GitHub REST API — `gh api --include 'repos/apache/nifi/contents/nifi-framework-bundle/nifi-framework/nifi-framework-core/src/main/java/org/apache/nifi/controller/queue/AbstractFlowFileQueue.java?ref=9e6c18893f1b1df713dac55d98c2b2944d235844' | sed -n '1p'` → `HTTP/2.0 200 OK`; comparação dos limites de quantidade/bytes nas linhas 147–168.
- [2026-10-14 19:14–19:17 UTC] GitHub REST API — `gh api --include 'repos/apache/apisix/contents/apisix/init.lua?ref=2e43b6c605566d383378a45ef1f06f3debf48a42' | sed -n '1p'` → `HTTP/2.0 200 OK`; match de rota nas linhas 919–948.
- [2026-10-14 19:14–19:17 UTC] GitHub REST API — `gh api --include 'repos/apache/apisix/contents/apisix/plugins/limit-count/init.lua?ref=2e43b6c605566d383378a45ef1f06f3debf48a42' | sed -n '1p'` → `HTTP/2.0 200 OK`; implementação do plugin verificada.
- [2026-10-14 19:14–19:17 UTC] GitHub REST API — `gh api --include 'repos/statelyai/sketch/contents/examples/inspect/src/main.ts?ref=a29bbd11662e1a64efca9e14e604adf25e9705a4' | sed -n '1p'` → `HTTP/2.0 200 OK`; máquina, actor e inspector verificados nas linhas 1–43.

### Limites de suporte que permanecem

- **15:** o código Trino demonstra refresh após leitura elegível; o Superset documenta e implementa warm-up agendado, mas o intervalo e o TTL são escolhas de configuração. Não inspecionei uma implantação ativa nem afirmo que esses trabalhos estejam habilitados em produção.
- **24:** o arquivo GitLab citado demonstra a contração; não rastreei a migração pareada de expansão/backfill para as mesmas colunas.
- **40:** há código executável de demonstração, classificado como `REF`; não localizei nesta passada um consumidor OSS independente de XState para classificar como produto.
- **23 e 37:** permanecem as limitações já descritas acima: endpoints fictícios no exemplo de Strangler e um adaptador que não demonstra sozinho toda a tradução semântica de uma ACL.

As quatro linhas receberam referências diretas de código; o total segue em 40. Não rodei testes, build ou renderização MDX.
