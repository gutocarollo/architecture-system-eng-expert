# references/ — fontes clonadas

Corpus de fontes clonadas neste repositório.

## data-engineer-handbook

`data-engineer-handbook/` — clone de [`dataexpert-io/data-engineer-handbook`](https://github.com/dataexpert-io/data-engineer-handbook).

## repos/ — repositórios open source de referência

Cada diretório é um clone `--depth 1` de um repositório de referência:

| Diretório | Repositório | Padrões |
|---|---|---|
| `debezium` | `debezium/debezium` | CDC / Outbox CDC |
| `temporal` | `temporalio/temporal` | Saga orquestrada, durable execution |
| `eventuate-tram-sagas` | `eventuate-tram/eventuate-tram-sagas` | Saga |
| `watermill` | `ThreeDotsLabs/watermill` | Event-Driven Architecture |
| `modular-monolith-with-ddd` | `kgrzybek/modular-monolith-with-ddd` | Modular Monolith, DDD |
| `wild-workouts-go-ddd-example` | `ThreeDotsLabs/wild-workouts-go-ddd-example` | Hexagonal, DDD, CQRS |
| `EventSourcing.NetCore` | `oskardudycz/EventSourcing.NetCore` | Event Sourcing, CQRS, Outbox/Inbox, Saga |
| `marten` | `JasperFx/marten` | Event store, projections (PostgreSQL) |
| `wolverine` | `JasperFx/wolverine` | Mensageria, command handling |
| `resilience4j` | `resilience4j/resilience4j` | Circuit Breaker, Retry, Bulkhead, RateLimiter |
| `awesome-software-architecture` | `mehdihadeli/awesome-software-architecture` | Curadoria de arquitetura |

## Sobre o versionamento (blobs pesados)

Os clones foram **vendorizados** (`.git` internos removidos) para virar conteúdo deste repositório.

Arquivos **> 1 MB** (dados de bootcamp, imagens/PDFs de documentação, fixtures de teste) foram
**excluídos do versionamento** via `.gitignore`, mas **permanecem no disco local** — o corpus local
fica completo. Motivo: manter o repositório remoto leve e pushável sem LFS.

Para restaurar os blobs excluídos, basta reclonar a fonte correspondente (ver tabela acima) ou
remover a linha do arquivo em `.gitignore` se quiser versioná-lo (requer LFS para arquivos grandes).

## Outros repositórios recomendados (não clonados)

`AxonFramework`, `EventStore`, `dapr`, `redpanda`, `nats-server`, `envoy`, `apisix`, `traefik`,
`argo-rollouts`, `argo-cd`, `unleash`, `etcd`, `hazelcast`, `vitess`, `cockroach`, `tikv`, `loki`,
`istio`, `linkerd2`, `xstate`, `celery`, `superset`, `kubernetes`, `eShop`.

Lista completa e curadoria em [`../docs/referencias/repositorios.md`](../docs/referencias/repositorios.md).
