# Catálogo completo de padrões de arquitetura

Organizado por **nível arquitetural**. Um padrão como "Dual Write" não está no mesmo nível de
"MVC", "Hexagonal" ou "Factory" — ele é um padrão de consistência/integração de dados.

## Índice

1. [Arquiteturas de aplicação](#1-arquiteturas-de-aplicação)
2. [Sistemas distribuídos e consistência](#2-sistemas-distribuídos-e-consistência)
3. [Event-driven / Messaging](#3-event-driven--messaging)
4. [CQRS, Event Sourcing e modelos de leitura](#4-cqrs-event-sourcing-e-modelos-de-leitura)
5. [Banco de dados e armazenamento](#5-banco-de-dados-e-armazenamento)
6. [Cache](#6-cache)
7. [Resiliência](#7-resiliência)
8. [Concorrência](#8-concorrência)
9. [APIs e integração](#9-apis-e-integração)
10. [DDD](#10-ddd--domain-driven-design)
11. [Padrões para decompor sistemas](#11-padrões-para-decompor-sistemas)
12. [Deploy e releases](#12-deploy-e-releases)
13. [Alta disponibilidade](#13-alta-disponibilidade)
14. [Segurança](#14-segurança)
15. [Observabilidade](#15-observabilidade)
16. [Workflow e processamento](#16-workflow-e-processamento)
17. [Padrões clássicos GoF](#17-padrões-clássicos-gof)
18. [O core moderno: 40 padrões](#18-o-core-moderno-40-padrões)

---

## 1. Arquiteturas de aplicação

| Pattern | Uso principal |
|---|---|
| Layered / N-Tier | UI → Service → Domain → Data |
| Modular Monolith | Monólito dividido em módulos fortemente isolados |
| Microservices | Serviços independentes por domínio |
| SOA | Serviços corporativos compartilhados |
| Serverless | Execução baseada em funções/eventos |
| Microkernel / Plugin Architecture | Core pequeno + plugins |
| Hexagonal / Ports & Adapters | Domínio isolado de infra/framework |
| Clean Architecture | Dependências apontam para o domínio |
| Onion Architecture | Domínio no centro, infraestrutura externa |
| Vertical Slice Architecture | Organização por feature/use case |
| MVC | Model / View / Controller |
| MVP | Model / View / Presenter |
| MVVM | Model / View / ViewModel |
| PAC | Presentation-Abstraction-Control |
| Component-Based Architecture | Sistema composto por componentes |
| Space-Based Architecture | Estado distribuído em memória; alta escala |
| Cell-Based Architecture | Sistema dividido em células independentes |
| Actor Model | Entidades independentes comunicando por mensagens |
| Peer-to-Peer | Nós equivalentes |
| Blackboard Architecture | Múltiplos agentes sobre estado comum |
| Pipe and Filter | Transformações sequenciais |
| Event-Driven Architecture | Eventos como principal mecanismo de integração |

## 2. Sistemas distribuídos e consistência

| Pattern | Ideia |
|---|---|
| Dual Write | Escrever em dois sistemas na mesma operação |
| Transactional Outbox | DB + evento escritos na mesma transação |
| Transactional Inbox | Registrar mensagens recebidas para evitar duplicação |
| Outbox + CDC | DB grava outbox; CDC publica no broker |
| Change Data Capture (CDC) | Capturar mudanças do log do banco |
| Saga | Transações distribuídas com etapas + compensações |
| Choreography Saga | Serviços reagem a eventos |
| Orchestration Saga | Orquestrador controla a saga |
| Two-Phase Commit / 2PC | Commit distribuído coordenado |
| Three-Phase Commit / 3PC | Variante de commit distribuído |
| TCC — Try/Confirm/Cancel | Reserva → confirmação → cancelamento |
| Compensating Transaction | Desfazer semanticamente operação anterior |
| Reservation Pattern | Reservar recurso antes do commit definitivo |
| Idempotency | Repetir operação sem efeitos adicionais |
| Idempotency Key | Identificador da operação para deduplicação |
| Deduplication | Detectar mensagens/operações repetidas |
| Exactly Once Semantics | Efeito lógico exatamente uma vez |
| At-Least-Once Delivery | Pode duplicar; consumidor deve ser idempotente |
| At-Most-Once Delivery | Pode perder; nunca duplica |
| Eventual Consistency | Réplicas convergem posteriormente |
| Strong Consistency | Leitura vê estado confirmado |
| Read-your-writes | Cliente vê suas próprias alterações |
| Monotonic Reads | Leituras nunca voltam para versão mais antiga |
| Optimistic Concurrency Control | Detecta conflito no commit |
| Pessimistic Locking | Bloqueia recurso antecipadamente |
| Distributed Lock | Lock coordenado entre máquinas |
| Lease | Lock com expiração |
| Fencing Token | Token crescente evita escritor antigo |
| Compare-and-Swap / CAS | Atualiza somente se versão esperada coincidir |
| Version Vector | Detectar causalidade/conflitos |
| Lamport Clock | Ordem lógica distribuída |
| Hybrid Logical Clock | Tempo físico + lógico |
| Quorum Read/Write | R + W > N para consistência |
| Leader Election | Eleição de nó coordenador |
| Consensus | Nós concordam sobre estado |
| Raft | Algoritmo de consenso |
| Paxos | Família clássica de consenso |
| Gossip Protocol | Nós disseminam estado entre si |

> **Dual Write direto** tem o problema clássico `PostgreSQL ✅ / Kafka ❌` → estado inconsistente.
> Por isso substitui-se por: `Dual Write → Transactional Outbox → CDC → Broker`.

## 3. Event-driven / Messaging

| Pattern | Uso |
|---|---|
| Publish/Subscribe | Muitos consumidores recebem eventos |
| Message Queue | Distribuição de trabalho |
| Competing Consumers | Workers consomem fila em paralelo |
| Producer/Consumer | Produtor desacoplado do consumidor |
| Request/Reply | RPC através de mensagens |
| Fire-and-Forget | Produtor não espera resposta |
| Fan-out | Evento distribuído para múltiplos destinos |
| Fan-in | Combinar múltiplos fluxos |
| Message Router | Decide destino da mensagem |
| Content-Based Router | Roteamento baseado no payload |
| Message Filter | Descarta mensagens irrelevantes |
| Message Translator | Converte schemas |
| Message Enricher | Adiciona dados |
| Splitter | Uma mensagem vira várias |
| Aggregator | Várias mensagens viram uma |
| Resequencer | Reordena mensagens |
| Correlation ID | Liga mensagens da mesma operação |
| Dead Letter Queue | Eventos que falharam permanentemente |
| Retry Queue | Reprocessamento posterior |
| Delayed Queue | Processamento futuro |
| Priority Queue | Prioridade de processamento |
| Poison Message Handling | Isola mensagens problemáticas |
| Event Notification | Evento apenas informa mudança |
| Event-Carried State Transfer | Evento carrega estado suficiente |
| Event Streaming | Log contínuo de eventos |

## 4. CQRS, Event Sourcing e modelos de leitura

| Pattern | Ideia |
|---|---|
| CQRS | Separar comandos de consultas |
| Event Sourcing | Eventos são a fonte de verdade |
| Projection | Construir estado derivado de eventos |
| Materialized View | Pré-computar representação para leitura |
| Read Model | Banco/modelo otimizado para consulta |
| Write Model | Modelo otimizado para comando |
| Snapshotting | Snapshot periódico do Event Sourcing |
| Command Handler | Processa comandos |
| Query Handler | Processa consultas |
| Domain Events | Mudanças importantes no domínio |
| Integration Events | Eventos publicados entre bounded contexts |

## 5. Banco de dados e armazenamento

**Replicação:** Primary/Replica · Leader/Follower · Multi-Leader · Multi-Primary ·
Active/Passive · Active/Active · Read Replica · Cascading Replication · Synchronous Replication ·
Asynchronous Replication

**Particionamento:** Horizontal Partitioning · Vertical Partitioning · Sharding · Range Sharding ·
Hash Sharding · Directory-Based Sharding · Geographic Sharding · Consistent Hashing

**Escrita:** Write-Ahead Log (WAL) · Append-Only Log · Copy-on-Write · Log Structured Storage ·
Write Amplification Control

**Leitura:** Read Replica · Materialized View · Indexing · Covering Index · Denormalization ·
Precomputation

## 6. Cache

| Pattern | Funcionamento |
|---|---|
| Cache Aside | Aplicação lê DB e popula cache |
| Read Through | Cache carrega dados automaticamente |
| Write Through | Escrita atualiza cache + storage |
| Write Behind / Write Back | Cache grava storage depois |
| Refresh Ahead | Atualiza cache antes de expirar |
| TTL Cache | Expiração temporal |
| Negative Caching | Cachear ausência de resultado |
| Distributed Cache | Cache compartilhado |
| Local Cache | Cache por processo |
| Two-Level Cache | L1 local + L2 Redis |
| Cache Stampede Protection | Evitar milhares de recomputações |
| Single Flight | Apenas uma requisição recalcula |
| Cache Warming | Pré-carregar cache |
| Cache Invalidation | Invalidar quando fonte muda |

> **Relevante para o MakersHub:** `L1 process memory → L2 Redis → PostgreSQL` com
> `cache-aside + refresh-ahead + single-flight + event-driven invalidation`.

## 7. Resiliência

| Pattern | Problema resolvido |
|---|---|
| Retry | Falhas transitórias |
| Exponential Backoff | Evitar retry agressivo |
| Jitter | Evitar synchronized retries |
| Circuit Breaker | Serviço quebrado não recebe chamadas infinitamente |
| Bulkhead | Falha de um componente não derruba outros |
| Timeout | Limitar espera |
| Deadline Propagation | Prazo atravessa cadeia de serviços |
| Fallback | Resposta alternativa |
| Fail Fast | Falhar cedo |
| Graceful Degradation | Sistema continua parcialmente |
| Load Shedding | Rejeita carga excedente |
| Backpressure | Consumidor controla ritmo |
| Rate Limiting | Limita volume |
| Throttling | Reduz consumo |
| Health Check | Detectar instância problemática |
| Heartbeat | Detectar nós vivos |
| Watchdog | Detectar processos travados |
| Self-Healing | Reiniciar/substituir componente |
| Chaos Engineering | Testar resiliência ativamente |

## 8. Concorrência

Mutex · Semaphore · Reader/Writer Lock · Spinlock · Optimistic Locking · Pessimistic Locking ·
Lock-Free · Wait-Free · Compare-and-Swap · Actor Model · Thread Pool · Worker Pool ·
Producer/Consumer · Work Stealing · Fork/Join · Futures/Promises · Async/Await ·
Reactive Streams · Backpressure · Single Writer Principle · Immutable Data · Copy-on-Write

## 9. APIs e integração

| Pattern | Aplicação |
|---|---|
| API Gateway | Entrada central de APIs |
| Backend for Frontend (BFF) | API específica para cada frontend |
| Gateway Aggregation | Junta respostas de vários serviços |
| Gateway Routing | Roteia para serviços |
| Gateway Offloading | Auth/TLS/rate limit no gateway |
| Reverse Proxy | Proxy na frente dos serviços |
| Service Mesh | Comunicação service-to-service |
| Sidecar | Infra junto ao processo |
| Ambassador | Proxy local para comunicação externa |
| Adapter | Converte interfaces |
| Anti-Corruption Layer | Protege domínio de sistema externo |
| Facade | Interface simplificada |
| Proxy | Intermediário transparente |
| API Composition | Agregação de serviços |
| GraphQL Federation | Vários schemas unidos |
| RPC | Chamada remota |
| REST | Recursos HTTP |
| HATEOAS | Navegação via links |
| Webhook | Notificação HTTP reversa |
| Polling | Perguntar periodicamente |
| Long Polling | Polling prolongado |
| Server-Sent Events | Stream unidirecional HTTP |
| WebSocket | Canal bidirecional |

## 10. DDD — Domain-Driven Design

Bounded Context · Ubiquitous Language · Entity · Value Object · Aggregate · Aggregate Root ·
Domain Service · Application Service · Repository · Factory · Domain Event · Domain Policy ·
Specification · Anti-Corruption Layer · Context Map · Shared Kernel · Customer/Supplier ·
Conformist · Open Host Service · Published Language · Separate Ways

## 11. Padrões para decompor sistemas

**Strangler Fig** — substituir o sistema antigo gradualmente:

```
                 ┌─ Legacy
Client → Router ─┤
                 └─ New System
```

Até o legado desaparecer. Outros: Branch by Abstraction · Parallel Run · Shadow Traffic ·
Dark Launch · Feature Toggle · Expand/Contract · Transitional Architecture · Modularization ·
Service Extraction · Database Decomposition · CDC Migration · Dual Write Migration

## 12. Deploy e releases

Blue/Green Deployment · Canary Release · Rolling Deployment · Recreate Deployment ·
Shadow Deployment · Dark Launch · Feature Flags · Progressive Delivery · A/B Deployment ·
Immutable Infrastructure · Infrastructure as Code · GitOps

## 13. Alta disponibilidade

Active/Active · Active/Passive · Hot Standby · Warm Standby · Cold Standby · Multi-AZ ·
Multi-Region · Leader/Follower · Quorum · Failover · Automatic Failover ·
Split-Brain Prevention · Fencing · Heartbeat · Leader Election · Replication · Stateless Services

## 14. Segurança

Zero Trust · Defense in Depth · Least Privilege · RBAC · ABAC · ReBAC ·
Policy-Based Access Control · OAuth2 · OIDC · Token Exchange · Short-Lived Credentials ·
Secrets Rotation · mTLS · API Gateway Security · Service-to-Service Identity · Bastion Host ·
Network Segmentation

## 15. Observabilidade

Structured Logging · Centralized Logging · Distributed Tracing · Correlation ID · Request ID ·
Metrics · **RED Method** (Rate, Errors, Duration) · **USE Method** (Utilization, Saturation,
Errors) · Golden Signals · OpenTelemetry · Health Checks · Synthetic Monitoring

## 16. Workflow e processamento

State Machine · Finite State Machine · Workflow Engine · DAG · Pipeline · Orchestrator ·
Choreography · Job Queue · Worker Pool · Batch Processing · Stream Processing ·
Lambda Architecture · Kappa Architecture · MapReduce · Scatter/Gather · Fork/Join

## 17. Padrões clássicos GoF

> São padrões de **código**, não de arquitetura distribuída.

- **Creational:** Singleton · Factory Method · Abstract Factory · Builder · Prototype
- **Structural:** Adapter · Bridge · Composite · Decorator · Facade · Flyweight · Proxy
- **Behavioral:** Chain of Responsibility · Command · Interpreter · Iterator · Mediator ·
  Memento · Observer · State · Strategy · Template Method · Visitor

## 18. O core moderno: 40 padrões

Se fosse montar um core de conhecimento para arquitetura moderna, priorizaria estes 40:

1. Modular Monolith
2. Hexagonal Architecture
3. Vertical Slice
4. DDD / Bounded Context
5. Event-Driven Architecture
6. Pub/Sub
7. Transactional Outbox
8. CDC
9. Saga
10. Idempotency
11. CQRS
12. Event Sourcing
13. Materialized Views / Projections
14. Cache Aside
15. Refresh Ahead
16. Circuit Breaker
17. Retry + Exponential Backoff + Jitter
18. Bulkhead
19. Backpressure
20. Rate Limiting
21. API Gateway
22. BFF
23. Strangler Fig
24. Expand/Contract
25. Blue/Green
26. Canary
27. Feature Flags
28. Leader Election
29. Distributed Lock + Lease + Fencing
30. Replication
31. Sharding
32. Consistent Hashing
33. Optimistic Concurrency
34. WAL
35. Sidecar
36. Service Mesh
37. Anti-Corruption Layer
38. Competing Consumers
39. Dead Letter Queue
40. State Machine

> **Distinção importante:** Dual Write é um problema a ser controlado, não a arquitetura final
> desejável. A evolução típica é:
> `Dual Write → Outbox → CDC → Event Broker → Idempotent Consumers → Saga/CQRS quando necessário`.

Ver o mapeamento de **skills, frameworks e OSS** para cada um destes 40 em
[`docs/referencias/catalogo-40-patterns-skills-frameworks.md`](../referencias/catalogo-40-patterns-skills-frameworks.md).
