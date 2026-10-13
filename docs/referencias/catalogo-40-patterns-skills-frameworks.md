# Catálogo: 40 padrões × skills × frameworks × aplicações OSS

> `PROD` = sistema/aplicação OSS de produção real. `REF` = aplicação de referência feita para
> demonstrar a arquitetura.

| # | Pattern | Skill | Framework/lib base | OSS para estudar |
|---|---|---|---|---|
| 1 | Modular Monolith | S1 `architecture-patterns` + S2 | Spring Modulith | `kgrzybek/modular-monolith-with-ddd` REF |
| 2 | Hexagonal / Ports & Adapters | S1 | Spring Boot + ArchUnit / Watermill | `ThreeDotsLabs/wild-workouts-go-ddd-example` REF |
| 3 | Vertical Slice | S1/S2 | ASP.NET Minimal APIs + MediatR/Wolverine | `vertical-slice-dotnet` REF |
| 4 | DDD / Bounded Context | S1 | Spring Modulith / Axon | `ddd-by-examples/library`, Wild Workouts REF |
| 5 | Event-Driven Architecture | S2 + S7 | Dapr / Watermill / Redpanda | eShop / Eventuate examples |
| 6 | Pub/Sub | S7 | NATS / Redpanda / Dapr | Apache Superset PROD |
| 7 | Transactional Outbox | S2 | Eventuate Tram / Debezium Outbox | Eventuate Customers & Orders REF |
| 8 | CDC | S2 | Debezium | Airbyte PROD |
| 9 | Saga | S2 + S8 | Temporal / Eventuate Tram Sagas | Eventuate Customers & Orders REF |
| 10 | Idempotency | S2 + S7 | Temporal / Redpanda/Kafka | Temporal samples + Temporal PROD |
| 11 | CQRS | S2 | Axon / Wolverine / Marten | Wild Workouts / Eventuate REF |
| 12 | Event Sourcing | S2 | Marten / EventStoreDB / Axon | `EventSourcing.NetCore` REF |
| 13 | Materialized Views / Projections | S2 | PostgreSQL / Marten | Eventuate Order History REF |
| 14 | Cache Aside | S2 | Redis | Apache Superset PROD |
| 15 | Refresh Ahead | S2 | Redis / Caffeine | Caffeine integrations / large JVM apps |
| 16 | Circuit Breaker | S2 | Resilience4j / Envoy | Envoy PROD |
| 17 | Retry + Backoff + Jitter | S2 | Temporal / Resilience4j | Temporal PROD |
| 18 | Bulkhead | S2 | Resilience4j | Envoy / Spring ecosystem |
| 19 | Backpressure | S2/S7 | Reactor / RxJava / NATS | Apache Beam PROD |
| 20 | Rate Limiting | S2 | Envoy / APISIX / Resilience4j | APISIX PROD |
| 21 | API Gateway | S2 | APISIX / Envoy / Traefik | APISIX PROD |
| 22 | BFF | S2 | YARP / Envoy | `dotnet/eShop` REF |
| 23 | Strangler Fig | S1/S2 | Envoy / Traefik | migration reference apps |
| 24 | Expand / Contract | S1/S2 | Flyway / Liquibase | Discourse/GitLab-style migrations |
| 25 | Blue/Green | S1 | Argo Rollouts | `argoproj/rollouts-demo` REF |
| 26 | Canary | S1 | Argo Rollouts / Flagger | `argoproj/rollouts-demo` REF |
| 27 | Feature Flags | S1/S2 | Unleash | Unleash PROD |
| 28 | Leader Election | S1/S2 | etcd / Kubernetes client-go | Kubernetes PROD |
| 29 | Distributed Lock + Lease + Fencing | S2 | etcd / Hazelcast FencedLock | Kubernetes / Hazelcast PROD |
| 30 | Replication | S1/S2 | PostgreSQL / etcd/Raft | CockroachDB / TiKV PROD |
| 31 | Sharding | S1/S2 | Vitess | Vitess PROD |
| 32 | Consistent Hashing | S2 | Hashicorp/memberlist / consistent | Grafana Loki PROD |
| 33 | Optimistic Concurrency | S2 | PostgreSQL / Marten | `EventSourcing.NetCore` REF |
| 34 | WAL | S2/S3 | PostgreSQL / RocksDB | PostgreSQL PROD |
| 35 | Sidecar | S1 | Dapr / Envoy | Kubernetes / Dapr PROD |
| 36 | Service Mesh | S1 | Istio / Linkerd | Istio Bookinfo REF + deployments |
| 37 | Anti-Corruption Layer | S1/S2 | MapStruct/Camel + domain adapters | Wild Workouts / DDD examples REF |
| 38 | Competing Consumers | S2 | Celery / NATS / RabbitMQ | Apache Superset PROD |
| 39 | Dead Letter Queue | S2/S7 | RabbitMQ / NATS JetStream / Kafka | broker reference applications |
| 40 | State Machine | S2 | XState / Temporal | Temporal workflows / XState examples |

## Combinações em destaque

### Modular Monolith
- **Framework:** Spring Modulith — verifica automaticamente fronteiras de módulos, testes isolados
  por módulo, documentação estrutural e comunicação por eventos (~1k★).
- **Referência:** `kgrzybek/modular-monolith-with-ddd` (~14k★) — modular monolith + DDD, voltado a
  uso real. Muito mais valioso que começar um template do zero.

### Hexagonal + DDD + CQRS
- **Referência:** `ThreeDotsLabs/wild-workouts-go-ddd-example` (~6.4k★) — DDD + Clean/Hexagonal +
  CQRS + repositories + gRPC + Terraform.
- **Base Go:** `ThreeDotsLabs/watermill` (~10k★) para event-driven.

### Saga / Distributed transactions
- **Base principal:** `temporalio/temporal` (~23k★) — *durable execution* com compensações duráveis
  (`reserve inventory → charge payment → create shipment` / `cancel shipment → refund payment →
  release inventory`).
- **Didática:** `eventuate-tram/eventuate-tram-sagas` (~1.1k★).
- **Aplicação:** **Eventuate Customers and Orders** — Saga + CQRS + microserviços.

### Transactional Outbox
- Stack madura: `PostgreSQL → Transactional Outbox → Debezium → Redpanda → consumidor idempotente`.
- **Debezium** (~13k★) é uma das implementações OSS canônicas de CDC.

### CQRS + Event Sourcing
- **Axon Framework** (~3.6k★) · **Marten** (~3.5k★) · **Wolverine** (~2.4k★).
- **Melhor biblioteca de exemplos:** `oskardudycz/EventSourcing.NetCore` (~3.7k★) — Event Sourcing,
  CQRS, projections, snapshots, optimistic concurrency, Outbox/Inbox, Saga e process managers.

### Event-driven / Pub-Sub
- **Redpanda** (~12.6k★) · **NATS** (~20.8k★) · **Dapr** (~26k★). Redpanda tem Agent Skills oficiais.

### Resilience
- **Resilience4j** (~10.8k★): CircuitBreaker, Retry, RateLimiter, Bulkhead, TimeLimiter, Cache.
- **Envoy** (~29k★): resolve parte desses patterns **no nível de rede** — retry, timeout, circuit
  breaking, load balancing e telemetria **fora de cada aplicação**.

### API Gateway / Reverse Proxy
- **Traefik** (~65k★) · **Envoy** (~29k★) · **Apache APISIX** (~17k★). APISIX é interessante como
  produto; Envoy é primitiva mais baixa.

### BFF
- `dotnet/eShop` (~11k★) — mantém BFF, incluindo `mobile-bff` baseado em YARP.

### Cache
- **Redis** (~76k★). Mas não pense `Redis = cache`; a combinação completa é
  `L1 local → L2 Redis → PostgreSQL` + cache-aside + single-flight + TTL jitter + refresh-ahead +
  event-driven invalidation.

### Worker queues / Competing Consumers
- **Celery** (~29k★) · aplicação real: **Apache Superset** (~75k★) com Celery + Redis + async tasks.

### State Machine
- **XState** (~30k★): state machine + statecharts + actor model. XState v5 trata machines como
  actors (actors filhos, promises, eventos, orchestration).
- `XState → estado/orquestração de app` · `Temporal → workflows distribuídos duráveis`. **Não são
  substitutos diretos.**

### Deployment progressivo
- **Argo Rollouts** (~3.6k★): Canary, Blue/Green, progressive delivery, analysis, promoção e
  rollback automáticos. Demo: `argoproj/rollouts-demo`. GitOps: **Argo CD** (~24k★).

### Feature Flags
- **Unleash** (~14k★). Desacopla `deployment ≠ release`.

### Consensus / Leader Election / Lease
- **etcd** — KV distribuído fortemente consistente (Raft), base de coordenação do Kubernetes:
  Consensus, CAS, leases, leader election, watch, quorum. Aplicação: **Kubernetes** (~128k★).

### Distributed Lock + Fencing
- `SETNX` no Redis **não** é coordenação forte. Prefira `etcd lease + fencing token monotônico` ou
  CP systems como **Hazelcast** (~6.6k★) com `FencedLock`.

### Replication
- **CockroachDB** (~32k★) · **TiKV** (~17k★) · **PostgreSQL** — WAL + streaming replication.

### Sharding
- **Vitess** (~21k★) — nasceu para escalar MySQL; implementa sharding, routing, topology, resharding.

### Consistent Hashing / Ring
- **Grafana Loki** (~29k★) — ring + memberlist/gossip.

### Service Mesh
- **Istio** (completa) · **Linkerd** (~11.5k★, leve). Trade-off operacional comunitário.

### Observabilidade (transversal)
- **OpenTelemetry Collector** (~7.6k★) · **Jaeger** (~23k★) · **Grafana Loki** (~29k★).

## O dual write que originou tudo

Criaria a skill como `dual-write-and-consistency`, ensinando principalmente **quando NÃO** fazer
dual-write. Árvore de decisão:

```
Preciso alterar dois sistemas?
        │
        ├── mesma DB?            └── transaction
        ├── DB + broker?         └── Transactional Outbox + CDC
        ├── operação distribuída longa?  └── Saga / Temporal
        ├── reserva/confirm/cancel?      └── TCC
        └── realmente exige atomicidade global?  └── avaliar 2PC
```

**Framework de referência:** Eventuate Tram + Debezium.
**Aplicação:** Eventuate Customers and Orders (Saga + CQRS + Outbox juntos).
