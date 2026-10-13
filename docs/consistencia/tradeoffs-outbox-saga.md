# Trade-offs: Transactional Outbox vs Saga

> A adoção de Outbox e Saga substitui a simplicidade transacional de um banco relacional por
> **garantias distribuídas de consistência eventual**. Isso resolve falhas de rede e
> escalabilidade, mas impõe custos operacionais, computacionais e cognitivos severos.

---

## Trade-offs do Transactional Outbox

O Outbox elimina a inconsistência do Dual Write confinando o evento ao banco relacional. Em troca,
transfere a complexidade para o **pipeline de leitura** e para o **consumidor**.

### Vantagens e ganhos reais

- **Consistência garantida na escrita:** estado da aplicação e evento de domínio comitam sob a
  mesma transação ACID local. Se a gravação da regra de negócio abortar, o evento nunca existirá.
- **Sobrevivência à indisponibilidade do broker:** se Kafka/RabbitMQ/Redis caírem, a API continua
  processando e persistindo no PostgreSQL; a fila de saída se acumula no banco.
- **Eliminação de transações distribuídas (2PC/XA):** dispensa locks pessimistas globais.

### Desvantagens e custos operacionais

- **Obrigatoriedade de idempotência no consumidor:** entrega At-Least-Once. Se o publicador envia
  ao broker e cai antes de marcar `processed_at`, reprocessa ao reiniciar. Todo consumidor a
  jusante precisa de chave de idempotência e tabela de deduplicação (**Inbox Pattern**).
- **Sobrecarga de armazenamento e table bloat:** a tabela cresce na proporção de todas as mutações.
  No PostgreSQL, `INSERT`+`SELECT`+`UPDATE` em alta volumetria gera *dead tuples* → exige `VACUUM`
  agressivo, particionamento ou pruning.
- **Latência de publicação não-zero:** dezenas de ms a segundos (polling/decodificação).
- **Desacoplamento de schema (Contract Drift):** payload em JSONB/TEXT não tem validação estrita
  no momento da gravação → exige Schema Registry externo (Avro/Protobuf).

### Polling Publisher vs CDC

| Critério | Polling (SKIP LOCKED) | CDC (Debezium + WAL) |
|---|---|---|
| Custo de infraestrutura | Mínimo | Alto (Kafka Connect, Debezium, KRaft) |
| Impacto no PostgreSQL | Alto I/O | Mínimo I/O |
| Latência fim-a-fim | 100ms–2.000ms | 10ms–50ms |
| Ponto único de falha / risco | Baixo; tabela acumula linhas | **Crítico:** retenção de WAL enche o disco e derruba o primário |
| Complexidade de schema | Trivial (ALTER TABLE) | Sensível a DDL; pode exigir reiniciar snapshots |
| Recomendação | **Comece aqui** (até ~1.000 msg/s) | Migre quando o polling saturar I/O |

---

## Trade-offs do Saga Pattern

A Saga substitui transações ACID distribuídas por uma sequência de transações locais com
compensações semânticas. Prioriza **AP** (Disponibilidade/Partição) sobre **C** imediato.

### Vantagens e ganhos reais

- **Alta escalabilidade e disponibilidade:** etapas independentes, sem prender conexões nem travar
  tabelas remotas esperando terceiros.
- **Suporte a processos de longa duração:** minutos, dias ou semanas.
- **Resiliência a falhas parciais:** falhas transitórias recuperam-se via retries.

### Desvantagens e custos operacionais

- **Perda total de isolamento (O "I" do ACID)** — a mais perigosa. Dados intermediários expostos
  antes do término:
  - **Dirty Reads**, **Non-repeatable Reads**, **Lost Updates**.
- **Complexidade na escrita de compensações:** desfazer ≠ ROLLBACK; é programar a operação inversa
  de negócio. Nem tudo é reversível (e-mails, push, webhooks; PIX exige estorno via adquirente).
- **Possibilidade de falha na própria compensação:** se a compensação quebra, o sistema entra em
  estado inconsistente permanente → alertas críticos e intervenção humana.
- **Explosão no custo de testes:** matriz combinatória de falhas e compensações.

### Coreografia vs Orquestração

| Critério | Coreografia | Orquestração |
|---|---|---|
| Modelo mental | Reativo (eventos no broker) | Imperativo (coordenador comanda) |
| Acoplamento | Baixo entre nós | Serviços acoplados aos contratos do orquestrador |
| Visibilidade | Cega (precisa tracing distribuído) | Cristalina (um lugar) |
| Complexidade operacional | Baixa no início | Alta (cluster de Temporal/Camunda/Step Functions) |
| Risco arquitetural | Event spaghetti / dependências circulares | Monólito distribuído (Smart Coordinator, Dumb Services) |
| Ideal para | 2–3 etapas | 4+ etapas, bifurcações, auditoria |

---

## Matriz comparativa consolidada

| Arquitetura | Latência | Complexidade de código | Sobrecarga operacional | Consistência | Garantia contra falhas |
|---|---|---|---|---|---|
| Monólito com transação ACID única | Mínima (µs) | Mínima | Baixa (só o RDBMS) | Forte (ACID) | Alta, mas não escala além de uma máquina/banco |
| Dual Write ingênuo | Mínima | Baixa (aparente) | Mínima | Nula (inconsistente) | Péssima: perda de sincronia silenciosa |
| Two-Phase Commit (2PC/XA) | Altíssima (s) | Média | Altíssima (locks globais) | Forte (ACID distribuído) | Baixíssima: trava sob partição/timeout |
| Outbox (Polling) | Baixa a Média | Baixa/Média | Baixa | Eventual (At-least-once) | Alta; sobrecarrega I/O do banco em alta escala |
| Outbox (CDC/Debezium) | Sub-segundo | Média | Alta (Kafka Connect/WAL) | Eventual (At-least-once) | Alta; risco de esgotamento de disco |
| Saga Coreografada | Baixa | Média (por nó) | Média (broker) | Eventual (sem isolamento) | Média; rastreabilidade opaca |
| Saga Orquestrada (Temporal) | Média | Média/Alta | Alta (engine de workflow) | Eventual (sem isolamento) | Máxima; controle total de estado/retries |

---

## Síntese comparativa direta

| Dimensão | Transactional Outbox | Saga Pattern |
|---|---|---|
| Objetivo primário | Integração confiável (Banco ↔ Broker) | Transação de negócio distribuída entre serviços |
| Escopo arquitetural | Local (uma app + seu banco) | Global (vários serviços/bancos) |
| Problema que elimina | Dual Write / perda de mensagens em crash | Necessidade de 2PC e locks globais |
| Mecanismo de recuperação | Retentativas automáticas (at-least-once) | Compensações semânticas em ordem inversa |
| Garantia de consistência | Eventual na propagação da mensagem | Eventual no estado global do negócio |
| Requisito obrigatório | Consumidores idempotentes | Compensações idempotentes e reversíveis |

---

Ver também:
- [Dual Write e alternativas](dual-write-e-alternativas.md)
- [Outbox](../outbox/README.md) · [Saga](../saga/README.md)
