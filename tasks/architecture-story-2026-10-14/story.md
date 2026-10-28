# Criar documentação de arquitetura aplicada em Nextra/Diátaxis com casos reais da Faz Capital

## História do estudante

Como estudante e integrante da equipe que trabalha com MakersHub, Airflow e integrações da Faz Capital, quero aprender os conceitos de arquitetura pelos problemas, dados e caminhos reais dos nossos sistemas, para entender por que uma operação falha, quais garantias uma solução oferece e como escolher uma alternativa antes de alterar o código.

## Objetivos solicitados

1. Transformar todo o texto fornecido em documentação MDX no padrão do Nextra, usando a skill do framework Diátaxis. A cobertura inclui todos os conceitos dos 18 grupos e os 40 padrões destacados como prioritários; o pedido não se limita à lista de quarenta.
2. Analisar e abstrair o conteúdo, respeitar seus níveis arquiteturais e agrupar os conceitos em capítulos que façam sentido. A organização deve ajudar o estudante a passar do problema ao mecanismo e à decisão.
3. Produzir uma leitura didática e estimulante, com ganchos que mostrem o valor de aprender cada conceito e histórias curtas que expliquem a dor, sua causa sustentada por evidência e o que mudaria com outra escolha. A prosa deve ser clara para uma pessoa de 18 anos.
4. Explicar os conceitos com casos e códigos reais do MakersHub e do Airflow, usando o MCP PostgreSQL para obter dados e valores reais e o MCP FazGraph para identificar relações e blast radius.
5. Usar o histórico de commits e problemas já enfrentados para explicar por que aconteceram e como o conhecimento dos conceitos poderia ter orientado a solução desde o início. O pedido descreveu como ideal analisar todos os commits e problemas; um censo de metadados não deve ser apresentado como análise causal de todo esse histórico.
6. Curar, para cada item, skills relevantes, em destaque e com estrelas verificadas, bibliotecas e frameworks GitHub que implementem o mecanismo, e pelo menos uma aplicação real open source de referência.
7. Executar o trabalho em ondas, com especialistas e auxiliares distribuídos pela complexidade, council e o máximo de reuso de agentes aquecidos e de contexto/cache verificável.

## Escopo conceitual integral

O conteúdo de cada grupo do texto original deve continuar rastreável até sua explicação e referência. Os grupos são:

1. Arquiteturas de aplicação, incluindo camadas, monólito modular, serviços, Serverless, Hexagonal/Clean/Onion, fatias verticais, MVC/MVP/MVVM/PAC, componentes, células, actors, P2P, Blackboard, Pipe and Filter e eventos.
2. Sistemas distribuídos e consistência, incluindo dual write, Outbox/Inbox/CDC, Sagas, 2PC/3PC/TCC, reservas e compensações, idempotência, entrega e efeitos, garantias de leitura, concorrência, locks/leases/fencing, relógios, quórum, eleição, consenso, Raft/Paxos e gossip.
3. Eventos e mensageria, incluindo Pub/Sub, filas e consumidores, Request/Reply, fan-out/fan-in, roteadores, filtros, tradução, enriquecimento, divisão, agregação, ordenação, correlação, DLQ, retries, atraso, prioridade, poison messages e streaming.
4. CQRS, Event Sourcing e modelos de leitura, incluindo handlers, modelos de escrita/leitura, projeções, views materializadas, snapshots e eventos de domínio/integração.
5. Banco e armazenamento, incluindo replicação, particionamento, sharding, hashing, WAL, logs, Copy-on-Write, armazenamento estruturado por log, amplificação de escrita, índices e pré-computação.
6. Cache, incluindo os modos de leitura/escrita, TTL, ausência, caches local/distribuído e em níveis, proteção contra recomputação simultânea, single-flight, warming, refresh e invalidação.
7. Resiliência, incluindo retry/backoff/jitter, circuit breaker, bulkhead, timeout/deadline, fallback, degradação, rejeição de carga, backpressure, limitação de taxa, saúde e recuperação.
8. Concorrência, incluindo locks, semáforos, CAS, estruturas lock-free/wait-free, actors, pools, Work Stealing, Fork/Join, Futures/Promises, Async/Await, Reactive Streams, single writer e dados imutáveis.
9. APIs e integração, incluindo gateway, BFF, composição/roteamento/offloading, proxies, mesh/sidecar/ambassador, Adapter/ACL/Facade, GraphQL Federation, RPC/REST/HATEOAS, webhooks, polling, SSE e WebSocket.
10. DDD, incluindo contexto delimitado, linguagem, entidades, valores, agregados, serviços, repositórios, factories, eventos, políticas, Specification e relações entre contextos.
11. Decomposição e evolução de sistemas, incluindo Strangler Fig, Branch by Abstraction, execuções paralelas e shadow, flags, Expand/Contract, modularização, extração e migração de dados.
12. Deploy e releases, incluindo Blue/Green, Canary, Rolling/Recreate/Shadow, Dark Launch, flags, entrega progressiva, A/B, infraestrutura imutável, IaC e GitOps.
13. Alta disponibilidade, incluindo modos ativo/passivo, standbys, regiões/zonas, quórum, failover, prevenção de split-brain, fencing, eleição, replicação e serviços stateless.
14. Segurança, incluindo Zero Trust, defesa em profundidade, privilégio mínimo, RBAC/ABAC/ReBAC, políticas, OAuth2/OIDC, troca de tokens, credenciais curtas, rotação, mTLS e identidade/segmentação.
15. Observabilidade, incluindo logs estruturados/centralizados, tracing, IDs de correlação/requisição, métricas RED/USE/Golden Signals, OpenTelemetry, health checks e monitoramento sintético.
16. Workflow e processamento, incluindo máquinas de estado, engines, DAGs, pipelines, orquestração/coreografia, filas/pools, batch/stream, Lambda/Kappa, MapReduce e divisão/coleta de trabalho.
17. Os padrões GoF de criação, estrutura e comportamento, incluindo todos os itens do texto original.
18. O núcleo de quarenta padrões modernos prioritários, como roteiro aprofundado relacionado aos outros grupos.

## Os quarenta itens que devem ser aprofundados

1. Modular Monolith.
2. Hexagonal Architecture / Ports and Adapters.
3. Vertical Slice Architecture.
4. DDD / Bounded Context.
5. Event-Driven Architecture.
6. Pub/Sub.
7. Transactional Outbox.
8. Change Data Capture — CDC.
9. Saga.
10. Idempotency.
11. CQRS.
12. Event Sourcing.
13. Materialized Views / Projections.
14. Cache Aside.
15. Refresh Ahead.
16. Circuit Breaker.
17. Retry com Exponential Backoff e Jitter.
18. Bulkhead.
19. Backpressure.
20. Rate Limiting.
21. API Gateway.
22. Backend for Frontend — BFF.
23. Strangler Fig.
24. Expand/Contract.
25. Blue/Green Deployment.
26. Canary Release.
27. Feature Flags.
28. Leader Election.
29. Distributed Lock com Lease e Fencing.
30. Replication.
31. Sharding.
32. Consistent Hashing.
33. Optimistic Concurrency.
34. Write-Ahead Log — WAL.
35. Sidecar.
36. Service Mesh.
37. Anti-Corruption Layer.
38. Competing Consumers.
39. Dead Letter Queue.
40. State Machine.

## Requisitos de entrega e de evidência

**R1 — Formato e organização.** Entregar os arquivos MDX, os metadados e a navegação do Nextra. Aplicar o Diátaxis para distinguir explicações, tutoriais, guias de tarefa e referência. Os capítulos devem expressar uma jornada de aprendizado; a presença do nome de um conceito em uma lista não constitui sua explicação.

**R2 — Cobertura.** Manter uma matriz que ligue todas as ocorrências do texto original aos conceitos, capítulos, exemplos e referências. Preservar distinções de significado, mesmo quando um termo aparece em mais de um nível. Explicar cada prioritário com problema, mecanismo, benefício, custo, limites e critérios de escolha.

**R3 — Casos reais e valores.** Usar dados e valores obtidos pelo MCP PostgreSQL e relações/blast radius obtidos pelo MCP FazGraph. Registrar consulta, resultado, fonte, ambiente e horário. Proteger credenciais e dados pessoais; agregados podem fundamentar os exemplos. Uma contagem não prova por si só a causa de um incidente.

**R4 — Código e produção.** Vincular os casos aos caminhos, funções e páginas reais quando isso ajudar o aprendizado. Distinguir o SHA de um checkout local do código efetivamente lido em um runtime. Afirmar implantação ou comportamento de produção somente com a prova correspondente. A solicitação de investigar o PR 362 e sua relação com CQRS exige leitura atual do PR e do código; a hipótese do pedido não é uma conclusão.

**R5 — Ecossistema distribuído.** Procurar exemplos no MakersHub, Airflow e scraping, incluindo suas interações com Salesforce, Azure, PostgreSQL, MinIO, SeaweedFS, Redis, n8n e dbt. Explicar o Airflow no Rancher/Kubernetes informado pelo usuário. Integrações não confirmadas devem permanecer identificadas como não confirmadas.

**R6 — Apresentação e cache.** Analisar que organização de apresentação o MakersHub utiliza no recorte examinado e comparar MVC, MVP e MVVM com exemplos de como a solução mudaria. Explicar os conceitos de Redis/cache já encontrados e apresentar, como propostas, a utilidade e o funcionamento dos que não foram encontrados.

**R7 — Diagramas.** Focar os exemplos em fluxos Mermaid que expliquem o macro, as decisões, as fronteiras entre sistemas, falhas e recuperação. Acrescentar funções, paths e páginas quando esclarecerem o caminho. Diferenciar desenho do código observado de desenho proposto.

**R8 — Alternativas financeiras.** Quando não houver exemplo implementado no ecossistema, criar um caso financeiro aplicado, como o que uma corretora poderia enfrentar. Usar XP apenas como referência de setor no cenário hipotético; não atribuir uma arquitetura real à empresa sem fonte.

**R9 — Retrospectivas.** Investigar commits e problemas, sustentar a causa das histórias selecionadas com fontes e explicar como os conceitos poderiam ter mudado a abordagem inicial. Registrar o universo e a profundidade realmente examinados. A intenção de analisar todo o histórico permanece distinta de um inventário de metadados ou de algumas autópsias.

**R10 — Skills e GitHub.** Para cada item, indicar skill pertinente, pelo menos um framework base e pelo menos uma aplicação real OSS de referência, além de bibliotecas complementares quando pertinentes. Verificar a evidência do mecanismo, popularidade, manutenção, licença e data da consulta. Para selecionar as skills mais estreladas e em tendência, declarar o universo comparado e o critério de seleção, citar fonte primária datada para a contagem de estrelas e apresentar uma medida de tendência no período informado, como crescimento de estrelas ou presença em um ranking datado. Sem essa medida, a tendência continua pendente; a contagem pontual de estrelas não pode substituí-la. Distinguir produto OSS, exemplo didático executável, modelo de referência e código source available. Estrelas pontuais não provam tendência, qualidade ou que uma biblioteca implementa qualquer padrão citado.

**R11 — Orquestração originalmente solicitada.** O usuário pediu pelo menos seis Sol 6.1 xhigh, pelo menos três Luna 6 max por Sol — mínimo de dezoito auxiliares —, divisão por complexidade, ondas, council e reuso máximo dos agentes aquecidos/cache. O council inicial foi especificado como um Opus 5.5, um Grok 4.7 xhigh e um Sol 6.1 xhigh. A mineração de histórico também mencionou Luna 6 ou Haiku 5.5 como opção.

**R12 — Emenda de modelo.** O usuário cancelou o Opus por prever falha da subscription e autorizou substituição por “muse muse wonder full high”, na grafia fornecida pelo usuário, Sol 6.1 xhigh, Grok 4.7 xhigh, AGY Gemini 3.8 Flash high ou OpenCode DeepSeek v4.1 Flash. A opção selecionada nesta execução foi um segundo Sol independente. A rota configurada ficou com dois Sol e um Grok no council; não houve chamada LLM ao Opus. A lista de alternativas autorizadas não comprova disponibilidade técnica de todas elas. Novos despachos devem observar a política de modelos vigente do proprietário.

**R13 — Clareza e verificação.** Escrever prosa completa em português, simples e concreta; manter identificadores e comentários de código em inglês. Conferir compilação MDX, navegação, anchors, cobertura e Mermaid. Separar prova de sintaxe, renderização e semântica; vincular a revisão independente aos hashes e fontes realmente examinados.

## Complemento posterior: busca global padrão do Nextra

Após a entrega, o usuário perguntou onde estava a busca global. A configuração entregue tinha search:false e search={null}; essa foi uma pendência funcional. A busca padrão deve aparecer no cabeçalho, indexar o conteúdo pelo Pagefind, aceitar o atalho do componente e abrir o resultado no capítulo ou seção correspondente. Essa exigência foi explicitada depois da solicitação original e integra o aceite atual.

## Critérios de aceite verificáveis

1. A matriz demonstra cobertura de todos os conceitos e das ocorrências dos 18 grupos, sem substituir explicação por menção. Os quarenta prioritários têm desenvolvimento identificável.
2. A organização Diátaxis é visível nas páginas e na navegação; cada tipo de página tem uma necessidade clara do estudante. Os títulos e ganchos mostram o valor de aprender.
3. Os casos reais apontam ao código e às fontes usados. Os exemplos com números têm consulta/resultado e horário; o blast radius tem nó, snapshot e consumidores discriminados.
4. As histórias de falha distinguem fato verificado, hipótese e proposta. O alcance do histórico examinado está documentado; a intenção de analisar todos os commits não é marcada como satisfeita por censo de metadados.
5. MVC/MVP/MVVM, cache/Redis e o ambiente Rancher/Kubernetes do Airflow estão tratados com exemplos concretos e alternativas delimitadas.
6. Cada item tem uma skill selecionada com evidência primária datada de estrelas e tendência, critério e universo comparado declarados, pelo menos um framework base e pelo menos uma aplicação real open source de referência, com fonte que demonstre o mecanismo e classificação correta. Um exemplo didático ou modelo pode complementar o estudo, mas não satisfaz sozinho a exigência de aplicação real OSS. Eventuais lacunas permanecem pendentes e explícitas; uma URL genérica ou produto proprietário rotulado como OSS não satisfaz esse aceite.
7. Os Mermaid dos exemplos passam em parsing, renderização e revisão semântica contra a fonte. As conexões declaradas preservam o ambiente e a fronteira do efeito.
8. O Nextra compila; links locais e anchors funcionam; as rotas da entrega respondem e os leitores encontram o conteúdo pela navegação.
9. A busca global padrão está visível, o índice cobre as páginas entregues e uma consulta como outbox retorna conteúdo pertinente; clicar no resultado abre a página/seção esperada. O índice é regenerado pelo build.
10. Os despachos, configurações, ondas, reusos e council têm recibos reais. Autores não aprovam o próprio recorte; o resultado da revisão está ligado à versão examinada. Cache só é quantificado quando o runtime expõe a medida.
11. A entrega tem arquivos/fontes, instrução de uso, provas e limitações claras. Quantidades produzidas e aprovação técnica são registradas como evidência, sem reescrever retroativamente o pedido.

## Evidência de entrega já produzida

O recibo local de 14/10/2026 às 20:39 UTC registra 52 MDX, 18 capítulos escolhidos pela organização, 310 conceitos normalizados, quarenta prioritários, seis tutoriais, dois guias e 76 diagramas. Registra também build aprovado, 52 aprovações independentes ligadas aos hashes, zero links locais inválidos e 52 rotas HTTP 200. Essas quantidades são o resultado da execução; o usuário não impôs originalmente 52 páginas, seis tutoriais ou 76 diagramas.

As fontes incluem valores agregados do PostgreSQL e blast radius FazGraph com snapshot/horário, casos de código MakersHub e arquivos/configuração Airflow lidos no ambiente identificado. As referências diferenciam código local, runtime, histórico, exemplos REF e propostas.

O censo de histórico registrou 12.697 commits por metadados e aprofundou diffs selecionados. A análise causal de todos os commits e problemas não foi demonstrada. Essa limitação permanece visível para que a Story não encerre uma intenção maior com uma prova menor.

A busca foi corrigida em 14/10/2026 às 23:18 UTC: Pagefind indexou 52 páginas e 5.465 palavras. No navegador headless, outbox retornou sete páginas e abriu o tutorial; refresh retornou a seção Refresh Ahead e o capítulo de cache. O recibo registra ausência de erros de página.

Prévia local no Mac: http://127.0.0.1:59024. Esse endereço não constitui publicação externa. Repositório-alvo: https://github.com/gutocarollo/architecture-system-eng-expert. Os arquivos desta frente ainda são artefatos locais; o link do repositório não comprova commit, push, merge ou deploy.

## Fontes para reconstituir o pedido e as provas

- O pedido de direção e a emenda do Opus estão em tasks/architecture-course-2026-10-14/original-request.md. A fonte primária continua sendo a conversa do usuário.
- O corpus conceitual original está em docs/catalogos/catalogo-patterns.md, docs/aplicado/aplicacao-makershub-40-patterns.md e docs/referencias/catalogo-40-patterns-skills-frameworks.md; a matriz preserva seus hashes e linhas.
- A cobertura está em tasks/architecture-course-2026-10-14/evidence/coverage.json. Os recibos de dados, código, runtime e curadoria estão na pasta evidence dessa frente.
- A entrega anterior está em tasks/architecture-course-2026-10-14/delivery.json; o aceite independente e os hashes estão em prepared-council/packet.json e reviews/.
- A correção de busca está em tasks/architecture-story-2026-10-14/search/receipt.json, com build, consulta real, navegação e captura do navegador.

## Topologia, arquivos compartilhados e fronteira de escrita

A implementação local já está no worktree perfect-citizen-a30f5998, cujo HEAD observado é 23d5d158d3a964dceba296296368ec14bcd8970b. Esta Story registra uma entrega documental autônoma. O comportamento de produção fornece os casos estudados; as regras e dados desses sistemas são somente consultados.

Os arquivos do curso estão em content/, app/, mdx-components.jsx e next.config.mjs. A busca altera a configuração, package.json/package-lock.json, app/layout.jsx e o índice gerado. Esses são os arquivos compartilhados desta frente; alterações concorrentes precisam preservar os trabalhos existentes. MakersHub, Airflow, Salesforce e os outros sistemas são fontes consultadas nesta entrega documental, sem mutação de suas regras ou dados.

A busca por duplicatas encontrou cards de Central de Ajuda, documentação de telas e cobertura de vídeos, mas não um card equivalente a este currículo de arquitetura. Nenhum desses pais foi copiado para esta Story.

## Pendência de catálogo e de fechamento

O catálogo controlado instalado não registra gutocarollo/architecture-system-eng-expert nem um asset canônico confirmado do curso. A Story deve registrar Catalog Validation Status blocked, com a justificativa e os campos controlados de repositório/assets vazios. As camadas aplicáveis são documentation e frontend. Contextos e capacidades de negócio, páginas MakersHub, labels de página e sistemas operacionais afetados não são inferidos a partir de exemplos somente lidos.

Este registro preserva os objetivos e a entrega observada. A classificação de catálogo pendente e a cobertura causal integral do histórico continuam documentadas; a criação da Story não declara automaticamente todos os critérios cumpridos nem autoriza publicação externa ou alteração de sistemas de produção.
