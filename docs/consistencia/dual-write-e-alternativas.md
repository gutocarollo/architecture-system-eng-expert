# Dual Write e as formas de resolvê-lo

> **Dual Write** é o ato de escrever em dois sistemas na mesma operação de negócio (ex.: gravar
> no PostgreSQL **e** publicar num broker/cache/API). É normalmente **um problema a ser
> controlado**, não uma arquitetura final desejável.

## O problema em uma imagem

```
App
 ├─ write PostgreSQL   ✅
 └─ write Kafka/Redis/API  ❌
```

Se a segunda escrita falha (rede, timeout, crash), o estado dos dois sistemas **diverge
silenciosamente**. Não existe transação ACID nativa que abranja um banco SQL e um broker
HTTP/TCP sem coordenadores distribuídos pesados (XA/2PC).

### Por que não usar 2PC sempre?

O Two-Phase Commit garante atomicidade distribuída, mas:
- **bloqueia linhas** com locks pessimistas durante a janela de rede;
- se o coordenador cai no *Prepare*, os recursos **permanecem travados**;
- degrada latência e disponibilidade a níveis inaceitáveis em alta escala.

## As 5 formas de resolver o Dual Write (além de Outbox e Saga)

### 1. Event Sourcing puro

A aplicação grava **apenas o evento** num *append-only event store* (EventStoreDB, Marten, Kafka
transacional). O evento é a fonte da verdade; o estado é uma projeção derivada.

- **Elimina o dual write na raiz.**
- Custo: alta complexidade cognitiva, versionamento de schemas de eventos, migrações não triviais.

### 2. Two-Phase Commit (2PC / XA)

Coordenador transacional pergunta a todos os recursos se podem commitar (*Prepare*) e depois ordena
o commit (*Commit*). Bancos relacionais e brokers legados (IBM MQ, ActiveMQ) suportam XA.

- **Garante consistência imediata (ACID distribuído).**
- Custo: locks globais, travamento sob partição de rede, latência altíssima.

### 3. CDC direto na tabela de domínio (log-based)

Diferente do *Outbox CDC* (com tabela intermediária), aqui o Debezium lê o WAL da **própria
tabela de negócio** (ex.: `orders`). A aplicação só faz `INSERT INTO orders`.

- **Zero código adicional, sem tabela extra.**
- Custo: **acopla o schema interno ao contrato público de eventos**; **não captura a intenção de
  negócio** (o *o quê* mudou, não o *porquê*).

### 4. Listen-to-Yourself / Event-First (inversão do fluxo)

A aplicação grava **direto no broker/log** (que age como WAL distribuído) e **consome a si mesma**;
um consumidor atualiza o PostgreSQL.

- **A escrita no banco é garantida via retries do consumidor.**
- Custo: a requisição síncrona **não pode responder imediatamente** com o estado gravado (quebra
  o *Read-Your-Writes* imediato) → exige interfaces assíncronas (WebSocket, SSE, polling).

### 5. Eliminação da fronteira distribuída (reconvergência)

Muitos dual writes são criados artificialmente pela **separação prematura** de serviços que
compartilham o mesmo ciclo de vida transacional.

- **Retorne os módulos para o mesmo processo/banco (Modular Monolith)** e use uma única transação
  ACID local gerenciada pelo PostgreSQL.
- Custo: abre mão de deploys e bancos desacoplados.

## Resumo — Outbox e Saga em relação ao Dual Write

| Abordagem | Resolve Dual Write? | Nível |
|---|---|---|
| Transactional Outbox | Sim (banco ↔ broker) | Integração local confiável |
| Saga | Sim (entre serviços) | Transação de negócio distribuída |
| TCC (Try-Confirm-Cancel) | Sim (reserva/confirm/cancel) | Transação distribuída com reserva |
| 2PC/XA | Sim (atomicidade global) | Bloqueio global (evitar em escala) |
| CDC direto | Sim (acopla schema) | Integração por log |
| Event Sourcing | Sim (na raiz) | Modelo de dados |
| Listen-to-yourself | Sim (assíncrono) | Inversão de fluxo |
| Reconvergência | Sim (elimina a fronteira) | Arquitetura |

## Árvore de decisão rápida

```
Preciso alterar dois sistemas?
│
├── Todos os recursos estão no MESMO banco relacional?
│   └── SIM: use uma única transação ACID (BEGIN ... COMMIT). Não use Saga.
│
└── Os recursos estão em bancos diferentes ou serviços independentes?
    │
    ├── É apenas propagação de eventos / integração unidirecional?
    │   └── SIM: TRANSACTIONAL OUTBOX + consumidor idempotente.
    │
    └── É uma operação interdependente com chance de reversão?
        │
        ├── Fluxo curto (2 a 3 etapas) e sem visão centralizada necessária?
        │   └── CHOREOGRAPHED SAGA.
        │
        └── Fluxo longo (4+ etapas), lógica crítica e auditoria estrita?
            └── ORCHESTRATED SAGA (ex: Temporal, state machine durável).
```

## A evolução típica na prática

```
Dual Write
   ↓
Outbox Pattern
   ↓
CDC
   ↓
Event Broker
   ↓
Idempotent Consumers
   ↓
Saga / CQRS quando necessário
```

---

Ver também:
- [Outbox — documento completo](../outbox/README.md)
- [Saga — documento completo](../saga/README.md)
- [Trade-offs Outbox vs Saga](tradeoffs-outbox-saga.md)
