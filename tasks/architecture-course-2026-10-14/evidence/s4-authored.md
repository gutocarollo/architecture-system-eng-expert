# S4 — Recibo de autoria

Status: **AUTHORED_NOT_REVIEWED**. S4 escreveu cinco explicações e quatro referências no worktree de arquitetura. O conteúdo usa Diátaxis, o contrato de autoria preparado e os deltas `l4a-ledger.md`, `l4b-messaging.md` e `l4c-protocols.md`. A raiz possui integração, índices, cobertura, compilação e council; este recibo não aprova o conteúdo.

Preflight: `pwd` devolveu `/Users/augustocarollo/.superset/worktrees/architecture-engineer-expert/perfect-citizen-a30f5998`, branch `perfect-citizen-a30f5998`, SHA `23d5d158d3a964dceba296296368ec14bcd8970b`. O escopo de escrita foi os nove MDX abaixo e este recibo. Os arquivos de outros autores foram preservados. Não houve commit, escrita no banco ou publicação.

## Arquivos e hashes

- [2026-10-14 18:17:33 UTC] Worktree de arquitetura — leitura dos nove arquivos com `Path.read_text()`, `hashlib.sha256(Path.read_bytes())` e contagem literal de anchors/fences → `documents=9`, `words=16239`, `mermaid_fences=21`, `catalog_anchors=103`, `missing_catalog_anchors=[]`, `duplicate_catalog_anchors=[]`, `priority_anchors=18`.

Essas contagens são inventário mecânico. Não medem qualidade semântica, correção Mermaid, build ou revisão.

| Arquivo | SHA256 | Palavras | Mermaid |
|---|---|---:|---:|
| `content/explicacoes/reliable-integration/index.mdx` | `127c54a80e554a10d55963b52b4e7a924bcb12214f90e7739d5adc8c8c597109` | 1653 | 4 |
| `content/explicacoes/messages/index.mdx` | `e017756a5accc42f79cfbb45fbac8bf02d9471ff31c23c23a03793849188cb4f` | 1857 | 5 |
| `content/explicacoes/read-models/index.mdx` | `40ebbdadc0d69b331005ba7d3583567ff8971b34b256ec6e7add5573b2108240` | 1428 | 4 |
| `content/explicacoes/data-durability/index.mdx` | `4a0bc76a5691adbea0e7615a848180f4f905ae6b213d34d7ff21ca99a7d9c645` | 1306 | 4 |
| `content/explicacoes/data-distribution/index.mdx` | `b79b33e38f81d2d2158eee2f453406a38ac842e8705a3771ae7a819bdeddda2e` | 1714 | 4 |
| `content/referencia/catalogo/02-sistemas-distribuidos-e-consistencia.mdx` | `8e3ce58db06fd90bc157a44bc7602d73ac33e9c3c52947187c549c982098f617` | 3100 | 0 |
| `content/referencia/catalogo/03-event-driven-messaging.mdx` | `6af14ef3e0eef7488fe552e0c7e7eb1747ec9365536b007e0f7724fd185406f6` | 1911 | 0 |
| `content/referencia/catalogo/04-cqrs-event-sourcing-e-modelos-de-leitura.mdx` | `b083078bf6cbb0aef1c9b9a2cf47ceb2f4483ee00067fbbc0c6b7b7f8cf0b1d4` | 911 | 0 |
| `content/referencia/catalogo/05-banco-de-dados-e-armazenamento.mdx` | `c524241d60a938458406eac41128c6c49e069752e69ab75269161e4f420160d7` | 2359 | 0 |

## Âncoras dos prioritários sob S4

Os 18 itens deste recorte possuem uma seção com o nome do padrão e um anchor estável. Os demais 22 prioritários dos 40 pertencem aos outros autores; S4 não declara cobertura deles por esta tabela.

| ID | Padrão | Caminho e anchor |
|---:|---|---|
| 5 | Event-Driven Architecture | `content/explicacoes/messages/index.mdx#pattern-5` |
| 6 | Pub/Sub | `content/explicacoes/messages/index.mdx#pattern-6` |
| 7 | Transactional Outbox | `content/explicacoes/reliable-integration/index.mdx#pattern-7` |
| 8 | CDC | `content/explicacoes/reliable-integration/index.mdx#pattern-8` |
| 9 | Saga | `content/explicacoes/reliable-integration/index.mdx#pattern-9` |
| 10 | Idempotency | `content/explicacoes/messages/index.mdx#pattern-10` |
| 11 | CQRS | `content/explicacoes/read-models/index.mdx#pattern-11` |
| 12 | Event Sourcing | `content/explicacoes/read-models/index.mdx#pattern-12` |
| 13 | Materialized Views / Projections | `content/explicacoes/read-models/index.mdx#pattern-13` |
| 28 | Leader Election | `content/explicacoes/data-durability/index.mdx#pattern-28`; desenvolvimento operacional em S6 `availability` |
| 29 | Distributed Lock + Lease + Fencing | `content/explicacoes/data-distribution/index.mdx#pattern-29`; desenvolvimento principal em S5 `concurrency` |
| 30 | Replication | `content/explicacoes/data-durability/index.mdx#pattern-30` |
| 31 | Sharding | `content/explicacoes/data-distribution/index.mdx#pattern-31` |
| 32 | Consistent Hashing | `content/explicacoes/data-distribution/index.mdx#pattern-32` |
| 33 | Optimistic Concurrency | `content/explicacoes/data-distribution/index.mdx#pattern-33`; desenvolvimento principal em S5 `concurrency` |
| 34 | WAL | `content/explicacoes/data-durability/index.mdx#pattern-34` |
| 38 | Competing Consumers | `content/explicacoes/messages/index.mdx#pattern-38`; ligação com executor e DAG em S3 `workflow` |
| 39 | Dead Letter Queue | `content/explicacoes/messages/index.mdx#pattern-39` |

## Ocorrências das referências

O inventário lido encontrou os anchors `g02-e001` a `g02-e038`, `g03-e001` a `g03-e025`, `g04-e001` a `g04-e011` e `g05-e001` a `g05-e029`. A soma é 38 + 25 + 11 + 29 = 103. As ocorrências de Read Replica no grupo 5 têm seções distintas, por replicação e por leitura. Cada seção redige definição, caso, custo, limite e apoio de skill/framework/OSS ou lacuna específica. Essa é a intenção de autoria; a correção de cada item depende do council.

## Fontes e fronteiras preservadas

O código MakersHub permanece identificado pelo SHA `e233fb046ec333982cd1547171b0f0bd8d8d92ee`. `ReportReadService` e `ReportPersistenceService` são um caso delimitado de separação de leitura e alteração. O PR 362 é citado pelo snapshot OPEN, source/target e 601 arquivos; sua introdução do CQRS não é afirmada.

A flag de outbox representa intenção de sincronização, sem promessa de stream completo. O UUID de claim valida ownership local, sem fencing monotônico no Salesforce. As 4.771 linhas `done` não são prova de efeitos externos Exactly Once; zero pendências D1 não é prova de sincronização completa.

A captação usa a medição original de 15:56:30 UTC: 557.731 linhas, 3.380 movimentos de outubro, soma assinada de R$ 18.742.122,16 e data máxima 08/10/2026. O objeto tem `relkind=r` no recibo das 16:07:16 UTC. Não é chamado de view materializada nativa, receita ou fechamento mensal.

WAL minimal no banco `.137` permanece separado do banco CloudNativePG de metadados Airflow. CDC lógico, streaming físico e PITR nessa instância aparecem como mecanismos e propostas, sem prova de habilitação. Outbox polling não exige CDC/broker; CQRS não exige Event Sourcing; auditoria não comprova reconstrução por eventos.

As explicações preservam suposições de quórum, distinções de relógios e leituras de sessão, bloqueio de 2PC e modelo de falhas de 3PC. Saga não é classificada universalmente como AP, não remove o isolamento de cada transação local e não exige outbox em todo desenho. TCC, reservas, pivô e ações irreversíveis são casos hipotéticos explícitos.

## Fontes complementares lidas na autoria

As fontes dos três auxiliares foram reutilizadas. S4 acrescentou leituras pontuais de documentação primária em 14/10/2026, sem nova consulta SQL: PostgreSQL 16 partitioning, index-only scans, REFRESH MATERIALIZED VIEW, standby, PREPARE TRANSACTION e isolation; Vitess 23 sharding e vindexes; componentes Loki; RocksDB Overview; Btrfs Introduction; Paxos Made Simple e Time, Clocks de Lamport.

A consulta web de `https://galeracluster.com/documentation/html_docs/architecture.html` devolveu `URL ... is not accessible via this tool`. Por isso ela não é fonte verificada para Multi-Leader/Multi-Primary. A lacuna ficou explícita, sem inferir ausência global de uma solução.

Os localizadores locais de 14 skills usadas foram conferidos com `Path.is_file()` e devolveram EXISTS. Os MDX usam caminhos locais apenas como texto; os links de documentação, código OSS e PR são HTTP, e os links da trilha são rotas Nextra.

## Gates a cargo da raiz

`MDX_BUILD=PENDING`; `LINK_VALIDATION=PENDING`; `MERMAID_PARSE=PENDING`; `MERMAID_RENDER=PENDING`; `SEMANTIC_REVIEW=PENDING`. As 21 fences precisam de extração, parsing, renderização e conferência contra as fontes. S4 não produziu recibo de aprovação própria, não editou índices/meta, não alterou coverage/packet e não abriu subagentes.
