# S2 — arquitetura de aplicação, organização, DDD e GoF

Este pacote planeja material de estudo com três fluxos observados no MakersHub. Ele distingue o código do checkout, três mudanças históricas e propostas didáticas. Não houve alteração no MakersHub, execução de teste, consulta de dados de clientes ou verificação de produção.

## Escopo e recibos

- [2026-10-14 16:03 UTC] worktree do curso — `Path.cwd().resolve(); git branch --show-current; git rev-parse HEAD` → `/Users/augustocarollo/.superset.noindex/worktrees/architecture-engineer-expert/perfect-citizen-a30f5998`, `perfect-citizen-a30f5998`, `23d5d158d3a964dceba296296368ec14bcd8970b`.
- [2026-10-14 16:03 UTC] `/Users/augustocarollo/Developer/makershub` — `git branch --show-current; git rev-parse HEAD` → `main`, `e233fb046ec333982cd1547171b0f0bd8d8d92ee`. `Path.resolve()` → `/Users/augustocarollo/Developer.noindex/makershub`.
- [2026-10-14 15:59 UTC] MakersHub, os 21 caminhos dos três fluxos e das duas referências citadas — `git diff --stat -- <paths>` → saída vazia. A igualdade é com o checkout local; não indica atualização em relação ao remoto.
- [2026-10-14 16:03 UTC] histórico local MakersHub — `git rev-list --all --count` → `12686`; `git rev-parse --is-shallow-repository` → `false`.
- [2026-10-14 16:03 UTC] histórico local MakersHub — `git merge-base --is-ancestor <SHA> HEAD` → exit code `1` para `8206752f9b1bc8650d0a4572f4a0d64566260b83`, `7101d3a4babe95081b0b41d35ec305c08bf8a577` e `a55d4d4a004511106ecc23354de0abf23f7d6ddb`. Os três casos históricos pertencem a outras referências locais.

CodeGraph foi a primeira ferramenta de localização dos três fluxos. Suas respostas declararam releitura do código no disco. As relações do índice orientaram a investigação; as chamadas e linhas foram confrontadas com os arquivos. O diretório `docs/architecture/` não existe nesse checkout; `docs/index.md:26` aponta para o corpus aninhado `docs/docs/architecture/`. O guia específico usado foi `docs/reference/SUPER_R1_ARCHITECTURE.md`, que declara snapshot `b9703e18` e drift conhecido na abertura. Seu desenho antigo não serve como topologia atual.

## Composição antes de colisão

Podemos reutilizar o catálogo de 18 grupos em `docs/catalogos/catalogo-patterns.md`, os exemplos propostos explicitamente identificados em `docs/aplicado/aplicacao-makershub-40-patterns.md:1`, e as referências já curadas. A seção de organização desse último arquivo explica monólito modular, hexagonal e fatias verticais; o curso acrescentará provas, alternativas e exercícios. O contrato frontend existente, `MakersHub/docs/reference/DATA_FETCHING_GUIDE.md:1`, descreve componente, hook, DataManager e API, com orientação sobre consumidores compartilhados em `:213`.

A colisão principal é temporal: o checkout local não contém os três fixes escolhidos. Outra colisão é conceitual: ter arquivos chamados `service` e `repository` prova separação local, mas não prova DDD, Clean Architecture ou monólito modular. Hooks com estado também não comprovam MVVM integral. O catálogo deve conservar a identificação de proposta e remover qualquer implicação de que os 40 padrões já foram implementados. As estrelas do corpus não foram medidas nesta lane.

## Três fluxos com fonte no checkout

Os caminhos abaixo são relativos a `/Users/augustocarollo/Developer/makershub` e correspondem ao SHA local acima. As tabelas são referências SQL do código; valores, cardinalidade e execução não foram medidos nesta lane.

| Caso | Caminho observado e fonte |
|---|---|
| O SDR agenda pelo Super R1. | `frontend/app/(pages)/super-r1/[lead_id]/page.tsx:145` instancia `useQualify`; `:507` chama `mutateAsync`. `_hooks/useLeads.ts:330` chama `qualifyLead` e invalida cinco famílias de consulta em `:340`. `_data/DataManager.ts:1210` serializa o pedido e usa `fetch` diretamente para `POST /api/v1/super-r1/qualify`. `backend/app/api/v1/super_r1.py:405`, `post_qualify`, chama `run_qualify` em `:422`. `backend/app/services/qualify_service.py:2030` seleciona o fluxo; o ramo D+1 `_qualify_regular_d1`, em `:1630`, instancia `RoutingRepository` e `RoutingService` em `:1667`, e persiste a intenção em `:1723`. `backend/app/repositories/routing_repo.py:719`, `insert_pending_d1_routing`, monta o `INSERT` na tabela obtida por `_pending_d1_table` em `:765` e executa-o em `:781`. O mesmo caso usa integração Salesforce; esse caminho não passa pelo ApiClient compartilhado. |
| O operador abre os leads de Call Sprint. | `frontend/app/(pages)/call-sprint/page.tsx:307` chama `useCallList`; `_hooks/useCallList.ts:32` usa React Query e `getCallList`. `_data/DataManager.ts:198` converte a aba em tipo de contato, monta filtros e chama `apiClient.get` em `:226`. `frontend/app/_data/ApiClient.tsx:392` delega a `fetch` em `:399`. `backend/app/api/v1/call_list.py:58`, `get_contacts`, limita o escopo em `:87` e chama o serviço em `:95`. `backend/app/services/call_list_service.py:135`, `get_contacts`, chama `self.repo.get_callable_leads` em `:229`. `backend/app/repositories/call_list_repo.py:140` monta a consulta em `:211`, agrega `makershub.fct_salesforce__call` em `:233`, lê `salesforce_prod.stg_salesforce__lead` e executa dados e contagem em `:283` e `:287`. |
| O gestor abre os indicadores de Seguros. | `frontend/app/(pages)/insurance/page.tsx:46` chama `useAllInsuranceData`; `_hooks/useInsurance.ts:248` cria uma chave por dois períodos e chama o DataManager em `:256`. `_data/InsuranceDataManager.tsx:406` agrega 11 chamadas em `Promise.all`; `getKPIMetrics`, em `:238`, chama `/api/v1/insurance/kpi-metrics`. `ApiClient.tsx:399` faz o HTTP. `backend/app/api/v1/insurance.py:46` consulta o cache, instancia `InsuranceRepository` e `InsuranceService` em `:63`, e grava cache com TTL de 300 segundos em `:67`. `backend/app/services/insurance_service.py:19` delega ao repositório. `backend/app/repositories/insurance_repo.py:74` constrói filtro de `issue_date`, consulta `makershub.rpt_insurance__policy` em `:90` e executa em `:99`. |

Metadados medidos às 15:59 UTC: `qualify_service.py` tem mtime `2026-09-15T03:35:20.078850+00:00` e SHA-256 prefixo `7fd3f57455162898`; `call_list_repo.py`, `2026-09-04T03:53:42.387906+00:00`, `748f1970c6bbd45c`; `insurance_repo.py`, `2026-09-04T03:53:42.392785+00:00`, `a44cb58867bf60f4`. Esses metadados vinculam a leitura ao disco local.

## Classificação e comparação

Seguros e a consulta de Call Sprint fornecem exemplos de camadas e objetos de acesso a dados. `InsuranceService.get_kpi_metrics` é delegação direta; seu nome não comprova domínio rico. Super R1 fornece um serviço de aplicação e dispatcher com dependência concreta de FastAPI, SQLAlchemy, repositórios e Salesforce. A extração de portas de negócio seria uma proposta de arquitetura hexagonal, não a classificação do código inteiro.

`useCallLifecycle` expõe estado e ações em `frontend/app/(pages)/call-sprint/_hooks/useCallLifecycle.ts:76`, com implementação em `:139`. A página principal instancia-o em `page.tsx:111`; a janela instancia-o em `window/page.tsx:86`. É um exemplo observável de reutilização de lógica de apresentação. Há `useState`, refs e efeitos; a evidência não comprova objetos de estado do GoF ou uma máquina declarativa XState.

O exercício deve comparar o mesmo seletor Manual/Automático em três alternativas. MVC mostra a requisição controlada e a separação do modelo; MVP usa uma view passiva que encaminha a escolha ao presenter; MVVM usa um modelo de apresentação com `mode` e `selectMode`, observado pela view. Recomendo a terceira como proposta didática para o frontend React porque preserva o fluxo de estado e ações já encontrado no hook e permite discutir sincronização entre duas views. Seu custo é um contrato e sincronização adicionais; para um componente simples, estado local pode ser suficiente. Nenhuma dessas três versões será atribuída ao checkout sem prova.

GoF será ensinado com distinção entre forma e intenção. `backend/app/utils/performance.py:62` envolve a função com medição e preserva seu contrato por `wraps`; é um decorator funcional comparável ao Decorator clássico. `getAllInsuranceData:406` fornece uma fachada de consultas. `get_call_list_service`, em `backend/app/api/v1/call_list.py:43`, é uma fábrica simples por DI, sem comprovar Factory Method por subclasses. Os ramos de qualificação permitem propor Strategy; não há prova de interface de estratégias intercambiáveis nesse recorte.

## Inventário completo dos metadados locais e três diffs

Foi percorrido `git log --all -z --format=%H%x09%cI%x09%P%x09%s`, sem copiar e-mails ou nomes de clientes. O inventário abrange todos os commits alcançáveis pelas 926 referências locais: 12.686 commits, dos quais 895 têm mais de um pai. Não inclui refs remotas que nunca foram buscadas. Os extremos de data de commit são `2025-08-20T17:27:36-03:00` e `2026-10-14T12:48:39-03:00`.

| Mês da data do commit | Quantidade |
|---|---:|
| 2025-08 | 78 |
| 2025-09 | 142 |
| 2025-10 | 191 |
| 2025-11 | 101 |
| 2025-12 | 172 |
| 2026-01 | 140 |
| 2026-02 | 156 |
| 2026-03 | 187 |
| 2026-04 | 192 |
| 2026-05 | 345 |
| 2026-06 | 804 |
| 2026-07 | 298 |
| 2026-08 | 2.489 |
| 2026-09 | 3.983 |
| 2026-10 | 3.408 |

1. **Super R1, `8206752f9b1bc8650d0a4572f4a0d64566260b83`, FBI-4719.** O pai de `qualify_service.py:2185` distinguia Account de Lead e enviava os demais IDs para `_fetch_lead`. No commit, `:2902` usa `classify_record_id`; `:2903` abre o ramo Opportunity e a autorização por objeto. `:659` entrega `existing_opportunity` ao pacote de execução; `:2050` recusa uma Opportunity no fluxo D+1. O diff do arquivo tem 951 linhas acrescentadas e 139 removidas; o commit completo contém 70 arquivos. A história didática é a entrada por uma entidade já existente e a necessidade de manter sua identidade em todas as etapas. O diff prova a mudança, mas não mede duplicações anteriores nem garante deploy.
2. **Seguros, `7101d3a4babe95081b0b41d35ec305c08bf8a577`, FBI-4840.** `InsuranceProposalsAnalysisCard.tsx` usava `new Date(dateStr)` e formatação local. O diff passa a chamar `formatBrDate`; `frontend/app/_utils/isoDate.ts` recebe 30 linhas que distinguem a string inteira `YYYY-MM-DD` de timestamp e usam `parseIsoLocal` para a primeira. A história registrada no commit usa a emissão `2026-10-05`, mostrada como dia 04 em UTC−3. Ela ensina a diferença entre uma data de calendário e um instante; não transforma automaticamente o helper em Value Object DDD. O inventário mostra um teste adicionado; ele não foi executado nesta lane.
3. **Call Sprint, `a55d4d4a004511106ecc23354de0abf23f7d6ddb`, FBI-4714.** `CallSprintWindowView.tsx`, hunk `@@ -136,8 +136,8 @@`, substitui um botão que sempre chamava `toggleAutoMode` por dois botões. Cada um chama o toggle somente se o modo atual difere da escolha. São quatro linhas acrescentadas e quatro removidas no componente. A história ensina comando explícito: clicar no modo já ativo deve preservá-lo. O benefício de MVP/MVVM seria manter essa regra no contrato de apresentação, em vez de reproduzi-la em cada view. Não foi medida paridade visual.

## Plano de capítulos

1. **Organizar o código que muda junto.** O capítulo começa na consulta de Seguros, contrasta camadas e fatias verticais, depois explica fronteiras de módulo e portas. A pergunta é quantos contratos um aluno precisa compreender para alterar uma emissão. Os itens prioritários aprofundados são 1, 2, 3 e 4; cada um terá benefício, custo, limite, diagrama, referência OSS e skill.
2. **Separar apresentação, estado e regra.** O mesmo seletor de Call Sprint recebe versões didáticas MVC, MVP e MVVM, com um diagrama de dependências e um diagrama de sequência por alternativa. O caso histórico de escolha ativa fornece o critério de comportamento. A proposta preserva o modelo React e evita uma migração artificial de framework.
3. **Modelar o negócio antes das classes.** Super R1 fornece Lead, Account, Opportunity, assessor e reunião como ponto de partida, mas o mapa de contextos será proposto. Um exercício explica por que o `OwnerId` externo não se torna automaticamente a identidade interna do assessor. S2 cobre 21 conceitos do grupo DDD: Bounded Context, Ubiquitous Language, Entity, Value Object, Aggregate, Aggregate Root, Domain Service, Application Service, Repository, Factory, Domain Event, Domain Policy, Specification, Anti-Corruption Layer, Context Map, Shared Kernel, Customer/Supplier, Conformist, Open Host Service, Published Language e Separate Ways. Agregados e fronteiras transacionais dependem da lane de consistência; não serão inferidos da pasta.
4. **Comparar arquiteturas.** A referência conservará os 22 itens do grupo 1: Layered/N-Tier, Modular Monolith, Microservices, SOA, Serverless, Microkernel/Plugin, Hexagonal, Clean, Onion, Vertical Slice, MVC, MVP, MVVM, PAC, Component-Based, Space-Based, Cell-Based, Actor Model, Peer-to-Peer, Blackboard, Pipe and Filter e Event-Driven. Uma matriz compara unidade de mudança, implantação, dependência, falha e custo. Cada item recebe um exemplo explicitamente classificado como observado, histórico ou proposto.
5. **Compor objetos e funções.** A referência cobrirá os 23 GoF, agrupados em cinco de criação, sete estruturais e onze comportamentais. A explicação aprofunda Decorator, Facade, Adapter, Strategy, Command, Observer e State com os três casos; os restantes ganham exemplo e limite, sem forçar sua presença no MakersHub.
6. **Aprender com um diff.** O tutorial conduz o estudante do comportamento antes ao contrato depois dos três commits, sem executar integrações. Os SHAs e a ausência de ancestralidade ficam visíveis. O estudante compara o efeito real do patch com o rótulo arquitetural, sem usar o assunto do commit como prova de causa.

Os exercícios usam código e comentários em inglês e dados sintéticos identificados. MDX ainda não foi escrito. A passagem para tabelas/valores reais exige FazGraph antes de PostgreSQL e pertence às lanes designadas pela raiz.

## Referências e limites

Context7 foi tentado para React e FastAPI; ambas as chamadas responderam literalmente `Monthly quota reached`. A orientação conceitual foi conferida em fontes primárias públicas, em 2026-10-14: [React: custom hooks](https://react.dev/learn/reusing-logic-with-custom-hooks), [FastAPI: bigger applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/), [Fowler: GUI Architectures](https://martinfowler.com/eaaDev/uiArchs.html), [Fowler: Presentation Model](https://martinfowler.com/eaaDev/PresentationModel.html), [Fowler: Bounded Context](https://martinfowler.com/bliki/BoundedContext.html), [Microsoft: common web architectures](https://learn.microsoft.com/en-us/dotnet/architecture/modern-web-apps-azure/common-web-application-architectures), e [DDD by Examples: Library](https://github.com/ddd-by-examples/library). O manifest local declara Next `16.3.4`, React `^19.2.8`, React Query `^5.101.4` e FastAPI `0.141.1`; a documentação pública acessada é corrente e não constitui auditoria exata dessas versões.

## Três tarefas para os auxiliares Luna, sem despacho nesta lane

- **Luna código:** produzir recortes pequenos dos três fluxos no SHA escolhido pela raiz e um desenho Mermaid por fluxo; conferir chamadas e todos os consumidores de `useCallLifecycle`; separar estado local, estado remoto e regra de negócio. Ownership proposto: anexo de evidência de código, sem escrita no MakersHub.
- **Luna histórico:** confirmar pais, hunk, arquivos e alcançabilidade dos três SHAs; escrever três histórias curtas com entrada, antes, depois e limite da prova. Substituir o caso de 70 arquivos por um commit menor somente se preservar a mesma regra observada. Ownership proposto: anexo histórico, sem cherry-pick ou testes.
- **Luna referências:** verificar fontes primárias e maturidade dos exemplos OSS já curados; entregar uma matriz dos 22 estilos, 21 conceitos DDD e 23 GoF com fonte, limite e sugestão de exercício. Conferir MVC/MVP/MVVM e a diferença entre Factory simples, Factory Method e Abstract Factory. Ownership proposto: anexo de referências; não usar estrelas históricas como atuais.

Memória consultada apenas para orientar a cautela: `MEMORY.md:1310-1320` registrava revisão de Super R1 sem conclusão capturada. Nenhum estado vivo acima deriva dela.
