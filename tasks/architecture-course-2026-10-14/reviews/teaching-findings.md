# Revisão independente da experiência de aprendizagem

ADVERSARIAL-VERIFICATION: SATISFEITO
GAPS-CRITICOS: 0
PROXIMA-ACAO: vincular os recibos por documento ao packet final. TH1 foi fechado no único recheck aquecido; o histórico e o backlog mantêm seus limites.

Esta é a primeira leitura independente de `/root/council_teaching_sol`, despachado como `default`, `gpt-6.1-sol`, esforço `xhigh`, contexto novo e `fork_turns=none`. O reviewer não escreveu as páginas. Foram aplicadas as skills `adversarial-review`, `diataxis-documentation` e o contrato `council-and-authoring.md`. Este relatório não aprova hashes intermediários. O arquivo de prioritários ainda estava em curadoria, e a raiz informou que os hashes de integração seriam atualizados.

## Escopo e composição

Reutilizei o pedido literal, os três catálogos originais, as evidências S1/S2, L1A/L1C, L2A/L2B/L2C, o bootstrap, a consulta agregada e a curadoria GitHub. O catálogo original já distingue aplicações REF de produtos; os exemplos propostos do documento aplicado oferecem ganchos válidos, sem provar produção. As aulas locais reutilizam os contratos e as falhas dessas fontes, com seu limite sintético explícito.

Li os 22 documentos atribuídos: a entrada do curso; a entrada das explicações e os capítulos de regras, fronteiras e GoF; a entrada dos tutoriais e as seis aulas; a entrada dos guias e o guia de impacto; as quatro páginas de referência; a entrada do catálogo e os grupos 01, 10 e 17. A leitura abrange 66 entradas desses três grupos, além da tabela dos 40 prioritários. Não constitui aprovação semântica das entradas das lanes técnicas.

Também conferi semanticamente os 21 diagramas desta lane: sete de fronteiras, quatro de regras, três de GoF, seis das aulas e um do guia. Os diagramas que mostram alternativas têm rótulo de proposta; os das aulas descrevem as simulações em memória. O fluxo observado de Seguros conserva cache, serviço, repositório, SQL e propagação de erro. A verificação semântica não substitui os recibos de sintaxe e renderização nem cobre pixels do site.

## TH1 — Algumas referências não demonstram o conceito que a entrada promete (achado inicial, fechado no recheck)

- Severidade: ALTA.
- Classe: PLANO/ESCOPO e FONTE/OSS.
- Veredito: REAL.
- Contrato: `original-request.md` exige pelo menos uma base e uma aplicação OSS por item. Um exemplo didático é aceitável quando implementa o mecanismo e recebe o rótulo REF. Uma referência de contraste, que o próprio texto diz não demonstrar o conceito, deixa essa parte do pedido pendente.
- Evidência: no grupo DDD, `Shared Kernel` aponta `ValueObject.cs` apenas para contrastar uma base genérica com um modelo compartilhado. `Customer/Supplier`, `Conformist`, `Open Host Service` e `Separate Ways` declaram que a relação ou implementação intencional não foi verificada. O ADR de módulos de MyMeetings acrescentado nessas entradas continua rotulado como contraste. Em Blackboard, a base permanece descrita apenas como “Base REST e grafo de conhecimento”.
- Impacto: o estudante encontra a definição, mas não consegue abrir uma implementação ou declaração concreta do item para comparar a definição com a prática. A honestidade da lacuna evita uma alegação falsa; ela não completa a referência solicitada.
- Correção: reutilizar fontes primárias de modelagem ou documentação do próprio projeto que declarem as relações organizacionais, com caminho e trecho pertinente. Para Blackboard, identificar a base e o mecanismo no projeto citado. Nenhuma biblioteca precisa ser apresentada como criadora de um acordo humano. Preservar os limites e não substituir ausência de prova por classificação automática.

Recibos da leitura:

- [2026-10-14 19:10 UTC] Worktree do curso, `content/referencia/catalogo/10-ddd-domain-driven-design.mdx` — leitura Python das linhas 113, 119, 127, 135 e 153 → “apenas para contrastar base técnica e conceito de domínio”; “nenhuma implementação de relação organizacional foi verificada nesta lane”; “nenhuma relação entre equipes foi verificada”; “esta lane não verificou que ela seja deliberadamente um serviço para vários contextos”; “nenhuma implementação intencional foi verificada nesta lane”. SHA-256: `ab3e0077ea8a8f17264b02a769f484109af0c1dac5078ed43ef6d1e387dcece6`.
- [2026-10-14 19:10 UTC] Worktree do curso, `content/referencia/catalogo/01-arquiteturas-de-aplicacao.mdx` — leitura Python da linha 209 → “Base REST e grafo de conhecimento”. SHA-256: `4b6007be434159bef5b4162399e25da259ac12f2cf9031723e4646090e5ee0f1`.

FIX-REQUEST:
- gap: TH1, aplicação ou declaração OSS pertinente ausente nas cinco entradas DDD citadas e base genérica de Blackboard.
- evidencia: o pedido literal e os trechos acima.
- alteracao-obrigatoria: publicar fontes pertinentes com prova do mecanismo ou da relação, ou manter a entrega como parcial nesse requisito.

## Limite original do estudo do histórico

O pedido solicita que agentes analisem todos os commits e problemas para explicar por que ocorreram. A evidência L2B registra um censo de 12.697 commits por metadados e três diffs aprofundados. A própria linha 9 informa que a classificação é heurística e não é leitura de diff nem diagnóstico causal. A página de evidências preserva corretamente a diferença entre inventário e aprofundamento.

Essa parte do objetivo original permanece parcial. Não foi encontrada emenda que substitua a análise de todos os problemas pelo censo. O fechamento precisa dizer que houve inventário completo das referências locais observadas e estudo causal delimitado de três patches. Não se pode afirmar auditoria semântica de 12.697 commits nem confirmação de incidentes ou resultados em produção. Este registro não solicita uma nova leitura ampla nesta fase nem interfere na aceitação de páginas que respeitam seu próprio escopo.

## Pontos refutados e limites verificados

As seis aulas oferecem pré-requisitos, código completo, comandos, saída esperada, repetição e resultado observável. As simulações de Outbox e concorrência declaram a ausência de armazenamento durável e atomicidade SQL. O laboratório de single-flight usa eventos e relógio controlado; o cancelamento de um leitor fica separado da tarefa compartilhada. O relatório L1C contém as saídas previamente executadas. Não executei produção nem repeti as aulas nesta revisão.

As páginas de arquitetura evitam classificar o MakersHub inteiro como MVC, MVP, MVVM, DDD ou Hexagonal apenas pela estrutura de pastas. As três alternativas de apresentação usam a mesma escolha Manual/Automático e conservam a ação quando o modo já está ativo. Os três casos históricos dizem que os commits não são ancestrais do HEAD local estudado e limitam a prova ao patch.

Os números da entrada e do guia de impacto correspondem ao recibo `postgres-inflow.json`: 557.731 linhas e chaves distintas, 3.380 movimentos em outubro e soma assinada de 18.742.122,16. A conta de consumidores indiretos conserva 424 − 322 = 102 cards e 27 − 3 = 24 endpoints. Os textos não confundem esses agregados com receita, mês fechado, atividade de todos os consumidores ou atraso comprovado. Essa comparação é contra o recibo datado; não é uma nova medição do banco.

Conferi em disco os seis hashes de API, serviço e repositório de Seguros e relatórios: os seis correspondiam ao packet preparado. O método de relatórios chama sua porta de leitura; a rota de Seguros instancia o serviço com o repositório, utiliza `ttl=300` e converte exceção em HTTP 500. Esses fatos são do checkout local, sem inferência de implantação.

- [2026-10-14 19:07 UTC] `/Users/augustocarollo/Developer/makershub` — comparação SHA-256 dos seis arquivos com os IDs `report-api`, `report-service`, `report-repository`, `insurance-api`, `insurance-service`, `insurance-repository` do packet → `match=True` para os seis.
- [2026-10-14 19:07 UTC] MakersHub, `backend/app/api/v1/insurance.py` — `nl -ba`, linhas 63–73 → `repo = InsuranceRepository(session)`, `service = InsuranceService(repo)`, `ttl=300`, `status_code=500`.
- [2026-10-14 19:07 UTC] MakersHub, `backend/app/services/report_read_service.py` — `codegraph explore` → linha 41: `result = await self._repository.read(request)`.

## Backlog editorial

Os links com nomes de skills levam repetidamente à página geral de curadoria. A página lista packs e papéis, mas nem sempre oferece um localizador direto da skill nomeada. Acrescentar um mapa com nome, arquivo local ou URL pública pertinente melhoraria a consulta e preservaria a diferença entre pack e skill. Isto é MEDIA, não reabre conteúdo já aceito e não exige novo reviewer.

O diagrama didático de Bridge mostra a operação e dois fornecedores, mas não ilustra duas variantes da operação. O texto preserva a condição de haver duas dimensões que variam. Um segundo tipo de operação tornaria essa diferença mais visível; isto é MEDIA editorial e pode seguir para backlog.

## Curadoria ainda aberta e gate final

A versão intermediária de `prioritarios.mdx` ainda trazia Refresh Ahead apenas como wiki Caffeine, Backpressure como wiki RxJava, API Gateway como rota de documentação e State Machine como exemplo na documentação XState. Refresh Ahead admite não ter encontrado uma aplicação consumidora. Registrei esses pontos à raiz para a curadoria ativa; não emiti finding contra uma versão final que ainda não existe.

O primeiro sinal de ausência de aplicação Space-Based foi refutado pela releitura: a versão atual já aponta `CacheAffinityExample.java` do Apache Ignite e delimita o sample como REF. Ele não deve continuar no conjunto de achados abertos por causa do snapshot anterior.

O packet preparado ainda divergia de vários hashes de índices e páginas integradas. Isso coincide com a atualização pendente informada pela raiz; não constitui acusação de recibo falso. Aguardo `FINAL_PACKET`, a conclusão da curadoria e o delta de TH1. Somente então os recibos por documento podem fixar o conteúdo realmente examinado.

PLACAR: 1 achado alto real de referências; 1 limite original de objetivo; 2 melhorias editoriais em backlog; nenhum recibo de aprovação emitido.
PROXIMO PASSO: o autor corrige TH1, a raiz conclui a curadoria e atualiza o packet; o recheck usa este mesmo reviewer e somente o delta material.

## Recheck aquecido de TH1 — 14/10/2026 às 19:50 UTC

O único recheck de TH1 examinou o delta `evidence/s2-reference-repair.md` e as oito entradas reparadas, sem reler corpos que permaneceram iguais. Recuperei as dezoito fontes primárias em URLs fixadas por commit; todas responderam HTTP 200 e os dezoito SHA-256 integrais coincidiram com o relatório do autor. Os corpos brutos, as URLs, os hashes e os horários desta conferência estão em `reviews/teaching-recheck-sources.json`.

A base de modelagem CML distingue papéis, direção de influência e estado pretendido. Os mapas acrescentados declaram a relação SK do núcleo semântico, a relação C/S da seguradora fictícia, a aceitação CF e os três consumidores de PrintingContext com OHS. Esses arquivos sustentam uma referência de modelo declarado; os textos deixam explícito que não comprovam acordos humanos nem execução de serviços de produção. Essa interpretação coincide com a [documentação primária de Context Mapper](https://contextmapper.org/docs/context-map/).

DcaShop declara Separate Ways no documento de domínio e no comentário de BackofficeContext. O catálogo preserva que Backoffice lê infraestrutura operacional compartilhada e que a declaração trata a relação entre modelos. A classificação não foi inferida somente da ausência de imports. O arquivo de verificações referencia DomainCentric.ArchRules.Xunit e o teste gera o mapa a partir de declarações; não executei esse teste.

Blackboard agora identifica Play 2.5.10 e Neo4j 3.2.1. O controller obtém KGraph, passa a fonte escolhida a KnowledgeSource, chama KSource.execute e ChemblKSource acrescenta nós e relações ao grafo recebido. O limite de controle solicitado por HTTP, em um projeto legado, conserva a diferença para um scheduler autônomo. JDT oferece registro da view e implementação de ViewPart/createPartControl; a [documentação Equinox](https://equinox.eclipseprojects.io/) identifica a base OSGi. NiFi oferece três processadores, duas conexões e os métodos que atualizam atributos e transferem FlowFiles. Essas referências mostram mecanismo e aplicação concreta.

- [2026-10-14 19:50:00–19:50:01 UTC] GitHub público, dezoito URLs brutas fixadas no relatório S2 — `urllib.request.urlopen` e comparação SHA-256 do corpo integral → `sources=18`, HTTP `200` e `hash_matches=True` em todos os dezoito registros.
- [2026-10-14 19:51 UTC] Worktree do curso — SHA-256 dos catálogos reparados → G01 `94fbb6133740e753c78c8e48fe0a463fc59d6de767529c2410a3ce0566b0e44a`; G10 `c0a23012114f5d9169959853498fb2148b5116c5d928e4d1e635c2f190932633`.

TH1 está fechado nesses hashes. As versões substituídas continuam acima somente como registro do achado inicial. Não resta achado alto aberto na lane didática. O limite original do histórico continua válido; fechar TH1 não transforma o censo em análise causal de todos os diffs.

### Curadoria de prioritários e semântica dos diagramas

As referências documentais intermediárias dos itens 15, 19, 21 e 40 foram substituídas. Recuperei oito arquivos primários em commits fixados e li os mecanismos pertinentes. Trino configura recarga assíncrona condicionada ao intervalo e ao executor; Superset oferece tarefa de warm-up e documenta sua relação com o TTL. NiFi possui condições de fila cheia; APISIX contém roteamento, execução de plugins e upstream; o exemplo Stately Sketch cria uma máquina, um actor e liga a execução à interface. O último permanece REF executável, sem alegação de consumidor de produção. Os corpos e hashes independentes estão em `reviews/teaching-priority-sources.json`.

Dois ajustes de fonte foram enviados à raiz como MEDIA, sem nova rodada: Trino importa `com.google.common.cache.CacheLoader`, portanto sua semântica deve apontar para Guava ou distinguir Caffeine como alternativa. No NiFi, `isBackPressureEngaged` das linhas 165–172 verifica self-loops; a interrupção do lote está em 263–264 e o gate geral de destinos em 206–210. O recorte publicado deve conservar essa distinção. Eles não reabrem TH1 nem exigem novo reviewer.

O delta de TH1 não mudou os vinte e um diagramas lidos na primeira passagem. Comparei seus SHA-256 com as fontes do packet preparado e os vinte e um corresponderam. `reviews/teaching-semantic-observations.json` vincula cada observação semântica ao ID e ao hash da fence. Esse arquivo registra a semântica examinada, sem substituir sintaxe, renderização ou o recibo por documento.

PLACAR DO RECHECK: TH1 fechado; zero achados altos abertos nesta lane; limite do histórico preservado; melhorias MEDIA ficam em backlog ou correção mecânica da raiz. A emissão dos vinte e dois recibos ainda depende do aviso `FINAL_PACKET`.

## Vinculação final — 14/10/2026 às 20:26:59 UTC

A raiz entregou `FINAL_PACKET` com SHA-256 `2735ced3d2249a581cedd3aef2c099e1a690ef85f96fc69b623cc8d8f8f3190a`. Foram emitidos vinte e dois recibos APPROVED dos documentos desta lane, sem editar o packet. Cada recibo usa o despacho real `collaboration.followup_task:/root/council_teaching_sol:final-bind-existing-TH1-review`, o reviewer `/root/council_teaching_sol`, o hash atual do documento e o digest calculado por `review-context` com as evidências examinadas. As duas relações de Seguros e as duas de relatórios incluem todas as pontas de prova, somente nos documentos que as declaram.

Esta operação fixa a primeira leitura e o único recheck de TH1; não representa uma nova rodada semântica. As linhas finais 15/19 da tabela preservam as correções de Guava e do gate de destinos NiFi. As fontes finalizadas das linhas 23/24 foram conferidas contra o recibo S6: oito corpos em commits fixados responderam HTTP 200 e seus hashes integrais coincidiram. Next.js conserva a precedência das páginas locais sobre o fallback, e as cinco migrações GitLab citam a mesma `bulk_import_entities.source_xid`. O snapshot dessa conferência está em `reviews/teaching-final-priority-sources.json`.

- [2026-10-14 20:26:59 UTC] Worktree do curso — `docs_workflow.py review-context` por documento, validação `Draft202012Validator` dos recibos e comparação de hashes, evidências e relações → `receipts=22 schema=PASS document_hashes=PASS evidence_bindings=PASS relation_bindings=PASS receipt_hashes=PASS`.

O manifesto `reviews/teaching-receipts-index.json` lista os vinte e dois paths relativos e seus hashes. Seu SHA-256 é `dea3fd858bf2e952065341088d0d6af30377ac1aad206a79c1d82dd7799a1c6e`. O packet conservou o hash informado pela raiz durante a emissão. TH1 segue fechado; o limite histórico e as melhorias editoriais anteriormente registradas seguem válidos. A conclusão do gate global pertence à raiz e depende das demais lanes.
