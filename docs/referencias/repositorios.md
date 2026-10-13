# Repositórios GitHub de referência

## Clonados neste repositório

Em [`references/repos/`](../../references/repos/) (clone `--depth 1`):

| Repositório | Papel | Local |
|---|---|---|
| `debezium/debezium` | CDC / log mining — implementação OSS canônica | `references/repos/debezium` |
| `temporalio/temporal` | Durable execution / workflow orchestration (Sagas) | `references/repos/temporal` |
| `eventuate-tram/eventuate-tram-sagas` | Orquestração de Saga (didática) | `references/repos/eventuate-tram-sagas` |
| `ThreeDotsLabs/watermill` | Event-driven systems em Go | `references/repos/watermill` |
| `kgrzybek/modular-monolith-with-ddd` | Modular Monolith + DDD (produção) | `references/repos/modular-monolith-with-ddd` |
| `ThreeDotsLabs/wild-workouts-go-ddd-example` | DDD + Clean/Hexagonal + CQRS | `references/repos/wild-workouts-go-ddd-example` |
| `oskardudycz/EventSourcing.NetCore` | Event Sourcing, CQRS, Outbox/Inbox, Sagas | `references/repos/EventSourcing.NetCore` |
| `JasperFx/marten` | Event store + document DB + projections (PostgreSQL) | `references/repos/marten` |
| `JasperFx/wolverine` | Mensageria + command handling (.NET) | `references/repos/wolverine` |
| `resilience4j/resilience4j` | Resiliência JVM (CircuitBreaker, Retry, Bulkhead, RateLimiter) | `references/repos/resilience4j` |
| `mehdihadeli/awesome-software-architecture` | Curadoria: Hexagonal, VSA, EDA, DDD, CQRS, modular monolith | `references/repos/awesome-software-architecture` |

E o handbook em [`references/data-engineer-handbook/`](../../references/data-engineer-handbook/).

## Papers acadêmicos e fundamentos teóricos

- **papers-we-love/papers-we-love** (`distributed_systems/`) — Raft, Paxos Made Simple, Dynamo,
  Spanner, MapReduce.
- **theanalyst/awesome-distributed-systems** — livros, papers, palestras, cursos (MIT 6.824).
- **ept/ddia-references** — fontes citadas no *Designing Data-Intensive Applications*.

## Padrões, decisões e system design

- **binhnguyennus/awesome-scalability** — problemas de escalabilidade por tópico (Availability,
  Caching, Consensus, Idempotence, Async Architectures).
- **donnemartin/system-design-primer** — design de sistemas em larga escala com trade-offs.
- **mehdihadeli/awesome-software-architecture** — DDD, Clean Architecture, CQRS, Event Sourcing,
  Outbox, Sagas.
- **joelparkerhenderson/architecture-decision-record** — exemplos de ADRs.

## Implementações canônicas adicionais (não clonadas)

| Repositório | Papel |
|---|---|
| `AxonFramework/AxonFramework` | CQRS/Event Sourcing/mensageria (Java) |
| `EventStore/EventStore` | Event store append-only |
| `dapr/dapr` | Building blocks distribuídos (pub/sub, state, workflows, sidecar) |
| `redpanda-data/redpanda` | Streaming Kafka-compatible |
| `nats-io/nats-server` | Messaging simples e rápido |
| `envoyproxy/envoy` | Data plane / proxy distribuído |
| `apache/apisix` | API Gateway |
| `traefik/traefik` | Reverse proxy / ingress |
| `argoproj/argo-rollouts` | Blue/Green, Canary, progressive delivery |
| `argoproj/rollouts-demo` | Demo para estudar progressive delivery |
| `argoproj/argo-cd` | GitOps |
| `Unleash/unleash` | Feature flags |
| `etcd-io/etcd` | Consenso (Raft), CAS, leases, leader election |
| `hazelcast/hazelcast` | CP subsystem, FencedLock, primitivas distribuídas |
| `vitessio/vitess` | Sharding MySQL horizontal |
| `cockroachdb/cockroach` | Distributed SQL |
| `tikv/tikv` | Distributed transactional KV + Raft |
| `grafana/loki` | Consistent hashing / ring / memberlist em produção |
| `istio/istio` | Service mesh (completa) |
| `linkerd/linkerd2` | Service mesh (leve) |
| `statelyai/xstate` | State machines / statecharts / actor model |
| `celery/celery` | Worker queues / competing consumers |
| `apache/superset` | Aplicação real com Celery/Redis/async tasks |
| `kubernetes/kubernetes` | Aplicação real dos padrões em escala |
| `dotnet/eShop` | Referência com BFF (YARP/mobile-bff) |
| `vert-x3 / vertical-slice-dotnet` | Referência de Vertical Slice |
| `ddd-by-examples/library` | DDD |

## Como usar este corpus

1. **Entenda o conceito** nos docs deste repositório ([`docs/`](../../docs/README.md)).
2. **Leia o código** do repositório de referência para o padrão.
3. **Compare trade-offs** antes de aplicar (ver [`docs/consistencia/`](../../docs/consistencia/)).
4. **Aplique** considerando sua stack concreta (ver [`docs/aplicado/`](../../docs/aplicado/)).
