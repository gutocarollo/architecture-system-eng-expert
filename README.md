# architecture-system-eng-expert

Repositório de estudo e referência de **arquitetura de sistemas distribuídos**, com foco em:

- Padrões de consistência e integração de dados (**Dual Write, Transactional Outbox, CDC, Saga**)
- Catálogo completo de padrões de arquitetura (aplicação, distribuídos, mensageria, resiliência, cache, DDD, deploy, observabilidade)
- Aplicação prática à stack **MakersHub** (Next.js/React + FastAPI + PostgreSQL + Redis + Airflow + integrações Bitbucket/Jira/Salesforce)
- Curadoria de **skills, frameworks/libs e aplicações open source** de referência para cada padrão

## Curso em Nextra e MDX

O curso publicado está em [Arquitetura na prática](https://fazcapital-arquitetura-na-pratica.navy-teal-7786.chatgpt.site). Ele usa uma senha compartilhada validada pelo servidor e permite estudar sem uma conta ChatGPT. A senha está no Keychain do proprietário, no serviço `com.fazcapital.sites.fbi4991`, conta `course-password`; o valor não é versionado.

O [curso aplicado](content/index.mdx) organiza o material nos quatro tipos de documentação do Diátaxis. Os capítulos explicam as decisões; os tutoriais conduzem experiências locais; os guias ajudam a investigar e recuperar fluxos; os catálogos servem à consulta. A navegação começa por dores de agendamento, integração, indicadores, capacidade e operação.

```sh
npm ci
npm run build
COURSE_PORT=$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')
npm run start -- --hostname 127.0.0.1 --port "$COURSE_PORT"
```

A conferência estrutural de páginas, links e cobertura usa `npm run check:course`. Ela localiza conteúdo e aponta pendências; a aprovação do significado pertence ao council, com recibos na pasta da frente.

O servidor imprime o endereço local. Para editar o conteúdo, use `npm run dev` com a mesma opção de porta. O projeto usa os componentes e a navegação padrão do Nextra; as páginas ficam em `content/`.

Os [recibos de evidência](content/referencia/evidencias.mdx) distinguem código local, configuração observada, histórico e propostas. Os números do PostgreSQL e a linhagem do FazGraph têm data e escopo. O material original em `docs/` continua disponível como corpus de entrada. O [plano desta frente](tasks/architecture-course-2026-10-14/plan.md) contém a organização do trabalho, e o [registro de agentes](tasks/architecture-course-2026-10-14/subagent-routing.md) documenta as ondas e o reuso.

## Aprenda com uma falha e corrija uma cópia

As [jornadas por caso](content/jornadas/index.mdx) conectam dezoito problemas à explicação, ao tutorial, ao guia e à referência do mesmo caso. Sete usam código histórico do MakersHub e do Airflow. Onze usam modelos financeiros hipotéticos, identificados como tal. A matriz conserva observações delimitadas dos 310 conceitos dos 18 grupos e dos quarenta prioritários; ela não apresenta esses modelos como implementações integrais de protocolos ou como a arquitetura interna da XP.

Comece pela [comissão duplicada na junção](content/jornadas/query-grain-postgres/index.mdx) ou pela [gravação que perde uma alteração concorrente](content/jornadas/revision-cas-postgres/index.mdx). Ambos executam SQL histórico em um PostgreSQL descartável. O tutorial leva você de uma cópia que falha ao mesmo contrato passando após o patch.

Os laboratórios Python, os dois casos PostgreSQL e o retry histórico do Airflow têm pré-condições próprias nos seus READMEs:

```sh
python3 labs/architecture/setup_labs.py
python3 labs/architecture/run_all.py
python3 labs/architecture/check_challenges.py
python3 labs/architecture/check_invariants.py
python3 labs/architecture/check_matrix.py
python3 labs/postgres-lineage/run.py
python3 labs/postgres-lineage/check_challenges.py
python3 labs/airflow-lock-retry/run.py
python3 labs/airflow-lock-retry/check_challenge.py
```

Para regenerar os textos após mudar um modelo, execute os runners e siga a ordem de geração indicada em [labs/architecture/README.md](labs/architecture/README.md). Depois da geração das duas frentes, execute `python3 tasks/FBI-4991-arquitetura-nextra/execution/airflow-learning/author_pages.py` e, em seguida, `python3 tasks/FBI-4991-arquitetura-nextra/execution/postgres-learning/author_pages.py` e `python3 tasks/FBI-4991-arquitetura-nextra/execution/postgres-learning/integrate_pages.py` para recompor os casos PostgreSQL e sua navegação. Regenerar não substitui a revisão independente.

A busca global fica no cabeçalho do Nextra e usa o índice Pagefind criado no build. A tecla `/` leva o foco ao campo. O percurso de uma consulta e os links entre os quatro tipos são conferidos em navegador sem abrir a interface do usuário.

A execução e os bloqueios da [Story FBI-4991](https://fazcapital.atlassian.net/browse/FBI-4991) ficam em [tasks/FBI-4991-arquitetura-nextra/execution](tasks/FBI-4991-arquitetura-nextra/execution). Um recibo de parsing, contagem ou autoria não equivale ao aceite da Story.

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

O texto original em `docs/aplicado` apresenta aplicações propostas. A trilha em `content/` distingue fontes de código, configuração datada, evolução histórica e hipótese. Um commit selecionado não comprova que a mesma versão está implantada. As práticas usam fixtures sintéticas; os valores reais publicados são agregados, com consulta e horário. Cada referência informa o mecanismo e o limite que a fonte permite estudar.
