# Documentação — architecture-system-eng-expert

Índice geral do material. Tudo aqui é documentação de estudo/referência.

## 1. Consistência e integração de dados

- [Dual Write e alternativas](consistencia/dual-write-e-alternativas.md)
  — o problema, por que surge, e as 5 formas de resolvê-lo (além de Outbox e Saga).
- [Trade-offs: Outbox vs Saga](consistencia/tradeoffs-outbox-saga.md)
  — vantagens, custos, matriz consolidada e quando usar cada um.

## 2. Transactional Outbox (em profundidade)

- [Outbox — documento completo](outbox/README.md)
  — o que é, Dual Write, anatomia da tabela, Polling vs CDC, idempotência, implementação, trade-offs e alternativas.

## 3. Saga (em profundidade)

- [Saga — documento completo](saga/README.md)
  — o que é, compensação semântica, tipos de transação (compensável/pivô/retentável), coreografia vs orquestração,
  falta de isolamento e Semantic Lock.

## 4. Problemas de sistemas distribuídos

- [Taxonomia de problemas](problemas/taxonomia-sistemas-distribuidos.md)
  — as 7 categorias estruturais de problemas e o mapa problema → padrão de resolução.

## 5. Catálogo de padrões

- [Catálogo completo de padrões](catalogos/catalogo-patterns.md)
  — os 18 grupos: arquiteturas de aplicação, distribuídos/consistência, mensageria, CQRS/Event Sourcing,
  banco/armazenamento, cache, resiliência, concorrência, APIs, DDD, decomposição, deploy, HA, segurança,
  observabilidade, workflow, GoF e o core moderno dos 40.

## 6. Aplicado ao MakersHub

- [Aplicação dos 40 padrões ao dia a dia](aplicado/aplicacao-makershub-40-patterns.md)
  — item por item, com casos reais, dores resolvidas e priorização por dor concreta.

## 7. Referências curadas

- [Livros canônicos](referencias/livros.md)
- [Repositórios GitHub de referência](referencias/repositorios.md)
- [Skills de arquitetura (agent skills)](referencias/skills.md)
- [Catálogo 40 padrões × skills × frameworks × OSS](referencias/catalogo-40-patterns-skills-frameworks.md)
- [Stack MakersHub/Airflow/PostgreSQL/Salesforce — referências](referencias/stack-makershub-airflow-postgres-salesforce.md)

## Curso navegável

A versão em [Nextra e MDX](../content/index.mdx) reorganiza estes textos com Diátaxis e casos datados do MakersHub e do Airflow. Para abrir o curso localmente, siga os comandos no [README do projeto](../README.md). O conteúdo deste diretório permanece como fonte do material fornecido.
