# Skills de arquitetura (Agent Skills) — curadoria

> Critério: **não** tratar "mais estrelada" como sinônimo de "melhor para aquele padrão".
> Skills de arquitetura específicas ainda têm bem menos estrelas que os grandes skill-packs
> generalistas. Separe **skill para raciocinar/implementar** de **framework/lib canônica** e de
> **aplicação de referência**.

## Skill-packs usados como base

| ID | Skill/repo | Papel |
|---|---|---|
| S1 | `wshobson/agents` (~40k★) | `architecture-patterns`, `microservices-patterns`, Kubernetes, service mesh |
| S2 | `j4flmao/agent-skills` | Melhor cobertura específica: Saga, Outbox, CQRS, Event Sourcing, caching, idempotency, locks, BFF, API gateway, resilience |
| S3 | `wondelai/skills` (~2.3k★) | `system-design`, arquitetura geral |
| S4 | `mblode/agent-skills` | `codebase-architecture`, fronteiras e contratos entre módulos |
| S5 | `addyosmani/agent-skills` (~95k★) | Engenharia/qualidade/implementação; complemento |
| S6 | `obra/superpowers` (~291k★) | Metodologia de execução, debugging, planejamento |
| S7 | Redpanda Agent Skills | Skills oficiais para streaming, producers, consumers, consumer groups, transactions, idempotência |
| S8 | Dapr Skills | Skills oficiais/comunitárias para workflows e distributed applications |

> O formato **Agent Skills** tem especificação aberta e repositório próprio com ~26k★ — mantenha
> tudo compatível com `SKILL.md`.

## Estrutura que se adotaria para skills próprias

```
architecture-skills/
│
├── foundations/
│   ├── distributed-systems/
│   ├── consistency/
│   ├── ddd/
│   └── messaging/
│
├── patterns/
│   ├── transactional-outbox/
│   ├── saga/
│   ├── cqrs/
│   ├── event-sourcing/
│   ├── cache-aside/
│   ├── circuit-breaker/
│   ├── distributed-lock/
│   ├── bff/
│   ├── strangler/
│   └── ...
│
└── references/
    ├── temporal/
    ├── debezium/
    ├── eventuate/
    ├── dapr/
    ├── resilience4j/
    ├── envoy/
    ├── etcd/
    ├── vitess/
    └── xstate/
```

Cada `SKILL.md` teria, obrigatoriamente:

1. Problem
2. When to use
3. When NOT to use
4. Failure modes
5. Decision tree
6. Canonical implementation
7. Preferred OSS libraries
8. Reference OSS implementations
9. Alternatives/trade-offs
10. Testing strategy
11. Observability
12. Production checklist
13. Anti-patterns
14. References

> **A parte mais valiosa:** não transformar os patterns em 40 "receitas" isoladas, mas numa
> biblioteca **roteável**: o agente reconhece o problema e carrega somente a skill relevante —
> evitando gastar dezenas de milhares de tokens com documentação que não participa da decisão atual.

## Skills relevantes já disponíveis neste ambiente

O ambiente de trabalho já oferece skills de arquitetura que cobrem boa parte deste corpus, por
exemplo: `architecture-patterns`, `microservices-patterns`, `backend-*` (idempotency, transactional-outbox,
message-queue, caching, resilience, event-sourcing, cqrs, distributed-locking, bff, saga via
orchestration), `system-design`, `domain-driven-design`, `clean-architecture`, `release-it`,
`data-streaming`, `makershub-architecture-router`, entre muitas outras. Use-as como camada de
raciocínio e este repositório como corpus de referência.
