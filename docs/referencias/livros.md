# Livros canônicos — arquitetura e sistemas distribuídos

## O cânone central (fundamentos e teoria dos dados)

- **Designing Data-Intensive Applications (DDIA)** — Martin Kleppmann.
  O livro mais importante da área. Modelos de dados, índices, replicação, particionamento,
  consenso, transações e por que sistemas distribuídos quebram.
- **Database Internals: A Deep Dive into How Distributed Data Systems Work** — Alex Petrov.
  Implementação concreta: B-Trees vs LSM-Trees, replicação, consenso (Paxos/Raft), coordenação.
- **Distributed Systems** — Maarten van Steen & Andrew S. Tanenbaum.
  A bíblia acadêmica: arquiteturas, RPC, processos, sincronização (relógios lógicos),
  consistência e tolerância a falhas.
- **Patterns of Distributed Systems** — Unmesh Joshi.
  Conhecimento de bancos distribuídos (Kafka, etcd, Cassandra) em padrões reutilizáveis: WAL,
  High-Water Mark, Leader & Followers, Heartbeat, Split-Brain Protections.

## Arquitetura, microsserviços e integração

- **Software Architecture: The Hard Parts** — Neal Ford, Mark Richards, Pramod Sadalage &
  Zhamak Dehghani. Decisões difíceis: transações distribuídas, decomposição de dados, contratos,
  trade-offs de Saga vs 2PC, análise de acoplamento.
- **Microservices Patterns: With Examples in Java** — Chris Richardson.
  Formalizou Transactional Outbox, Saga (orquestrada/coreografada), CQRS e Event Sourcing.
- **Enterprise Integration Patterns** — Gregor Hohpe & Bobby Woolf.
  Catálogo fundamental de mensageria assíncrona (Message Router, Content-Based Router,
  Competing Consumers, Idempotent Receiver).
- **Building Microservices: Designing Fine-Grained Systems** — Sam Newman.
  Fronteiras, divisão de bancos compartilhados, governança de APIs e resiliência.
- **Understanding Distributed Systems** — Roberto Vitillo.
  Guia direto e pragmático: comunicação, resiliência, observabilidade, consenso e storage.

## Complementares úteis

- **Fundamentals of Data Engineering** — Joe Reis & Matt Housley.
- **Designing Machine Learning Systems** — Chip Huyen.
- **Release It!** — Michael Nygard. Padrões de estabilidade (Circuit Breaker, Bulkhead).
- **Designing Distributed Systems** — Brendan Burns.
- **Distributed Systems for fun and profit** — Mikito Takada (livre).
- **Making reliable distributed systems in the presence of software errors** — Joe Armstrong (tese).

## Referências de estudo ligadas aos livros (repos)

- `ept/ddia-references` — todas as fontes citadas por Kleppmann em cada capítulo do DDIA.
- `theanalyst/awesome-distributed-systems` — curadoria de livros, papers, cursos (MIT 6.824, ETH).
- `papers-we-love/papers-we-love` — papers clássicos (Raft, Paxos, Dynamo, Spanner, MapReduce).

Ver também [`repositorios.md`](repositorios.md).
