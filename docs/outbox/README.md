# Transactional Outbox — documento completo

> Padrão de integração onde a emissão de um evento para o mundo externo não é feita
> chamando rede/broker diretamente, mas salvando o evento como uma **linha no próprio banco
> relacional, dentro da mesma transação local da regra de negócio**. Um processo em segundo
> plano lê essa tabela e publica no broker real (Kafka, RabbitMQ, Redis Streams, SQS).

## Índice

1. [O que é](#1-o-que-é)
2. [Por que existe: a armadilha do Dual Write](#2-por-que-existe-a-armadilha-do-dual-write)
3. [Anatomia da tabela Outbox](#3-anatomia-da-tabela-outbox)
4. [Como a mensagem sai do banco: os dois motores](#4-como-a-mensagem-sai-do-banco-os-dois-motores)
5. [A regra de ouro: entrega At-Least-Once](#5-a-regra-de-ouro-entrega-at-least-once)
6. [Implementação de referência](#6-implementação-de-referência)
7. [How-to: escala, performance e limpeza](#7-how-to-escala-performance-e-limpeza)
8. [Trade-offs](#8-trade-offs)
9. [Alternativas ao Outbox](#9-alternativas-ao-outbox)
10. [Referências](#10-referências)

---

## 1. O que é

O Transactional Outbox resolve um dos problemas mais clássicos da computação distribuída: **como
publicar um evento para o resto do sistema sem risco de perder a mensagem ou de divergir do
estado persistido**.

A ideia central é **confinar a atomicidade ao nó local**. Em vez de tentar uma transação ACID que
abranja banco + broker (o que exige 2PC/XA, caro e frágil), você transforma a *intenção de
integração* numa gravação local, dentro da mesma transação do agregado de negócio:

```
┌──────────────── PostgreSQL (Transação Única) ────────────────┐
│                                                              │
│  UPDATE orders SET status = 'CONFIRMED' WHERE id = 123;      │
│  INSERT INTO outbox_events (id, topic, payload, created_at)  │
│  VALUES ('evt-1', 'order.confirmed', '{"id":123}', NOW());   │
│                                                              │
└─────────────────────────── COMMIT ───────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                │ Mecanismo Assíncrono de Saída │
                ▼                               ▼
        Polling Publisher                 CDC (Debezium)
   (SELECT ... FOR UPDATE SKIP LOCKED)   (Lendo o PostgreSQL WAL)
                │                               │
                └───────────────┬───────────────┘
                                ▼
                     Message Broker / Kafka
```

Ambos salvam ou ambos falham. Zero chance de divergência entre o estado de negócio e a intenção
de publicar o evento.

---

## 2. Por que existe: a armadilha do Dual Write

Muitos sistemas tentam fazer o seguinte no código:

```python
# Anti-pattern: Dual Write
db.commit()        # Passo 1: grava no banco
kafka.send(event)  # Passo 2: avisa o broker
```

Se o servidor for reiniciado, a rede oscilar ou a conexão com o Kafka expirar **exatamente entre
o Passo 1 e o Passo 2**, seu banco foi atualizado, mas o resto do ecossistema jamais receberá o
evento.

Se você inverte a ordem:

```python
kafka.send(event)  # Passo 1: avisa o broker
db.commit()        # Passo 2: grava no banco
```

Se o banco falhar numa constraint (chave duplicada, violação) ou cair antes do commit, o evento
**já foi disparado**. Consumidores processarão uma ordem que nunca existiu no banco.

```
SEM OUTBOX (O Dual Write problem):
Aplicação ──┬──> [1] INSERT/UPDATE no PostgreSQL   (Sucesso)
            └──> [2] Envia mensagem para o Kafka    (💥 Falha de rede / Crash)
Resultado: O banco salvou, o broker nunca soube. Estado inconsistente.

COM OUTBOX:
Aplicação ─────> [ Transação Única no PostgreSQL ]
                 ├── [1] INSERT/UPDATE na tabela de negócio (ex: orders)
                 └── [2] INSERT na tabela outbox_events
                 [ COMMIT ATÔMICO ]

                 Ambos salvam ou ambos falham. Zero chance de divergência.
```

Não existe transação ACID nativa que abranja simultaneamente um banco SQL e um broker
HTTP/TCP sem coordenadores distribuídos pesados (XA/2PC), que bloqueiam recursos (locks
pessimistas) e colapsam sob partições de rede.

> **Detalhe importante para o MakersHub:** o Outbox **não exige Kafka nem CDC**. Um worker pode
> simplesmente consultar a outbox periodicamente. Ainda assim é necessário tratar duplicação e
> definir ordenação quando ela importa.

---

## 3. Anatomia da tabela Outbox

A tabela Outbox atua como uma **fila persistente dentro do banco relacional**:

| Campo | Tipo | Função |
|---|---|---|
| `id` | UUID / BIGINT | Identificador único do evento |
| `aggregate_type` | VARCHAR | Entidade de origem (ex: `Order`, `Lead`, `Invoice`) |
| `aggregate_id` | VARCHAR | Chave da entidade (ex: `ord-1234`) |
| `event_type` | VARCHAR | Nome do evento de domínio (ex: `OrderCreated`, `LeadDistributed`) |
| `topic` | VARCHAR | Destino no broker |
| `payload` | JSONB / TEXT | Dados completos do evento |
| `headers` | JSONB | Metadados (correlation id, tracing) |
| `created_at` | TIMESTAMP | Data/hora do commit original |
| `processed_at` | TIMESTAMP (NULL) | Preenchido quando o publicador confirma envio ao broker |

### DDL de produção (referência)

```sql
CREATE TABLE outbox_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_type VARCHAR(100) NOT NULL,
    aggregate_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    headers JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT clock_timestamp() NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE NULL
);

-- Índice parcial indispensável para polling de alto throughput
CREATE INDEX idx_outbox_unprocessed
ON outbox_messages (created_at ASC)
WHERE processed_at IS NULL;

-- Índice para deduplicação e rastreabilidade por agregado
CREATE INDEX idx_outbox_aggregate
ON outbox_messages (aggregate_type, aggregate_id);
```

---

## 4. Como a mensagem sai do banco: os dois motores

```
Abordagem A: Polling Publisher
[outbox_events] <── SELECT ... FOR UPDATE SKIP LOCKED ── [Worker App] ──> [Broker]

Abordagem B: Change Data Capture (CDC)
[Postgres WAL (Log)] ──> [Debezium / Logical Replication] ───────────────> [Broker]
```

### 4.1 Polling Publisher (Worker com SKIP LOCKED)

**Mecanismo:** uma thread/processo executa, em loop, consultas na tabela:

```sql
SELECT id, payload FROM outbox_events
WHERE processed_at IS NULL
ORDER BY created_at ASC
LIMIT 100
FOR UPDATE SKIP LOCKED;
```

- **Vantagens:** não exige infraestrutura adicional; funciona em qualquer PostgreSQL/MySQL;
  implementação simples em poucas linhas de código.
- **Trade-offs:** gera I/O constante de leitura e escrita no banco; latência atrelada ao
  intervalo de sleep (geralmente 100ms–2s); exige rotina de limpeza (pruning) para evitar bloat.

### 4.2 Change Data Capture (CDC / Transaction Log Miner)

**Mecanismo:** ferramentas como o **Debezium** leem diretamente o log binário de transações
(o **Write-Ahead Log / WAL** no PostgreSQL). O Debezium detecta que uma linha foi inserida em
`outbox_events` e publica imediatamente no Kafka, **sem executar queries SQL**.

- **Vantagens:** latência sub-segundo (ms); zero impacto de queries na CPU/disco do banco;
  nunca bloqueia tabelas.
- **Trade-offs:** alta complexidade operacional (Kafka Connect + Debezium + monitoramento
  rigoroso de replication slots, sob risco de encher o disco com WALs acumulados).

> **Limite conceitual do CDC:** detectar que uma linha mudou **não** revela automaticamente
> quais resultados de JOIN ou chaves Redis ficaram inválidos. Essa relação precisa ser modelada.

---

## 5. A regra de ouro: entrega At-Least-Once

O Outbox garante que **nenhum evento será perdido**, mas **não** garante entrega exatamente uma
vez (*Exactly-Once*).

Se o publicador lê o banco, envia ao Kafka com sucesso, mas cai milissegundos antes de atualizar
o `processed_at`, ao reiniciar ele relerá o mesmo evento e enviará uma **duplicata** ao broker.

> **Regra arquitetural:** toda arquitetura baseada em Outbox exige que os consumidores sejam
> **idempotentes** (receber a mesma mensagem repetida sem duplicar efeitos colaterais) — via
> **Idempotency Key** e/ou **Transactional Inbox** (tabela de deduplicação).

---

## 6. Implementação de referência

### Pré-requisitos

```bash
pip install psycopg[binary]
```

### Passo 1 — Tabelas de negócio + Outbox

```sql
CREATE TABLE IF NOT EXISTS accounts (
    id VARCHAR(50) PRIMARY KEY,
    balance NUMERIC(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(50) PRIMARY KEY,
    amount NUMERIC(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS outbox_events (
    id VARCHAR(50) PRIMARY KEY,
    aggregate_type VARCHAR(50) NOT NULL,
    aggregate_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE NULL
);

INSERT INTO accounts (id, balance) VALUES ('acc-1', 100.00)
ON CONFLICT (id) DO UPDATE SET balance = 100.00;
```

### Passo 2 — Operação com Transactional Outbox

```python
import json
import uuid
import psycopg

DB_URI = "postgresql://postgres:postgres@localhost:5432/postgres"

def criar_pedido_com_outbox(order_id: str, amount: float):
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            # 1. Escrita de negócio
            cur.execute(
                "INSERT INTO orders (id, amount, status) VALUES (%s, %s, %s);",
                (order_id, amount, "PENDING")
            )

            # 2. Escrita no Outbox dentro da MESMA transação
            event_id = str(uuid.uuid4())
            event_payload = json.dumps({"order_id": order_id, "amount": amount})
            cur.execute(
                """
                INSERT INTO outbox_events (id, aggregate_type, aggregate_id, event_type, payload)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (event_id, "Order", order_id, "OrderCreated", event_payload)
            )

        # O commit confirma AMBOS atomicamente
        conn.commit()
    print(f"[OK] Pedido {order_id} e evento Outbox gravados atomicamente.")

criar_pedido_com_outbox("ord-999", 50.00)
```

### Passo 3 — Polling Publisher

```python
def processar_outbox_publisher():
    with psycopg.connect(DB_URI) as conn:
        with conn.cursor() as cur:
            # Trava a linha sem bloquear workers concorrentes
            cur.execute(
                """
                SELECT id, event_type, payload
                FROM outbox_events
                WHERE processed_at IS NULL
                ORDER BY created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED;
                """
            )
            row = cur.fetchone()
            if not row:
                print("Nenhum evento pendente.")
                return None

            event_id, event_type, payload = row

            # Simulação de envio para broker (Kafka/RabbitMQ)
            print(f"[DISPATCH BROKER] Enviando {event_type}: {payload}")

            # Marca como processado
            cur.execute(
                "UPDATE outbox_events SET processed_at = NOW() WHERE id = %s;",
                (event_id,)
            )
        conn.commit()

processar_outbox_publisher()
```

### Passo 4 — Integração com Saga (o Outbox como transporte da Saga)

Uma Saga **usa o Outbox como canal de transporte**. Quando um participante conclui sua transação
local, ele não faz chamada de rede direta para o próximo serviço: grava o próximo passo na sua
tabela Outbox. Assim, a própria execução da Saga torna-se à prova de falhas de infraestrutura.

```python
class OrderSagaOrchestrator:
    def __init__(self, db_uri: str):
        self.db_uri = db_uri

    def debitar_saldo(self, account_id: str, amount: float) -> bool:
        with psycopg.connect(self.db_uri) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT balance FROM accounts WHERE id = %s FOR UPDATE;", (account_id,))
                res = cur.fetchone()
                if not res or res[0] < amount:
                    return False
                cur.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s;", (amount, account_id))
            conn.commit()
        return True

    def compensar_saldo(self, account_id: str, amount: float):
        """Ação semântica inversa: devolve o saldo caso a etapa posterior falhe."""
        with psycopg.connect(self.db_uri) as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s;", (amount, account_id))
            conn.commit()
        print(f"[COMPENSAÇÃO] Saldo de R$ {amount} devolvido para a conta {account_id}.")

    def executar_saga(self, order_id: str, account_id: str, amount: float, simular_falha_etapa2: bool = False):
        print(f"\n--- Iniciando Saga para Pedido {order_id} ---")

        # Etapa 1: Transação Compensável (Debitar Saldo)
        if not self.debitar_saldo(account_id, amount):
            print("[SAGA ABORTADA] Saldo insuficiente. Nenhuma compensação necessária.")
            return

        print(f"[ETAPA 1 SUCESSO] Débito de R$ {amount} realizado.")

        # Etapa 2: Confirmação do Pedido (Transação Pivô)
        try:
            if simular_falha_etapa2:
                raise RuntimeError("Falha de infraestrutura ao confirmar reserva.")

            with psycopg.connect(self.db_uri) as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE orders SET status = 'CONFIRMED' WHERE id = %s;", (order_id,))
                conn.commit()
            print("[ETAPA 2 SUCESSO] Pedido CONFIRMED. Saga concluída com êxito.")

        except Exception as e:
            print(f"[ERRO NA ETAPA 2] {e}")
            # Disparo da Ação de Compensação
            self.compensar_saldo(account_id, amount)
            with psycopg.connect(self.db_uri) as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE orders SET status = 'FAILED' WHERE id = %s;", (order_id,))
                conn.commit()
            print("[SAGA COMPENSADA] Estado global converge para cancelado.")

orchestrator = OrderSagaOrchestrator(DB_URI)
orchestrator.executar_saga(order_id="ord-999", account_id="acc-1", amount=50.00, simular_falha_etapa2=True)
```

---

## 7. How-to: escala, performance e limpeza

### 7.1 Índice parcial (não indexe o histórico de processados)

```sql
CREATE INDEX CONCURRENTLY idx_outbox_unprocessed
ON outbox_events (created_at ASC)
WHERE processed_at IS NULL;
```

### 7.2 Polling com batching e lock skip

```python
def fetch_and_publish_batch(conn, batch_size=100):
    with conn.cursor() as cur:
        # 1. Seleciona e trava lote sem enfileirar outros workers
        cur.execute(
            """
            SELECT id, topic, payload
            FROM outbox_events
            WHERE processed_at IS NULL
            ORDER BY created_at ASC
            LIMIT %s
            FOR UPDATE SKIP LOCKED;
            """,
            (batch_size,)
        )
        events = cur.fetchall()
        if not events:
            return 0

        event_ids = [e[0] for e in events]

        # 2. Publica no Message Broker (fora da transação SQL se o broker for remoto)
        for evt_id, topic, payload in events:
            broker_client.publish(topic, payload)

        # 3. Marca como processado
        cur.execute(
            "UPDATE outbox_events SET processed_at = NOW() WHERE id = ANY(%s);",
            (event_ids,)
        )
    conn.commit()
    return len(events)
```

### 7.3 Pruning periódico (evitar bloat)

Tabelas Outbox acumulam bloat rapidamente. Use particionamento por data ou rotina de deleção:

```sql
-- Executar via cron/pg_cron diariamente:
DELETE FROM outbox_events
WHERE processed_at < NOW() - INTERVAL '3 days';
```

> No PostgreSQL, a combinação frequente de `INSERT`, `SELECT` e `UPDATE` em alta volumetria gera
> *dead tuples*, exigindo `VACUUM` agressivo, particionamento ou pruning.

### 7.4 Schema drift (Contract Drift)

Como o payload costuma ser JSONB/TEXT, **não há validação estrita de schema** no momento da
gravação. Use um **Schema Registry** externo (Avro/Protobuf) para evitar que eventos malformados
cheguem aos consumidores.

---

## 8. Trade-offs

### Vantagens e ganhos reais

- **Consistência garantida na escrita:** estado da aplicação e evento comitam sob a mesma
  transação ACID local. Se o negócio abortar, o evento nunca existirá.
- **Sobrevivência à indisponibilidade do broker:** se Kafka/RabbitMQ/Redis caírem, a API continua
  processando e persistindo no PostgreSQL; a fila de saída se acumula no banco.
- **Eliminação de transações distribuídas (2PC/XA):** dispensa locks pessimistas globais.

### Desvantagens e custos operacionais

- **Idempotência obrigatória no consumidor:** semântica At-Least-Once exige Idempotency Key e/ou
  Inbox (tabela de deduplicação).
- **Bloat e armazenamento:** a tabela cresce na proporção de todas as mutações.
- **Latência não-zero:** de dezenas de ms a segundos (polling/decodificação).
- **Contract drift:** payload JSONB sem schema estrito.

### Polling Publisher vs CDC

| Critério | Polling Publisher (SKIP LOCKED) | CDC via Log Mining (Debezium + WAL) |
|---|---|---|
| Custo de infraestrutura | Mínimo (roda no processo/worker) | Alto (Kafka Connect, Debezium, KRaft) |
| Impacto no PostgreSQL | Alto I/O (SELECT/UPDATE disputam conexões) | Mínimo I/O (lê o WAL assíncrono) |
| Latência fim-a-fim | 100ms–2.000ms | 10ms–50ms |
| Ponto único de falha | Baixo (pior caso: tabela acumula) | Risco crítico de disco (retenção de WAL) |
| Complexidade de schema | Trivial (ALTER TABLE) | Sensível a DDL; pode exigir reinício |
| Recomendação | **Comece aqui** (MVP, até ~1.000 msg/s) | Migre quando o polling saturar I/O |

---

## 9. Alternativas ao Outbox

Além do Outbox (polling ou CDC em tabela dedicada), há outras formas de resolver o Dual Write:

1. **Event Sourcing puro** — grava apenas o evento num *append-only event store* (EventStoreDB,
   Marten, Kafka transacional). Elimina o dual write na raiz; impõe alta complexidade cognitiva,
   versionamento de schemas e migrações não triviais.
2. **Two-Phase Commit (2PC/XA)** — commit distribuído coordenado. Garante ACID distribuído, mas
   bloqueia linhas (locks pessimistas); se o coordenador cai no *Prepare*, os recursos ficam
   travados → disponibilidade e latência inaceitáveis em alta escala.
3. **CDC direto na tabela de domínio** — Debezium lê o WAL da própria tabela de negócio.
   Zero código adicional e sem tabela extra; contudo **acopla o schema interno ao contrato
   público de eventos** e **não captura a intenção de negócio** (o *porquê* da mudança).
4. **Listen-to-Yourself / Event-First (inversão do fluxo)** — a API grava direto no broker/log
   (que age como WAL distribuído) e um consumidor da própria aplicação atualiza o PostgreSQL.
   Garante a escrita via retries, mas quebra o **Read-Your-Writes** imediato na API (exige
   WebSocket/SSE/polling no frontend).
5. **Eliminação da fronteira distribuída (reconvergência)** — se os módulos compartilham ciclo de
   vida transacional, volte-os para o mesmo processo/banco (**Modular Monolith**) e use uma única
   transação ACID local. Resolve sem infraestrutura distribuída, ao custo de deploys/bancos
   desacoplados.

---

## 10. Referências

### Frameworks e bibliotecas

- **Debezium** — CDC / log mining (platform de referência).
- **Eventuate Tram** — Outbox + Saga + CQRS em Java.
- **Marten** + **Wolverine** — event store + messaging sobre PostgreSQL (.NET).
- **Watermill** — event-driven em Go.

### Aplicações de referência

- **Eventuate Customers and Orders** — demonstra Outbox + Saga + CQRS juntos.
- **kgrzybek/modular-monolith-with-ddd** — Outbox + Domain Events em monólito modular.
- **oskardudycz/EventSourcing.NetCore** — Outbox/Inbox, projeções, Sagas, optimistic concurrency.

Ver [`docs/referencias/repositorios.md`](../referencias/repositorios.md).
