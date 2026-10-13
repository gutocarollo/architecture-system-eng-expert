# Saga Pattern — documento completo

> Padrão arquitetural para gerenciar **transações distribuídas de longa duração** (*long-running
> transactions*) que atravessam múltiplos bancos de dados ou microsserviços, **sem** recorrer a
> locks globais ou Two-Phase Commit (2PC).

## Índice

1. [O que é](#1-o-que-é)
2. [Compensação semântica: a essência](#2-compensação-semântica-a-essência)
3. [Os tipos de transação em uma Saga](#3-os-tipos-de-transação-em-uma-saga)
4. [Coreografia vs Orquestração](#4-coreografia-vs-orquestração)
5. [O grande desafio: falta de isolamento](#5-o-grande-desafio-falta-de-isolamento)
6. [Onde aplicar na sua stack](#6-onde-aplicar-na-sua-stack)
7. [Trade-offs](#7-trade-offs)
8. [Como Outbox e Saga trabalham juntos](#8-como-outbox-e-saga-trabalham-juntos)
9. [Referências](#9-referências)

---

## 1. O que é

A Saga foi formulada originalmente em **1987** por Hector Garcia-Molina e Kenneth Salem para
transações longas em bancos relacionais e depois adaptada a sistemas distribuídos por Chris
Richardson e a comunidade de DDD.

Em uma Saga, uma grande transação de negócio é quebrada numa **cadeia ordenada de transações
locais independentes** (T1, T2, T3, …, Tn). Cada transação local commita no seu próprio banco e
avisa o próximo passo.

```
Fluxo Feliz:
[T1: Reserva Estoque] ──> [T2: Debita Pagamento] ──> [T3: Gera Envio] ──> Sucesso Global

Fluxo com Falha no Passo 3:
[T1: Reserva Estoque] ──> [T2: Debita Pagamento] ──> [T3: Falha no Envio!]
         │                        │
         ▼                        ▼
[C1: Estorna Estoque] <── [C2: Reembolsa Cartão] (Compensações em ordem inversa)
```

---

## 2. Compensação semântica: a essência

Em um banco comum, se uma query falha você dispara `ROLLBACK` e o banco descarta as alterações de
memória usando o log de transações. **Nada aconteceu para o mundo exterior.**

Em sistemas distribuídos, o `ROLLBACK` tradicional **não existe**. O Passo 1 já fez commit no
banco do Serviço A; o dinheiro já foi retirado ou o recurso já foi alterado minutos atrás.

A Saga resolve isso executando uma **Transação de Compensação (C)**:

> A compensação **não desfaz o tempo**: ela aplica uma nova transação com o **efeito oposto
> semântico**.

- Se `T1` foi "Cobrar R$ 100", a compensação `C1` não apaga o débito do extrato; ela insere uma
  linha de "Estorno / Crédito de R$ 100".
- Se `T1` foi "Reservar Assento 14B", `C1` é "Liberar Assento 14B".

**Nem toda ação é reversível:**

- Envio de e-mails, notificações push e webhooks **não podem** ser "des-enviados".
- Cobranças via PIX/cartão exigem fluxos separados de estorno, dependentes de adquirentes
  externos (que também podem falhar).

---

## 3. Os tipos de transação em uma Saga

Toda Saga madura classifica suas etapas em três categorias:

| Tipo | Definição | Exemplo |
|---|---|---|
| **Compensáveis** (T1…Tp-1) | Têm ação de compensação (C) que reverte o efeito de negócio | Reservar estoque, debitar crédito |
| **Pivô** (Tp) | O **ponto de não retorno**. Se falhar → compensa tudo antes. Se commitar → vai até o fim | Confirmar pedido |
| **Retentáveis** (Tp+1…Tn) | Ocorrem após o pivô. **Nunca** são compensadas; garantia de sucesso eventual via retries idempotentes | Enviar e-mail, emitir NF |

---

## 4. Coreografia vs Orquestração

### 4.1 Coreografia (Choreography)

Não existe maestro central. Cada serviço executa sua transação local, publica um evento de
domínio e outros serviços reagem.

```
[Serviço de Pedidos] ── evento: PedidoCriado ──> [Serviço de Pagamentos]
                                                        │
                  evento: PagamentoRecusado <───────────┘
                  │
                  ▼
[Serviço de Pedidos reage e cancela pedido]
```

- **Quando usar:** fluxos simples com 2–3 etapas, onde um coordenador seria sobre-engenharia.
- **Problema:** em fluxos com 5+ serviços vira uma "teia de aranha" (*event spaghetti*).
  Ninguém sabe onde o fluxo começa, termina ou por que travou.

### 4.2 Orquestração (Orchestration)

Existe um orquestrador central (máquina de estados durável ou motor de workflow como **Temporal**,
AWS Step Functions ou Camunda). Ele comanda cada serviço e escuta as respostas.

```
                 ┌──> 1. Executa "Reservar" ───> [Serviço Estoque]
                 │<── Resposta: Sucesso ───────────────┘
[ Orquestrador ] ───> 2. Executa "Cobrar" ────> [Serviço Pagamento]
(State Machine)  │<── Resposta: Falhou! ──────────────┘
                 │
                 └──> 3. Executa Compensação ──> [Serviço Estoque]
                      (Estorna a reserva)
```

- **Quando usar:** processos críticos com 3+ etapas, compensações complexas, timeouts longos
  (dias/semanas) ou necessidade de auditoria e visibilidade imediata do estado.

### 4.3 Comparativo

| Dimensão | Coreografia | Orquestração |
|---|---|---|
| Mecanismo | Serviços reagem a eventos via broker | Coordenador central comanda explicitamente |
| Acoplamento | Desacoplamento temporal e de endereçamento | Serviços acoplados aos contratos do orquestrador |
| Visibilidade | Difícil de rastrear (fluxo implícito) | Centralizada (grafo e estado claros) |
| Complexidade | Baixa para 2–3 etapas; ingovernável em fluxos longos | Requer infraestrutura de orquestração durável |
| Risco típico | Dependências cíclicas e tempestades de eventos | Orquestrador virar "monólito de regras de domínio" |
| Ideal para | Fluxos curtos e lineares (2–3 etapas) | Processos críticos com 4+ etapas, bifurcações e auditoria |

---

## 5. O grande desafio: falta de isolamento

Este é o ponto cego mais perigoso: em uma Saga, as transações locais **commitam imediatamente**.
Entre o commit da etapa 1 e a falha da etapa 3, **os dados intermediários estão visíveis**.

### Anomalias decorrentes da falta de isolamento

- **Dirty Reads:** o cliente A compra o último item (T1). O cliente B vê "Esgotado". Minutos
  depois o cartão de A é recusado (T2 falha), a compensação C1 roda e o item volta. B perdeu a
  compra por causa de um dado sujo temporário.
- **Lost Updates:** um serviço altera um registro que participava de uma saga; quando a saga é
  compensada, ela sobrescreve a alteração do terceiro.
- **Non-repeatable Reads:** dois fluxos concorrentes alteram os mesmos registros em ordens
  desencontradas.

### Contramedida canônica: Semantic Lock (bloqueio semântico)

Em vez de mudar o status direto para `RESERVADO`, mude para `RESERVA_PENDENTE`:

```sql
UPDATE seats SET status = 'PENDING_RESERVATION', saga_id = 'saga-xyz'
WHERE id = 42 AND status = 'AVAILABLE';
```

- Qualquer operação concorrente que consulte o registro **enxerga o estado pendente** e decide
  esperar ou recusar.
- **Sucesso:** o status passa para `RESERVED`.
- **Falha (compensação):** volta para `AVAILABLE` e limpa `saga_id`.

Outras contramedidas: **Commutative Updates** (operações comutativas) e **Optimistic Concurrency
Control (OCC)**.

---

## 6. Onde aplicar na sua stack

O exemplo abaixo parte da arquitetura MakersHub (Next.js/React, FastAPI, PostgreSQL, Redis,
Airflow, VMs self-hosted e integrações Bitbucket/Jira/Salesforce). São **aplicações propostas**.

**Cenário:** quando um agendamento depender de reservar um horário no MakersHub **e** confirmar
uma reserva em um sistema externo, uma falha definitiva externa pode exigir liberar a reserva
local.

**Critério importante:** falha no aviso do Teams **não** deveria necessariamente cancelar uma
reunião válida. Uma etapa acessória pode ser apenas **retentada**. Saga exige definir o que é
obrigatório, compensável ou irreversível.

| Etapa | Natureza | Ação em caso de falha posterior |
|---|---|---|
| Reservar horário local | Compensável | Liberar o horário |
| Confirmar reserva externa | Pivô | Se falhar antes: compensa o local |
| Notificar Teams | Retentável | Retry idempotente |
| Emitir confirmação ao cliente | Retentável | Retry idempotente |

---

## 7. Trade-offs

A Saga prioriza **Disponibilidade e Tolerância a Partições (AP)** em detrimento de **Consistência
imediata (C)**.

### Vantagens

- **Alta escalabilidade e disponibilidade:** serviços processam etapas independentemente, sem
  prender conexões nem travar tabelas remotas esperando HTTP de terceiros.
- **Suporte a processos de longa duração:** minutos, dias ou semanas (aprovação manual de crédito,
  compensação bancária) — impraticável com transação SQL normal.
- **Resiliência a falhas parciais:** falhas transitórias recuperam-se via retries sem abortar tudo.

### Desvantagens

- **Perda total de isolamento:** o "I" do ACID — Dirty Reads, Lost Updates, Non-repeatable Reads.
- **Complexidade das compensações:** desfazer ≠ ROLLBACK; é programar a operação inversa de
  negócio, e nem tudo é reversível.
- **Falha na própria compensação:** se uma compensação quebra, o sistema entra em estado
  inconsistente permanente → exige alertas críticos e intervenção humana.
- **Explosão no custo de testes:** matriz combinatória (falha em T1, falha em T2 com sucesso em C1,
  falha em T2 com falha em C1, quedas de rede no meio da compensação, timeouts dúbios…).

### Coreografia vs Orquestração — custos

| Critério | Coreografia | Orquestração |
|---|---|---|
| Complexidade operacional | Baixa no início (só o broker) | Alta (cluster de workflows duráveis) |
| Risco arquitetural | Event spaghetti / dependências circulares | Monólito distribuído (*Smart Coordinator, Dumb Services*) |
| Visibilidade | Cega (precisa tracing distribuído) | Cristalina (fluxo em um lugar) |

---

## 8. Como Outbox e Saga trabalham juntos

**Não são concorrentes; são complementares.**

Em qualquer arquitetura distribuída moderna, uma Saga **usa o Transactional Outbox como canal de
transporte**. Quando o Orquestrador (ou um participante) conclui sua transação local, ele **não**
faz chamada de rede direta para o próximo serviço: salva o estado local e coloca a mensagem do
próximo passo na sua tabela Outbox.

Dessa forma, a própria execução das etapas da Saga se torna **à prova de falhas de
infraestrutura**.

```
Saga step commit ──┬── UPDATE business_table
                   └── INSERT outbox_event (próximo comando/evento)
                          │
                          ▼
                   publisher / CDC ──> broker ──> próximo participante
```

---

## 9. Referências

### Frameworks e bibliotecas

- **Temporal** — *durable execution* / workflow orchestration com compensações duráveis.
- **Eventuate Tram Sagas** — orquestração de Saga em Java, didática.
- **Dapr Workflows** — workflows distribuídos com building blocks.
- **XState** — state machines/statecharts para orquestração no front (não é durável).

### Aplicações de referência

- **Eventuate Customers and Orders** — Saga + CQRS + microserviços.
- **Temporal samples** — `reserve inventory → charge payment → create shipment` com
  `cancel shipment → refund payment → release inventory` durável.

Ver [`docs/referencias/repositorios.md`](../referencias/repositorios.md).
