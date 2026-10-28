"""Prepare concrete product-flow repairs without mutating the frozen selection."""
import copy
import datetime
import hashlib
import json
from pathlib import Path
from evidence_helpers import source

BASE=Path(__file__).resolve().parent
S=source
rows=[]

def add(concept_id, base, application, mechanism, limits, application_kind='PRODUCT_OSS'):
    rows.append(dict(concept_id=concept_id,decision='AUTHOR_SOURCE_MATCH_REPAIR',independent_review='PENDING',
                     application_kind=application_kind,base=base,application=application,
                     mechanism=mechanism,limits=limits,
                     version_scope='Revisões e licenças são individuais e fixadas. Bases comparativas não são apresentadas como dependências sem prova específica.'))

saga_base=[S('temporalio/sdk-java','temporal-sdk/src/main/java/io/temporal/workflow/Saga.java',[
    (87,122,'A base executa compensações registradas, sequencialmente em ordem inversa ou em paralelo segundo a opção.'),(126,133,'A API registra a operação de compensação.')])]
saga_app=[
    S('medusajs/medusa','packages/core/core-flows/src/order/workflows/create-order.ts',[(190,210,'O workflow coordenador prepara região, canal e cliente.'),(412,423,'O coordenador transforma os dados e invoca createOrdersStep.'),(435,460,'Depois da criação, o fluxo consulta o pedido e seus itens.')]),
    S('medusajs/medusa','packages/core/core-flows/src/order/steps/create-orders.ts',[(31,50,'A etapa cria pedidos, guarda os IDs como entrada de compensação e registra a exclusão concreta dos pedidos criados.')]),
    S('medusajs/medusa','packages/core/core-flows/src/cart/steps/find-or-create-customer.ts',[(149,174,'A etapa pode criar um cliente e sua compensação só apaga o cliente que ela própria criou.')]),
    S('medusajs/medusa','packages/core/workflows-sdk/src/utils/composer/create-step.ts',[(174,186,'O composer registra invokeFn e compensateFn e marca noCompensation conforme a presença do callback real.')]),
    S('medusajs/medusa','packages/core/workflows-sdk/src/utils/composer/helpers/create-step-handler.ts',[(91,110,'O handler executa a função de invocação e guarda a resposta.'),(113,143,'O handler de compensação extrai compensateInput da resposta e chama o callback concreto.')]),
    S('medusajs/medusa','packages/core/orchestration/src/transaction/transaction-orchestrator.ts',[(835,861,'Uma falha que não permite continuar coloca o fluxo em espera de compensação.'),(1090,1104,'O orquestrador distingue compensação real de etapa sem callback.'),(1162,1194,'A execução escolhe COMPENSATE ou INVOKE e chama o handler da etapa.')])]
saga_limits='A prova é do fluxo real de criação de pedido e dos efeitos de criação de cliente/pedido que ele registra para desfazer. Não afirma que esse workflow reserva estoque: seu próprio comentário diz que apenas confirma disponibilidade. Compensações podem falhar e não apagam efeitos externos arbitrários. Não há promessa de isolamento global, rollback ACID entre módulos, outbox ou exatamente uma vez. Temporal é uma base comparativa; Medusa usa seu próprio motor.'
add('compensating-transaction',saga_base,saga_app,
    'A etapa de criação de pedidos do Medusa devolve os IDs criados como dado de compensação e registra uma função que chama deleteOrders com esses IDs. Quando o motor muda para compensação, o handler recupera esse dado e executa a função. A exclusão é uma nova ação de negócio que desfaz a criação anterior; não é apresentada como rollback da transação original.',saga_limits)
add('orchestration-saga',saga_base,saga_app,
    'O workflow de criação de pedido do Medusa decide a sequência de etapas e centraliza os dados que cada uma recebe. Ele pode criar um cliente e depois um pedido, e ambas as etapas registram compensações concretas. Quando uma falha não permite prosseguir, o motor passa para compensação e invoca os handlers correspondentes. O coordenador controla o avanço e o retorno desse processo.',saga_limits)
add('saga',saga_base,saga_app,
    'O Medusa compõe operações dos módulos de cliente e pedido em um workflow. Cada etapa conclui sua ação e entrega os dados necessários para uma ação posterior de compensação. Uma falha permanente pode iniciar o caminho que apaga o pedido criado e, se couber, o cliente criado pela própria etapa. Este é o recorte orquestrado de Saga do produto.',saga_limits)

mv_base=[S('postgres/postgres','src/backend/commands/matview.c',[(314,331,'A implementação cria uma relação transitória e materializa nela o resultado da consulta.'),(334,354,'A atualização aplica merge concorrente ou troca o heap persistido.'),(405,449,'O cálculo planeja e executa a consulta, direcionando os resultados ao receptor de tuplas.'),(893,898,'A atualização não concorrente troca o armazenamento e reconstrói índices.')])]
mv_app=[
    S('postgres/postgres','src/backend/tcop/utility.c',[(1679,1698,'O servidor PostgreSQL despacha CREATE TABLE AS e REFRESH MATERIALIZED VIEW para suas implementações reais.')]),
    S('postgres/postgres','src/backend/commands/createas.c',[(270,297,'CREATE MATERIALIZED VIEW cria a relação e usa RefreshMatViewByOid para a carga inicial quando há dados.')]),
    S('postgres/postgres','src/backend/commands/matview.c',[(119,138,'REFRESH adquire o lock da relação e invoca a atualização por OID.'),(319,354,'O servidor preenche o novo heap e o aplica à relação materializada.')]),
    S('postgres/postgres','src/backend/executor/nodeSeqscan.c',[(60,93,'Uma leitura sequencial lê tuplas da relação física por table_beginscan/table_scan_getnextslot, sem executar a consulta de definição a cada tupla.')])]
mv_limits='A aplicação escolhida é o próprio servidor PostgreSQL, um produto OSS de infraestrutura; a base são suas rotinas reutilizáveis de materialização. Os papéis são diferentes dentro do mesmo repositório. Não se afirma que uma aplicação financeira específica implantou esta view, que toda leitura usa SeqScan ou que o valor é atualizado automaticamente. REFRESH tem custo, locks e requisitos adicionais no modo concorrente; WITH NO DATA não produz um resultado consultável preenchido.'
add('materialized-view',mv_base,mv_app,
    'O PostgreSQL implementa uma view que guarda o resultado da consulta em armazenamento próprio. O comando do servidor cria a relação, executa a consulta para preenchê-la e, em um REFRESH posterior, substitui ou reconcilia seus dados. Uma consulta posterior pode ler as tuplas da relação materializada como dados físicos.',mv_limits,'INFRASTRUCTURE_OSS')
add('precomputation',mv_base,mv_app,
    'No servidor PostgreSQL, CREATE ou REFRESH MATERIALIZED VIEW executa a consulta antes das leituras posteriores e guarda o resultado. A fase de cálculo preenche um heap; as consultas seguintes podem ler esse resultado já calculado. O trabalho é deslocado da leitura para a criação ou atualização da representação.',mv_limits+' O ganho de tempo de consulta depende da consulta, dos índices e do custo de atualização; nenhum benchmark foi feito.','INFRASTRUCTURE_OSS')

add('denormalization',mv_base,[
    S('medusajs/medusa','packages/core/core-flows/src/cart/utils/prepare-line-item-data.ts',[(136,165,'A preparação copia título do produto e SKU da variante para campos próprios do item.')]),
    S('medusajs/medusa','packages/core/core-flows/src/order/workflows/create-order.ts',[(38,61,'O workflow prepara cada item com os dados da variante.'),(391,423,'Os itens preparados compõem orderToCreate e são enviados à etapa de criação.'),(435,458,'A leitura posterior do pedido pede items.*.')]),
    S('medusajs/medusa','packages/modules/order/src/models/line-item.ts',[(5,23,'O modelo persistido do item guarda product_id/variant_id e também product_title e variant_sku.')]),
    S('medusajs/medusa','packages/modules/order/src/services/order-module-service.ts',[(806,833,'O serviço cria o pedido e encaminha seus itens ao método de persistência em lote.'),(1138,1166,'O método transacional grava os próprios campos dos itens e seus vínculos com o pedido.')])],
    'Ao montar um pedido, o Medusa copia título do produto e SKU da variante para o item do pedido. O modelo guarda esses valores ao lado dos identificadores originais, e o serviço persiste os itens. Assim, o pedido conserva uma representação própria dos atributos que também existem no catálogo; sua leitura não depende de buscar novamente esses dois atributos no produto.',
    'Este é um snapshot de atributos do pedido, não uma afirmação de que toda a entidade Product foi duplicada ou de que todos os dados são imutáveis. O fallback usa valores explicitamente informados quando presentes. A base PostgreSQL mostra o armazenamento de uma representação calculada em separado, como alternativa comparativa; não é apresentada como implementação da cópia feita pelo Medusa.')

add('mvc',[
    S('rails/rails','actionpack/lib/action_controller/metal/implicit_render.rb',[(35,49,'O controlador encontra o template da ação e o renderiza, com erro definido para um HTML sem template.')]),
    S('rails/rails','actionview/lib/action_view/rendering.rb',[(109,110,'O contexto de view recebe os valores do controlador.'),(127,142,'O renderer resolve o template e devolve seu corpo renderizado.')])],[
    S('redmine/redmine','Gemfile',[(1,7,'O produto fixa Rails 8.1.4, a versão de framework inspecionada.')]),
    S('redmine/redmine','app/controllers/application_controller.rb',[(418,426,'O controlador busca o modelo Issue pelo identificador da rota e verifica visibilidade.')]),
    S('redmine/redmine','app/models/issue.rb',[(20,39,'Issue é um modelo ActiveRecord com relações de domínio de projeto e status.')]),
    S('redmine/redmine','app/controllers/issues_controller.rb',[(20,25,'A ação show executa antes find_issue.'),(102,117,'A ação prepara jornais, relações e status permitidos a partir do modelo.'),(124,137,'A resposta HTML escolhe explicitamente o template issues/show.')]),
    S('redmine/redmine','app/views/issues/show.html.erb',[(3,8,'A view renderiza informações do modelo Issue.'),(48,60,'O HTML usa autor, responsável e assunto da issue.')])],
    'Quando uma pessoa abre uma issue no Redmine, o controlador carrega o modelo Issue, verifica sua visibilidade e prepara os dados da página. A ação HTML manda renderizar issues/show. O template ERB lê assunto, status e pessoas ligadas à issue e produz a página. Rails fornece o contexto e o renderer que ligam controlador e view.',
    'A evidência é o caminho HTML show de issues. A mesma aplicação também expõe formatos API/PDF, que não são usados como prova deste MVC. O mapeamento das responsabilidades é uma leitura do código, sem alegação de que todas as classes do produto seguem MVC puro. A licença Redmine é GPL-2.0-or-later pelo grant de LICENSE.txt, com texto integral em doc/COPYING.')

add('range-sharding',[
    S('vitessio/vitess','go/vt/key/key.go',[(119,123,'KeyRangeContains aplica os limites de intervalo à chave.'),(245,252,'KeyRangeIntersect verifica se dois intervalos têm chaves em comum.')]),
    S('vitessio/vitess','go/vt/key/destination.go',[(167,190,'DestinationKeyRange.Resolve mantém somente shards cujo intervalo intersecta o pedido.'),(216,227,'Uma chave pontual é encaminhada ao shard cujo intervalo a contém.')])],[
    S('vitessio/vitess','go/vt/vtgate/vindexes/numeric.go',[(112,123,'Numeric.RangeMap transforma limites numéricos em um intervalo de keyspace IDs.'),(131,142,'Numeric mantém a ordem dos uint64 usando codificação big-endian e é registrado como vindex numeric.')]),
    S('vitessio/vitess','go/vt/vtgate/engine/routing.go',[(486,496,'O roteador real avalia a seleção between e chama a resolução sequencial.'),(629,643,'O motor chama RangeMap e entrega o intervalo ao resolver de shards.')]),
    S('vitessio/vitess','go/vt/srvtopo/resolver.go',[(248,273,'O resolver obtém os shards e usa destination.Resolve para produzir os destinos concretos.')])],
    'No VTGate do Vitess, o caminho between com vindex sequencial numeric transforma os limites da consulta em um intervalo de keyspace IDs ordenados. O resolver compara esse intervalo com os intervalos dos shards e mantém somente os que se cruzam. Para uma chave pontual, a seleção usa contenção no intervalo do shard.',
    'A prova vale para o vindex numeric/sequencial e para os intervalos do keyspace; não atribui essa propriedade a um vindex hash ou lookup. Os limites abertos e fechados seguem as funções KeyRange do Vitess. Não há claim de balanceamento, ausência de hotspots nem cluster implantado. Base de roteamento e produto VTGate ficam no mesmo repositório com papéis explícitos.','INFRASTRUCTURE_OSS')

add('centralized-logging',[
    S('fluent/fluent-bit','plugins/out_loki/loki.c',[(1941,1945,'O plugin cria um POST HTTP com o lote de logs.'),(1997,2002,'O plugin envia o lote ao endpoint configurado.'),(2167,2186,'O flush transforma os registros da entrada em payload Loki e o envia.'),(2433,2444,'O plugin de saída Loki registra o flush real.')])],[
    S('grafana/loki','pkg/distributor/http.go',[(27,42,'O servidor recebe requisições de logs e resolve o tenant.'),(68,71,'O corpo recebido é parseado para o formato de ingestão.'),(133,144,'O handler entrega os streams ao distribuidor e responde à requisição.')]),
    S('grafana/loki','pkg/distributor/distributor.go',[(958,972,'Streams são atribuídos aos ingesters responsáveis.'),(1661,1676,'O distribuidor monta o PushRequest e envia os logs ao ingester por RPC.')]),
    S('grafana/loki','pkg/ingester/instance.go',[(231,265,'O ingester reúne streams por labels, acrescenta entradas e registra o lote no WAL.')]),
    S('grafana/loki','pkg/ingester/stream.go',[(320,338,'As entradas recebidas são acrescentadas a chunks do stream.')]),
    S('grafana/loki','pkg/querier/querier.go',[(239,275,'A consulta busca dados nos ingesters e no armazenamento de chunks conforme o intervalo de tempo.')])],
    'O Fluent Bit envia lotes de registros pelo plugin Loki. No serviço Loki, o handler recebe os streams de produtores externos, o distribuidor os encaminha aos ingesters e estes os agrupam por tenant e labels, acrescentando entradas aos chunks e ao WAL. O querier oferece o caminho para consultar esse conjunto pelo intervalo solicitado. Esse fluxo demonstra coleta e consulta centralizadas de logs.',
    'O recorte são os componentes OSS de envio, ingestão e consulta. Não é uma observação de agentes instalados nem uma garantia de coleta de todos os logs de uma empresa. Retenção, falhas de rede, limites e configuração do WAL/armazenamento continuam relevantes; a prova não se baseia no logger interno do processo Loki.','INFRASTRUCTURE_OSS')

original=json.loads((BASE.parent/'curation/rare-support/transactions-source-recommendations.json').read_text())
choreography=copy.deepcopy(next(r for r in original['rows'] if r['concept_id']=='choreography-saga'))
choreography.update(concept_id='choreography',decision='AUTHOR_SOURCE_MATCH_REPAIR',independent_review='PENDING',
    mechanism='Duas instâncias Mastodon conduzem o processo de follow por mensagens ActivityPub. A grava seu pedido e envia Follow; B reage ao receber a atividade e responde Accept ou Reject segundo seu estado e suas regras. A reage à resposta atualizando seu próprio estado. O cancelamento é comunicado por Undo e também provoca uma reação local em B. O processo avança pelas reações dos participantes, sem um coordenador global de transação.',
    limits=choreography['limits']+' A base Eventuate fornece dispatch de eventos para handlers como mecanismo comparativo; não é uma dependência declarada do Mastodon. Este recorte prova um processo entre participantes, não apenas publicação local em um bus.')
rows.append(choreography)

add('composite',[
    S('javaparser/javaparser','javaparser-core/src/main/java/com/github/javaparser/ast/Node.java',[(395,403,'A base Node expõe todos os filhos pelo mesmo contrato.'),(462,487,'A associação de pai atualiza a coleção de filhos de forma concreta.'),(1020,1036,'Uma operação percorre recursivamente filhos pelo contrato Node.')])],[
    S('trinodb/trino','core/trino-parser/src/main/java/io/trino/sql/tree/Node.java',[(21,49,'O nó comum define a operação getChildren para os nós da árvore SQL.')]),
    S('trinodb/trino','core/trino-parser/src/main/java/io/trino/sql/tree/LogicalExpression.java',[(42,60,'O nó composto conserva pelo menos duas expressões como filhos.'),(68,82,'A expressão composta expõe seus termos por getChildren.')]),
    S('trinodb/trino','core/trino-parser/src/main/java/io/trino/sql/tree/Identifier.java',[(94,98,'O nó folha implementa o mesmo getChildren devolvendo uma lista vazia.')])],
    'Na árvore SQL do Trino, tanto a folha Identifier quanto a expressão composta LogicalExpression são nós e expõem getChildren. A folha devolve uma lista vazia, enquanto o composto conserva e devolve suas expressões filhas. Isso permite percorrer a árvore pelo mesmo contrato sem exigir que o consumidor trate toda folha como uma estrutura diferente. O JavaParser mostra uma base reutilizável que mantém os vínculos e realiza uma operação recursiva.',
    'O recorte é a estrutura da AST. Visitor pode complementar essa árvore, mas não é usado sozinho como prova de Composite. JavaParser é uma base comparativa, não uma dependência declarada do Trino. Foi escolhida a alternativa Apache-2.0 que o grant dual do JavaParser permite.','INFRASTRUCTURE_OSS')

add('domain-policy',[
    S('j-easy/easy-rules','easy-rules-core/src/main/java/org/jeasy/rules/core/DefaultRulesEngine.java',[(86,115,'Uma regra avalia os fatos e sua decisão controla a execução da ação.'),(160,178,'A API check devolve a decisão booleana de cada regra sobre os fatos.')])],[
    S('killbill/killbill','invoice/src/main/java/org/killbill/billing/invoice/generator/DefaultInvoiceGenerator.java',[(74,94,'A geração de fatura recebe a data alvo e chama a política antes de criar a fatura.'),(120,125,'A política rejeita uma data alvo que excede o número de meses futuros permitido pela configuração do tenant.')]),
    S('killbill/killbill','invoice/src/main/java/org/killbill/billing/invoice/InvoiceDispatcher.java',[(952,969,'O dispatcher real invoca o gerador de fatura com eventos, histórico e data alvo.')])],
    'O Kill Bill aplica uma política de faturamento antes de gerar a fatura: a data alvo não pode ficar além do número de meses futuros permitido para aquele tenant. A função compara a data alvo com o dia UTC do relógio e com a configuração; se o limite for excedido, lança o erro de domínio INVOICE_TARGET_DATE_TOO_FAR_IN_THE_FUTURE e impede a criação da fatura. O dispatcher chama esse gerador no fluxo real.',
    'A política demonstrada é esse limite de data, não uma descrição de toda a entidade ou de toda validação. O Easy Rules oferece uma base comparativa de regra que avalia fatos e controla uma ação; não se afirma que o Kill Bill usa essa biblioteca. Nenhuma decisão financeira real de cliente foi executada.')

nifi='nifi-framework-bundle/nifi-framework/'
add('pipeline',[S('apache/camel','core/camel-core-processor/src/main/java/org/apache/camel/processor/Pipeline.java',[(89,118,'O pipeline executa o próximo processador, leva o resultado à próxima entrada e encerra quando para, falha ou não há próximo estágio.')])],[
    S('apache/nifi',nifi+'nifi-framework-components/src/main/java/org/apache/nifi/connectable/StandardConnection.java',[(235,252,'A conexão conserva uma origem, um destino e sua fila de FlowFiles.')]),
    S('apache/nifi',nifi+'nifi-framework-components/src/main/java/org/apache/nifi/controller/repository/StandardProcessSession.java',[(2095,2113,'O estágio obtém o próximo FlowFile de uma conexão de entrada.'),(2564,2584,'transfer marca a relação de saída escolhida para o FlowFile.'),(358,387,'A sessão resolve a relação em uma conexão e seleciona sua fila de destino.'),(650,669,'No commit, os registros são realmente inseridos nas filas das próximas conexões.')]),
    S('apache/nifi',nifi+'nifi-framework-core/src/main/java/org/apache/nifi/controller/tasks/ConnectableTask.java',[(147,155,'O agendador verifica entradas e saídas de um estágio conectado.'),(198,210,'A execução depende de trabalho e da disponibilidade das relações, incluindo backpressure.'),(249,280,'O agendador chama onTrigger do próximo componente e repete segundo trabalho e pressão.')])],
    'No NiFi, uma conexão liga a saída de um componente à fila de entrada de outro. Um estágio retira um FlowFile, o transforma e marca sua relação de saída com transfer. Ao concluir a sessão, o produto resolve a conexão dessa relação e enfileira o resultado. O agendador pode então chamar o componente seguinte, respeitando trabalho disponível e backpressure. Essa cadeia de execução é o pipeline, e não apenas um processador isolado.',
    'A topologia concreta é configurada pelos fluxos do usuário; o recorte prova o motor real que executa a cadeia, sem inventar uma pipeline financeira implantada. Ramificações, filas, retries e fronteiras de sessão continuam existindo. Camel é uma base comparativa de encadeamento e não uma dependência atribuída ao NiFi.','INFRASTRUCTURE_OSS')

add('recreate-deployment',[
    S('kubernetes/kubernetes','pkg/controller/deployment/recreate.go',[(28,64,'O controlador reduz os ReplicaSets antigos, espera não haver pods antigos e só depois cria/escala o novo ReplicaSet.')])],[
    S('prometheus-community/helm-charts','charts/prometheus/values.yaml',[(470,472,'O chart do Prometheus escolhe concretamente strategy.type Recreate.'),(635,639,'O modo StatefulSet está desligado por padrão.'),(666,670,'O modo DaemonSet também está desligado por padrão.')]),
    S('prometheus-community/helm-charts','charts/prometheus/templates/deploy.yaml',[(1,24,'Com os padrões selecionados, o recurso emitido é um Deployment.'),(52,57,'O template aplica server.strategy e remove rollingUpdate quando o tipo é Recreate.'),(179,184,'O container implantado é a imagem de servidor Prometheus selecionada pelo chart.')])],
    'O chart mantido pela comunidade Prometheus escolhe Recreate para o Deployment do servidor por padrão. Seu template emite essa estratégia e elimina a configuração de rolling update. No controlador Kubernetes, o caminho correspondente primeiro escala as versões antigas para baixo, espera que não haja pods antigos em execução e só depois sobe a nova versão.',
    'A aplicação é a configuração pública do servidor Prometheus, não uma inferência de um campo configurável do Airflow. O comportamento vale para o modo Deployment e para esses valores; opções StatefulSet/DaemonSet seguem outros caminhos. A leitura não comprova um rollout executado nem disponibilidade contínua: Recreate pode deixar um intervalo sem servidor.','INFRASTRUCTURE_OSS')

add('rest',[
    S('encode/django-rest-framework','rest_framework/routers.py',[(93,125,'O router separa URI de coleção e de recurso e mapeia os verbos às operações de cada uma.')]),
    S('encode/django-rest-framework','rest_framework/viewsets.py',[(102,124,'A view liga o verbo da requisição ao método da operação e despacha a chamada.')])],[
    S('zulip/zulip','zproject/urls.py',[(415,427,'A coleção messages aceita GET/POST; messages/<message_id> aceita GET/PATCH/DELETE com handlers distintos.')]),
    S('zulip/zulip','zerver/lib/rest.py',[(52,63,'O dispatcher escolhe a função correspondente ao método HTTP.'),(85,110,'HEAD/OPTIONS e a seleção do método têm comportamento explícito.'),(211,224,'O dispatcher chama o handler e rest_path registra a URI com seu mapa de métodos.')])],
    'Na API do Zulip, messages é a coleção de mensagens: GET lista e POST envia uma mensagem. A URI que contém message_id representa uma mensagem específica e aceita leitura, alteração parcial e exclusão por GET, PATCH e DELETE. O dispatcher seleciona o handler pelo método da requisição. O Django REST Framework mostra uma base comparativa que oferece o mesmo tipo de mapeamento entre recursos e verbos.',
    'A classificação é uma API HTTP orientada a recursos no recorte de mensagens. Não certifica todos os níveis de maturidade REST, HATEOAS nem a pureza de todos os endpoints do produto. Zulip usa seu próprio dispatcher Django, não os ViewSets do DRF. O POST de envio pode ter efeitos de entrega e não recebe uma promessa de idempotência por esta referência.')

packet=dict(schema_version=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            frozen_matrix_sha256='a4b12f6c6aa8b1883d8f6c1ac7ed1c7f81d829859422f5a0212f7fd1cca6689e',
            purpose='Quinze reparos autorais de fluxos de produto; sem aprovação independente.',rows=rows,
            independent_review='PENDING',frozen_files_mutated=False)
assert len(rows)==15
path=BASE/'product-flow-recommendations.json';path.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(rows=len(rows),sha256=hashlib.sha256(path.read_bytes()).hexdigest())))
