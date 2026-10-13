# architecture-system-eng-expert

Repositório de estudo e referência de **arquitetura de sistemas distribuídos**, com foco em:

- Padrões de consistência e integração de dados (**Dual Write, Transactional Outbox, CDC, Saga**)
- Catálogo completo de padrões de arquitetura (aplicação, distribuídos, mensageria, resiliência, cache, DDD, deploy, observabilidade)
- Aplicação prática à stack **MakersHub** (Next.js/React + FastAPI + PostgreSQL + Redis + Airflow + integrações Bitbucket/Jira/Salesforce)
- Curadoria de **skills, frameworks/libs e aplicações open source** de referência para cada padrão

## Estrutura

```
architecture-system-eng-expert/
├── README.md                     ← este arquivo
├── docs/                         ← documentação (o material didático)
│   ├── README.md                 ← índice geral da documentação
│   ├── outbox/                   ← Transactional Outbox (em profundidade)
│   ├── saga/                     ← Saga Pattern (em profundidade)
│   ├── consistencia/             ← Dual Write e alternativas, trade-offs
│   ├── problemas/                ← taxonomia de problemas de sistemas distribuídos
│   ├── catalogos/                ← catálogo dos 18 grupos de padrões
│   ├── aplicado/                 ← aplicação ao dia a dia (MakersHub)
│   └── referencias/              ← livros, repositórios, skills, frameworks
└── references/                   ← fontes clonadas
    ├── data-engineer-handbook/   ← dataexpert-io/data-engineer-handbook
    └── repos/                    ← repositórios open source de referência
```

## Comece por aqui

| Se você quer… | Leia |
|---|---|
| Entender **Outbox** a fundo | [`docs/outbox/README.md`](docs/outbox/README.md) |
| Entender **Saga** a fundo | [`docs/saga/README.md`](docs/saga/README.md) |
| Entender o problema **Dual Write** e suas alternativas | [`docs/consistencia/dual-write-e-alternativas.md`](docs/consistencia/dual-write-e-alternativas.md) |
| Comparar **trade-offs** das duas arquiteturas | [`docs/consistencia/tradeoffs-outbox-saga.md`](docs/consistencia/tradeoffs-outbox-saga.md) |
| Ver a **taxonomia de problemas** de sistemas distribuídos | [`docs/problemas/taxonomia-sistemas-distribuidos.md`](docs/problemas/taxonomia-sistemas-distribuidos.md) |
| Consultar um **padrão específico** | [`docs/catalogos/catalogo-patterns.md`](docs/catalogos/catalogo-patterns.md) |
| Ver **onde aplicar** na stack MakersHub | [`docs/aplicado/aplicacao-makershub-40-patterns.md`](docs/aplicado/aplicacao-makershub-40-patterns.md) |
| Escolher **skills, frameworks e OSS** por padrão | [`docs/referencias/catalogo-40-patterns-skills-frameworks.md`](docs/referencias/catalogo-40-patterns-skills-frameworks.md) |
| A lista de **livros** canônicos | [`docs/referencias/livros.md`](docs/referencias/livros.md) |
| A lista de **repositórios** de referência | [`docs/referencias/repositorios.md`](docs/referencias/repositorios.md) |

## Referências clonadas

- **data-engineer-handbook** → `references/data-engineer-handbook/` (DataExpert-io)
- Repositórios open source de referência → `references/repos/` (ver [`docs/referencias/repositorios.md`](docs/referencias/repositorios.md))

## Nota sobre escopo e rigor

Os exemplos aplicados ao MakersHub são **aplicações propostas** a dores descritas — não uma
afirmação de que o código atual já implementa cada padrão. Cada padrão é documentado com:
o que é · quando usar · quando NÃO usar · modos de falha · implementação canônica · frameworks
preferidos · aplicações OSS de referência · alternativas e trade-offs.
