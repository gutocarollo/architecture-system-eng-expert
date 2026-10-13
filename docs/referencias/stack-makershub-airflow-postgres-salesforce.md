# Referências da stack: MakersHub · Airflow · PostgreSQL · Salesforce

Este documento reúne as principais referências para trabalhar com as quatro peças centrais do
sistema distribuído, conectando-as aos padrões deste repositório.

---

## MakersHub

Aplicação composta por: **Next.js/React** (frontend) + **FastAPI** (backend) + **PostgreSQL**
(dados) + **Redis** (cache) + **Airflow** (pipelines) + integrações (Bitbucket/Jira/Salesforce).

### Padrões centrais

| Área | Padrões |
|---|---|
| Fronteiras de código | Modular Monolith, Hexagonal, Vertical Slice, DDD/Bounded Context |
| Consistência | Transactional Outbox, Idempotency, Optimistic Concurrency |
| Leitura/KPIs | CQRS, Materialized Views, Cache Aside, Refresh Ahead |
| Integrações | Anti-Corruption Layer, Circuit Breaker, Retry+Backoff+Jitter, DLQ |
| Capacidade | Bulkhead, Backpressure, Rate Limiting, Competing Consumers |
| Fluxos | State Machine, Saga |

### Referências internas do ambiente

Skills e docs do próprio ecossistema MakersHub já existentes (usar como autoridade de convenção):

- **Arquitetura:** `makershub-architecture-router`, `backend-layered-architecture`.
- **Frontend:** `makershub-frontend`, `design-system`, `ui-component-standards`.
- **Backend:** `fastapi-backend-pattern`, `fastapi`.
- **Dados/DW:** `faz-dw-standards`, `faz-data-analyst`, `cube-router`, `cube-curator`.
- **Observabilidade:** `makershub-log-contract`.
- **Impersonation:** `makershub-impersonation`.
- **PR:** `makershub-pr-review-standard`, `bitbucket-pr-api`, `bitbucket-pr-text`.
- **Airflow:** `airflow-integration`, `airflow-live-source`, `airflow-exploration-protocol-autoagents`,
  `airflow-pr-review-standards`, `dag-performance-auditor`.

> **Regra:** as convenções reais do MakersHub vivem nessas skills/docs. Este repositório é corpus
> de **arquitetura distribuída**; não substitui as convenções do projeto.

---

## Apache Airflow

Orquestrador de DAGs e pipelines. No MakersHub, faz o batch D+1 e pipelines de dados.

### Padrões aplicáveis

- **Competing Consumers** — `CeleryExecutor` distribui tasks entre workers prontos; filas
  específicas para tarefas curtas vs. tarefas com Chrome/dependências pesadas.
- **Bulkhead** — **pools** limitam concorrência contra recursos compartilhados (mas **não**
  substituem isolamento de memória entre processos/containers).
- **Sidecar** — Helm Chart com `git-sync` para disponibilizar DAGs.
- **Leader Election** — múltiplos schedulers coordenados por locks no banco de metadados (não
  adicionar etcd).
- **Replication** — proteger o banco de metadados do Airflow (workers redundantes não bastam).
- **Retry + Backoff** — evitar multiplicar retries entre proxy, cliente HTTP e Airflow.
- **WAL/Backup** — recuperação do metadata DB.
- **Dead Letter Queue** — uma task `failed` **não** é uma DLQ; modele recuperação explícita.
- **State Machine** — transições de estado de task/DAG.

### Referências

- Código-fonte do Airflow (Apache Software Foundation).
- Skills locais: `airflow-integration`, `airflow-live-source`, `dag-performance-auditor`.
- `k8s-observability-api`, `minio-s3-api` para logs/metadata.

---

## PostgreSQL

Banco relacional central: dados de negócio + metadata do Airflow + base dos KPIs.

### Padrões aplicáveis

- **WAL** — registro antes das páginas; sustenta recuperação e replicação. PITR exige cadeia válida
  de backup-base + arquivamento de WAL.
- **Replication** — Primary/Replica, streaming, síncrona/assíncrona. Replicação **não é backup**.
- **Transactional Outbox** — tabela outbox + índice parcial + `FOR UPDATE SKIP LOCKED`.
- **Optimistic Concurrency** — coluna de versão + checagem no `UPDATE`.
- **Materialized Views** — `REFRESH ... CONCURRENTLY` (exige índice `UNIQUE`).
- **Partitioning** — evitar bloat na outbox e em tabelas de alta volumetria.
- **Isolation Levels / Locking** — pessimistic (`FOR UPDATE`) vs. optimistic.
- **Constraints** — exclusividade de horário/recursos compartilhados (evita double-booking).

### Ferramentas e referências

- **pg_cron / pg_partman** — pruning e particionamento.
- **Debezium** (PostgreSQL logical decoding) — CDC.
- **Vitess/TiKV/CockroachDB** — para estudar sharding/consenso (não necessários agora).
- Skill local: `postgresql-table-design`, `faz-dw-standards`, `supabase-postgres-best-practices`.

---

## Salesforce

CRM externo integrado ao MakersHub.

### Padrões aplicáveis

- **Anti-Corruption Layer** — traduzir campos/estados do Salesforce para conceitos canônicos; um
  `OwnerId` externo **não** é automaticamente a identidade interna de um assessor.
- **Circuit Breaker** — Salesforce indisponível: interromper a integração temporariamente em vez de
  cada requisição esperar timeout longo.
- **Retry + Backoff + Jitter** — falhas transitórias e rate limits da API.
- **Transactional Outbox** — não perder a sincronização quando a app cai após o commit local.
- **Idempotency** — webhooks e reprocessamentos.
- **Dead Letter Queue** — payloads inválidos preservados para análise.
- **Rate Limiting** — respeitar limites de API por credencial/integração.

### Referências

- Salesforce **REST/Bulk API**, **Change Data Capture** (CDC nativo), **Platform Events**.
- Skill local: `faz-opportunity-enrichment` (cruzamento Salesforce + DW).

---

## Como as quatro peças se conectam

```
Next.js/React ──> FastAPI ──> PostgreSQL ──> (Outbox) ──> Debezium/worker ──> broker
                    │             ▲
                    │             └── Airflow (batch D+1) escreve/atualiza dados
                    │
                    └──> Salesforce (ACL + Circuit Breaker + Retry/Backoff + Idempotency)
                              ▲
                              └── webhooks (idempotentes, DLQ)
```

**Pontos de atenção transversais:**

1. **Dual Write** sempre que FastAPI grava em PostgreSQL e chama Salesforce/broker → use **Outbox**.
2. **Idempotência** em todo webhook e em todo consumidor (At-Least-Once).
3. **CDC + invalidação de cache** quando Airflow altera dados fora da aplicação.
4. **Isolamento de carga** (Bulkhead/pools) separando batch pesado do fluxo interativo.
5. **Observabilidade** (correlation id atravessando FastAPI → Airflow → Salesforce).

Ver aplicação detalhada em [`docs/aplicado/aplicacao-makershub-40-patterns.md`](../aplicado/aplicacao-makershub-40-patterns.md).
