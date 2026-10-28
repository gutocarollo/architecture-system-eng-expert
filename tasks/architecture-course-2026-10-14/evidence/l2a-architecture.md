# S2 — Matriz de 22 estilos de arquitetura

## Escopo, composição e prova

O checkout desta evidência é o worktree de estudo, branch **perfect-citizen-a30f5998**, SHA **23d5d158d3a964dceba296296368ec14bcd8970b**. O MakersHub não foi editado. O CodeGraph não está instalado neste worktree; reutilizei a exploração S2 existente em [s2-application.md](s2-application.md), sem refazer buscas amplas nos três fluxos.

A composição aproveitável já observada é concreta: Call Sprint percorre página, hook, DataManager, ApiClient, rota FastAPI, serviço, repositório e PostgreSQL; Seguros usa página, hook, DataManager, API, cache, serviço e repositório; Super R1 chama a rota de qualificação, serviço, repositório e integração Salesforce. A fonte desses caminhos é o checkout local MakersHub **main**, SHA **e233fb046ec333982cd1547171b0f0bd8d8d92ee**, com leituras registradas entre 15:59 e 16:03 UTC em 14/10/2026 na evidência S2. Isso prova organização de código no snapshot local, não deploy ou execução em produção.

Legenda: **OBS** significa caminho visto no código daquele checkout; **HIST** significa mudança registrada em commit histórico; **PROP** significa exercício proposto, ainda não implementado; **REF** significa exemplo público de código. **LEGADO** identifica material arquivado ou antigo, útil para estudar a forma, sem recomendação de adoção. Nenhuma linha reivindica estado de produção. As páginas e repositórios públicos foram consultados em 14/10/2026. Estrelas não foram coletadas nem usadas como medida de qualidade.

Os exemplos do MakersHub são âncoras de aula. Uma classificação não se estende ao sistema inteiro: pastas **service** e **repository** não provam modular monolith, DDD, Clean Architecture ou Hexagonal. A matriz fonte contém exatamente os 22 itens do [catálogo local](../../../docs/catalogos/catalogo-patterns.md#1-arquiteturas-de-aplicação).

## Organização e implantação

| # | Estilo | Definição precisa e exemplo MakersHub | Limite principal | Base e skill existente | Código OSS que demonstra a forma |
|---:|---|---|---|---|---|
| 1 | Layered / N-Tier | Camadas agrupam responsabilidades por papel e encaminham chamadas por fronteiras definidas. **OBS:** o fluxo de Call Sprint passa por UI, acesso a dados, API, serviço e repositório. | Cada camada pode virar passagem sem regra e ainda depender fortemente da seguinte; separação em camadas não prova limites de módulo. | FastAPI; [backend-layered-architecture](</Users/augustocarollo/.codex/skills/backend-layered-architecture/SKILL.md>). | [Full Stack FastAPI sample](https://github.com/fastapi/full-stack-fastapi-template/blob/master/backend/README.md) documenta endpoints, CRUD e modelos como áreas distintas. |
| 2 | Modular Monolith | Um processo e uma implantação contêm módulos de negócio com contratos e dependências controladas. **PROP:** separar Qualificação, Call Sprint e Indicadores de Seguros em módulos da mesma aplicação, sem alegar que isso já existe. | Um módulo ainda pode furar o limite lendo tabelas de outro; dividir pastas não cria isolamento. | .NET e contratos de módulo; [domain-driven-design](</Users/augustocarollo/.codex/skills/domain-driven-design/SKILL.md>). | [modular-monolith-with-ddd](https://github.com/kgrzybek/modular-monolith-with-ddd), cuja documentação descreve módulos e chamadas entre eles. |
| 3 | Microservices | Serviços implantáveis separadamente possuem contratos de rede e limites de dados e operação próprios. **PROP:** só separar Indicadores de Seguros se escala, equipe ou cadência de release independentes justificarem o novo serviço; o fluxo S2 atual é uma rota FastAPI, não uma prova de microserviços. | Retries, rede, observabilidade distribuída, consistência e operação passam a fazer parte do produto. | Spring Boot e Spring Cloud; [microservices-patterns](</Users/augustocarollo/.codex/skills/microservices-patterns/SKILL.md>). | [Spring Petclinic distribuído](https://github.com/spring-petclinic/spring-petclinic-microservices), declarado como versão distribuída com Spring Cloud. |
| 4 | SOA | Serviços de negócio com contratos interoperáveis são compartilhados por consumidores diferentes e podem ser coordenados por uma camada corporativa. **PROP:** oferecer uma operação de consulta de leads a mais de um canal; a rota de Call Sprint sozinha não constitui SOA. | Um barramento, catálogo ou esquema central pode virar gargalo e contrato corporativo rígido; SOA não é apenas “vários endpoints”. | Apache OFBiz Service Engine; [api-and-interface-design](</Users/augustocarollo/.codex/skills/api-and-interface-design/SKILL.md>) apoia contratos, não é uma skill exclusiva de SOA. | [Apache OFBiz](https://github.com/apache/ofbiz-framework) e [manual SOA do projeto](https://nightlies.apache.org/ofbiz/stable/ofbiz/html5/user-manual.html#service-engine). |
| 5 | Serverless | A plataforma administra provisionamento e escala da unidade de execução; a aplicação ainda define eventos, contratos, limites e observabilidade. **PROP:** recalcular um resumo de Seguros por evento ou agenda, sem propor deploy. | Limites de execução, cold start, acoplamento ao provedor e custo por chamada continuam exigindo desenho. | AWS Lambda e SAM; [serverless](</Users/augustocarollo/.codex/skills/serverless/SKILL.md>). | [AWS Serverless Ecommerce](https://github.com/aws-samples/aws-serverless-ecommerce-platform) é **LEGADO / arquivado em 2024**: prova a forma e os componentes, não uma recomendação de copiar a plataforma. |
| 6 | Microkernel / Plugin | Um núcleo pequeno expõe pontos de extensão estáveis e carrega plugins opcionais que acrescentam comportamento. **PROP:** permitir validadores de qualificação substituíveis apenas se houver demanda real de extensão por produto ou equipe. | Compatibilidade, segurança, dependências e ordem de plugins podem ser mais caras que manter variações no próprio módulo. | VS Code Extension API; [superset-plugins](</Users/augustocarollo/.agents/skills/superset-plugins/SKILL.md>) é uma referência de plugin para Superset, não um guia universal de microkernel. | [VS Code Extension Host](https://code.visualstudio.com/api/advanced-topics/extension-host) e [API de extensões](https://code.visualstudio.com/api), que documentam isolamento e pontos de contribuição. |

## Direção de dependências e organização por caso de uso

| # | Estilo | Definição precisa e exemplo MakersHub | Limite principal | Base e skill existente | Código OSS que demonstra a forma |
|---:|---|---|---|---|---|
| 7 | Hexagonal / Ports & Adapters | O núcleo define portas de entrada e saída; adaptadores traduzem HTTP, banco ou Salesforce sem fazer o núcleo depender deles. **PROP:** pôr portas explícitas ao redor do caso qualify e da gravação de roteamento. | Criar uma interface para cada função aumenta cerimônia sem isolar regra relevante. | Spring Boot; [clean-architecture](</Users/augustocarollo/.codex/skills/clean-architecture/SKILL.md>) cobre Ports & Adapters. | [Hexagonal Architecture sample](https://github.com/talehkarimov/hexagonal-architecture): o README separa core, adaptadores web e de banco. |
| 8 | Clean Architecture | Entidades e casos de uso ficam dentro; adaptadores e frameworks dependem para dentro, seguindo a regra de dependência. **PROP:** um caso de uso de qualificação que não importe FastAPI, SQLAlchemy ou SDK Salesforce. | A regra de dependência exige contratos e composição explícitos; camadas com nomes certos não bastam. | ASP.NET Core; [clean-architecture](</Users/augustocarollo/.codex/skills/clean-architecture/SKILL.md>). | [Ardalis CleanArchitecture](https://github.com/ardalis/CleanArchitecture), template público com projetos centrais e externos. |
| 9 | Onion Architecture | O modelo de domínio ocupa o centro; aplicação, infraestrutura e interface ficam em anéis externos e dependem para dentro. **PROP:** pôr elegibilidade de assessor no centro e Salesforce/SQL nas bordas; S2 não provou um modelo de domínio assim. | Mapeamento ORM, transações e limites entre anéis podem exigir decisões adicionais. | .NET; [clean-architecture](</Users/augustocarollo/.codex/skills/clean-architecture/SKILL.md>) declara cobertura de Onion. | [dotnet-template-onion](https://github.com/pereiren/dotnet-template-onion) é **LEGADO / exemplo .NET 6** e afirma Onion explicitamente. |
| 10 | Vertical Slice | O código se agrupa por funcionalidade executável, mantendo perto endpoint, entrada, validação, handler e persistência necessária. **PROP:** fatias qualify-d1, call-list e insurance-kpi; não foi observado esse layout no S2. | Código transversal pode duplicar; uma fatia ainda precisa respeitar políticas e dados compartilhados. | ASP.NET Core e MediatR; [codebase-architecture](</Users/augustocarollo/.codex/skills/codebase-architecture/SKILL.md>) é orientação adjacente, não guia exclusivo de VSA. | [Vertical Slice API Template](https://github.com/mehdihadeli/vertical-slice-api-template), que organiza o exemplo por feature. |

## Padrões de apresentação e composição de interface

MVC, MVP e MVVM abaixo descrevem **a mesma interação pequena**: o operador escolhe Manual ou Automático na janela do Call Sprint. Nenhum deles rotula o MakersHub inteiro. O S2 observou useCallLifecycle compartilhando estado e ações entre duas views; isso não prova MVVM. A mudança histórica **a55d4d4a004511106ecc23354de0abf23f7d6ddb** tornou os dois botões explícitos e evitou alternar quando o modo já era o escolhido; ela não prova paridade visual nem a arquitetura global.

| # | Estilo | Definição precisa e exemplo MakersHub | Limite principal | Base e skill existente | Código OSS que demonstra a forma |
|---:|---|---|---|---|---|
| 11 | MVC | Controller recebe o evento da view, altera ou consulta o model e encaminha a renderização. **PROP:** o clique em Automático chega ao controller, que atualiza o modo do seletor. | O controller pode concentrar estado e regra; a interação entre view e model varia conforme o framework. | Spring MVC; [frontend-ui-engineering](</Users/augustocarollo/.agents/skills/frontend-ui-engineering/SKILL.md>) ajuda a construir a UI, sem ser skill específica de MVC. | [Spring Petclinic OwnerController](https://github.com/spring-projects/spring-petclinic/blob/main/src/main/java/org/springframework/samples/petclinic/owner/OwnerController.java) com templates Thymeleaf. |
| 12 | MVP | A view é passiva; encaminha ações ao presenter, que consulta o model e manda a view renderizar. **PROP:** selectMode("automatic") chama o presenter e ele responde com o estado visível. | Interface passiva e presenter testável adicionam contratos e código de ligação. | Android SDK; [frontend-ui-engineering](</Users/augustocarollo/.agents/skills/frontend-ui-engineering/SKILL.md>) é adjacente, sem skill MVP instalada. | [Android architecture samples](https://github.com/esiek/android-architecture) catalogam o app Todo em variante MVP; exemplo educacional **LEGADO**. |
| 13 | MVVM | A view observa ou vincula um modelo de apresentação que expõe estado e comandos. **PROP:** a janela observa mode e chama selectMode; a tela reflete a mudança do modelo. | Binding reativo e invalidação de estado podem ocultar o caminho da ação e aumentar o custo de depuração. | AndroidX ViewModel e LiveData; [react-state-management](</Users/augustocarollo/.codex/skills/react-state-management/SKILL.md>) trata estado React, não define MVVM. | [Android architecture samples](https://github.com/esiek/android-architecture) catalogam o mesmo app Todo em variantes MVVM; exemplo educacional **LEGADO**. |
| 14 | PAC | Cada agente de interação reúne Presentation, Abstraction e Control; agentes se coordenam hierarquicamente e Presentation não acessa Abstraction diretamente. **PROP:** painel financeiro composto por agentes independentes de filtro e indicadores. | A hierarquia e a comunicação entre controles custam mais que uma view simples. | WakaPAC; **gap:** não encontrei SKILL.md específica de PAC. [frontend-ui-engineering](</Users/augustocarollo/.agents/skills/frontend-ui-engineering/SKILL.md>) é apenas apoio de interface. | [WakaPAC](https://github.com/quellabs/wakapac) e [seus exemplos](https://github.com/quellabs/wakapac/tree/main/examples) provam um runtime/demo PAC; não provam adoção por aplicação financeira de produção. |
| 15 | Component-Based | O sistema se compõe de componentes com contratos de entrada e saída; isso descreve composição, não fronteiras de domínio. **HIST:** InsuranceProposalsAnalysisCard.tsx recebeu tratamento de data no commit **7101d3a4babe95081b0b41d35ec305c08bf8a577**. | Reuso pode acoplar aparência e comportamento; a pasta de componentes não define módulo de negócio. | React e Next.js; [component-family-consistency](</Users/augustocarollo/.agents/skills/component-family-consistency/SKILL.md>) cuida de famílias visuais, não da arquitetura inteira. | [Vercel Next.js Commerce](https://github.com/vercel/commerce/tree/main/components), aplicativo público composto por componentes React. |

## Distribuição, estado compartilhado e fluxo de dados

| # | Estilo | Definição precisa e exemplo MakersHub | Limite principal | Base e skill existente | Código OSS que demonstra a forma |
|---:|---|---|---|---|---|
| 16 | Space-Based | Unidades de processamento executam perto de um conjunto de dados particionado e replicado em memória; persistência pode ocorrer de forma assíncrona. Não é sinônimo de cache Redis. **PROP:** só estudar para um caminho transacional de alta contenção após medir o gargalo; a consulta de KPIs em Seguros não basta como justificativa. | Replicação, reconciliação com o banco e consistência elevam custo e risco operacional. | Apache Ignite é uma base de grid em memória; skill específica de Space-Based não encontrada; [architecture-optimization](</Users/augustocarollo/.codex/skills/architecture-optimization/SKILL.md>) é apoio geral. | **Gap de prova atual:** a [página histórica do XAP](https://xap.github.io/) lista hola-mundo para Space-Based, mas o link de código GitHub indicado ali retorna 404. Tratar como **LEGADO**, não como aplicação OSS atual verificada. |
| 17 | Cell-Based | O sistema se replica em células independentes, cada qual com dados e recursos isolados; um roteador direciona cada cliente à sua célula. **PROP:** isolar populações de tenants apenas se objetivos de falha e operação justificarem; S2 não prova roteamento por célula nem isolamento multi-tenant. | Cada célula aumenta roteamento, monitoramento, atualização e capacidade duplicada; operações entre células ficam difíceis. | AWS CDK e roteamento por tenant; [multi-tenant-architecture](</Users/augustocarollo/.codex/skills/multi-tenant-architecture/SKILL.md>) cobre isolamento de tenant, não o padrão Cell-Based inteiro. | [AWS SaaS Cell-Based Architecture](https://github.com/aws-samples/aws-saas-cell-based-architecture), workshop com criação de células e roteamento. |
| 18 | Actor Model | Cada actor mantém estado próprio, processa uma mensagem por vez e conversa com outros actors por mensagens assíncronas. **PROP:** serializar alterações de um lead por identidade de actor só se a regra de ordenação for confirmada. | Um actor ocupado vira ponto quente; mensagens não criam transação atômica entre actors. | Microsoft Orleans; [backend-concurrency-mechanics](</Users/augustocarollo/.codex/skills/backend-concurrency-mechanics/SKILL.md>) apoia mecânica de concorrência, não é guia específico de Actor. | [Orleans](https://github.com/dotnet/orleans) implementa virtual actors; [samples](https://github.com/dotnet/orleans/tree/main/samples) inclui aplicações oficiais. |
| 19 | Peer-to-Peer | Pares podem consumir e fornecer recursos diretamente, formando uma rede sem servidor central obrigatório no caminho de cada troca. **PROP hipotética:** sincronizar conteúdo público e não autoritativo entre pares desconectados; não trocar estado de leads ou apólices dessa forma. | Descoberta de pares, identidade, abuso, conflitos e revogação precisam de desenho próprio. | libp2p; **gap:** não encontrei SKILL.md específica de P2P. [architecture-patterns](</Users/augustocarollo/.codex/skills/architecture-patterns/SKILL.md>) é apoio geral, não uma competência de redes P2P. | [IPFS Kubo](https://github.com/ipfs/kubo) usa libp2p e descreve uma rede P2P; [configuração de peers](https://github.com/ipfs/kubo/blob/master/docs/config.md#bootstrap) mostra a descoberta inicial. |
| 20 | Blackboard | Fontes de conhecimento independentes publicam contribuições em estado compartilhado; um scheduler escolhe qual fonte pode avançar a solução. **PROP:** estudo de reconciliação financeira com entradas sintéticas e trilha de contribuições; indicadores SQL de Seguros não precisam desse mecanismo. | O estado comum e a seleção de próximos passos precisam de autoria, concorrência e proveniência. | Base REST e grafo de conhecimento; **gap:** não encontrei SKILL.md específica de Blackboard. [architecture-patterns](</Users/augustocarollo/.codex/skills/architecture-patterns/SKILL.md>) é apenas apoio geral. | [NCATS Blackboard](https://github.com/ncats/blackboard) é um exemplo real do padrão, mas está **LEGADO / arquivado em 12/06/2026** e não deve ser indicado para produção. |
| 21 | Pipe and Filter | Filtros transformam registros em etapas independentes; pipes ou filas transportam a saída de uma etapa à seguinte. **PROP:** pipeline de apólices: ler agregado, normalizar data, agrupar por período e persistir. O Promise.all de chamadas de Seguros observado no S2 não é esse pipeline. | Ordem, backpressure, dados inválidos e efeitos externos precisam de tratamento explícito. | Apache NiFi; [data-streaming](</Users/augustocarollo/.codex/skills/data-streaming/SKILL.md>). | [Apache NiFi Developer Guide](https://github.com/apache/nifi/blob/main/nifi-docs/src/main/asciidoc/developer-guide.adoc) define Processor como bloco de um dataflow e mostra roteamento. |
| 22 | Event-Driven Architecture | Um produtor publica fatos de negócio por contrato; consumidores reagem sem o produtor executar cada consequência diretamente. **PROP:** depois de confirmar uma qualificação, publicar evento durável para consumidores; S2 observou persistência de intenção e integração Salesforce, não um broker ou EDA. | Entrega duplicada, atraso, evolução de schema e rastreamento atravessam serviços. | Watermill com Kafka ou RabbitMQ; [backend-message-queue](</Users/augustocarollo/.codex/skills/backend-message-queue/SKILL.md>). | [ThreeDotsLabs Event-Driven Example](https://github.com/ThreeDotsLabs/event-driven-example) integra webhooks de GitHub com Grafana e Slack por Watermill e mensagens. |

## Três diagramas propostos: o mesmo seletor Manual/Automático

Os três desenhos abaixo são propostas para ensinar contratos de apresentação. Eles não descrevem o código atual. A mudança histórica que evitou alternar um modo que já estava ativo explica o comportamento do seletor, sem classificar a aplicação inteira.

### MVC proposto

~~~mermaid
sequenceDiagram
    actor Operador
    participant View
    participant Controller
    participant Model
    Operador->>View: escolhe Automatico
    View->>Controller: selectMode(automatic)
    Controller->>Model: setMode(automatic)
    Model-->>View: mode changed
    View-->>Operador: destaca Automatico
~~~

### MVP proposto

~~~mermaid
sequenceDiagram
    actor Operador
    participant View
    participant Presenter
    participant Model
    Operador->>View: escolhe Automatico
    View->>Presenter: selectMode(automatic)
    Presenter->>Model: setMode(automatic)
    Model-->>Presenter: mode=automatic
    Presenter->>View: render(automatic)
    View-->>Operador: destaca Automatico
~~~

### MVVM proposto

~~~mermaid
sequenceDiagram
    actor Operador
    participant View
    participant PresentationModel as ViewModel
    participant Model
    Operador->>View: escolhe Automatico
    View->>PresentationModel: selectMode(automatic)
    PresentationModel->>Model: setMode(automatic)
    Model-->>PresentationModel: mode=automatic
    PresentationModel-->>View: observable mode update
    View-->>Operador: destaca Automatico
~~~

## Fontes primárias para escolhas e limites

As recomendações de adoção são sustentadas por documentação oficial, enquanto os repositórios de exemplo provam estruturas concretas: [Microsoft: arquiteturas web comuns](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures), [Microsoft: arquitetura de microserviços](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/), [AWS: Cell-Based Architecture](https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html), [AWS: Serverless Applications Lens](https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/serverless-applications-lens.html), [Fowler: GUI Architectures](https://martinfowler.com/eaaDev/uiArchs.html), [React: reutilizar lógica com custom hooks](https://react.dev/learn/reusing-logic-with-custom-hooks), [Microsoft Orleans: modelo virtual actor](https://learn.microsoft.com/en-us/dotnet/orleans/overview) e [Apache NiFi: developer guide](https://nifi.apache.org/docs/nifi-docs/html/developer-guide.html).

Recomendação didática: começar pelos fluxos em camadas já observados; comparar modular monolith e vertical slice como opções de organização; deixar Microservices, Serverless, Cells e Space-Based como decisões que exigem uma necessidade medida de implantação, escala ou isolamento. Para a UI, usar o mesmo seletor em MVC, MVP e MVVM e ensinar apenas o limite do contrato de apresentação que cada escolha cria. Os samples arquivados ou antigos servem para reconhecer a estrutura, não para selecionar versões, segurança ou plataforma de produção.
