"""Connect each canonical concept to a bounded, executable financial observation."""
import importlib.util
import json
import re
import shlex
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
LEARNING=ROOT/'tasks/FBI-4991-arquitetura-nextra/execution/learning'
financial_contracts=json.loads((ROOT/'labs/architecture/financial_contracts.json').read_text())['probes']
object_contracts=json.loads((ROOT/'labs/architecture/object_contracts.json').read_text())['concepts']
coverage=json.loads((ROOT/'tasks/architecture-course-2026-10-14/evidence/coverage.json').read_text())
registry=json.loads((LEARNING/'families.json').read_text())
OWNED_CASE_IDS={'single-flight-cancel','early-refresh','date-only','opportunity-entry','order-boundaries','order-delivery','reservation','consensus','queue-workflow','cache-policy','ledger-projection','storage-partitions','safe-release','access-policy','diagnostics'}
bycase={c['case_id']:c for c in registry['families'] if c['case_id'] in OWNED_CASE_IDS}
receipts=json.loads((LEARNING/'receipts.json').read_text())
byreceipt={r['case_id']:r for r in receipts['receipts']}
entry_by_concept={}
for entry in coverage['catalog_entries']:
    if entry['group']==18:continue
    for concept in entry['concept_ids']:entry_by_concept.setdefault(concept,entry)

DEFAULTS={1:('order-boundaries','provider-contract'),2:('order-delivery','deduplicate'),3:('queue-workflow','route-enrich-aggregate'),4:('ledger-projection','projection-checkpoint'),5:('storage-partitions','shard-route'),6:('cache-policy','cache-expiry'),7:('queue-workflow','retry-budget'),8:('reservation','version-conflict'),9:('order-boundaries','provider-contract'),10:('order-boundaries','validate-before-side-effect'),11:('safe-release','expand-contract'),12:('safe-release','progressive-route'),13:('consensus','majority-partition'),14:('access-policy','object-authorization'),15:('diagnostics','correlate-retries'),16:('queue-workflow','dag-dependencies'),17:('order-boundaries','object-patterns')}
OVERRIDES={}
def assign(case,probe,names):
    for name in names.split('|'):OVERRIDES[name]=(case,probe)
assign('single-flight-cancel','historical-cancellation','Single Flight|Cache Stampede Protection|Async/Await|Futures/Promises|Mutex')
assign('early-refresh','historical-refresh','Refresh Ahead')
assign('date-only','historical-date','Value Object|Published Language')
assign('opportunity-entry','historical-identity','Idempotency Key|Domain Policy|Entity')
assign('order-delivery','deduplicate','Idempotency|Deduplication|Transactional Inbox|At-Least-Once Delivery|At-Most-Once Delivery|Exactly Once Semantics')
assign('order-delivery','commit-intention','Transactional Outbox|Outbox + CDC|Change Data Capture (CDC)|Dual Write|Dual Write Migration')
assign('order-delivery','compensate','Saga|Orchestration Saga|Choreography Saga|Compensating Transaction|TCC — Try/Confirm/Cancel')
assign('reservation','version-conflict','Compare-and-Swap / CAS|Optimistic Concurrency Control|Copy-on-Write|Immutable Data|Pessimistic Locking|Lock-Free|Wait-Free|Reader/Writer Lock|Spinlock|Single Writer Principle')
assign('reservation','fence','Distributed Lock|Lease|Fencing Token|Fencing')
assign('reservation','resource-key','Reservation Pattern|Semaphore|Actor Model')
assign('consensus','majority-partition','Consensus|Raft|Paxos|Leader Election|Quorum|Split-Brain Prevention|Automatic Failover|Failover|Active/Active|Active/Passive|Leader/Follower|Multi-Leader|Multi-Primary|Primary/Replica|Hot Standby|Warm Standby|Cold Standby|Multi-AZ|Multi-Region|Stateless Services|Cell-Based Architecture|Peer-to-Peer|Gossip Protocol|Self-Healing|Watchdog|Heartbeat')
assign('consensus','quorum-overlap','Quorum Read/Write|Strong Consistency|Synchronous Replication|Asynchronous Replication|Cascading Replication|Replication|Read Replica')
assign('consensus','causal-versions','Version Vector|Eventual Consistency|Monotonic Reads|Read-your-writes')
assign('consensus','logical-clock','Lamport Clock|Hybrid Logical Clock')
assign('consensus','prepared-participant','Two-Phase Commit / 2PC|Three-Phase Commit / 3PC')
assign('queue-workflow','retry-dlq','Retry|Retry Queue|Dead Letter Queue|Poison Message Handling|Delayed Queue|Priority Queue')
assign('queue-workflow','admission','Backpressure|Rate Limiting|Throttling|Load Shedding|Bulkhead|Reactive Streams|Worker Pool|Thread Pool|Work Stealing')
assign('queue-workflow','consumer-topology','Competing Consumers|Producer/Consumer|Message Queue|Job Queue|Publish/Subscribe|Fan-out|Fan-in|Event Notification|Event-Carried State Transfer|Event Streaming|Fire-and-Forget|Observer')
assign('queue-workflow','resequence-state','Resequencer|Finite State Machine|State Machine|State')
assign('queue-workflow','retry-budget','Exponential Backoff|Jitter|Circuit Breaker|Timeout|Deadline Propagation|Fail Fast|Fallback|Graceful Degradation|Chaos Engineering')
assign('queue-workflow','dag-dependencies','DAG|Workflow Engine|Orchestrator|Choreography|Batch Processing|Stream Processing|MapReduce|Fork/Join|Scatter/Gather|Pipeline|Pipe and Filter|Lambda Architecture|Kappa Architecture')
assign('cache-policy','cache-key','Cache Aside|Distributed Cache|Negative Caching')
assign('cache-policy','cache-expiry','TTL Cache|Read Through|Cache Warming')
assign('cache-policy','write-policy','Write Behind / Write Back|Write Through')
assign('cache-policy','cache-levels','Local Cache|Two-Level Cache|Cache Invalidation|Space-Based Architecture')
assign('ledger-projection','replay-events','Append-Only Log|Event Sourcing|Domain Event|Write Model|Command Handler')
assign('ledger-projection','projection-checkpoint','CQRS|Materialized View|Projection|Read Model|Query Handler|Integration Event|Denormalization|Precomputation')
assign('ledger-projection','snapshot-replay','Snapshotting|Memento')
assign('ledger-projection','durable-transaction','Write-Ahead Log (WAL)|Log Structured Storage|Write Amplification Control')
assign('storage-partitions','shard-route','Sharding|Range Sharding|Hash Sharding|Geographic Sharding|Directory-Based Sharding|Horizontal Partitioning|Vertical Partitioning')
assign('storage-partitions','hash-remap','Consistent Hashing')
assign('storage-partitions','covering-index','Indexing|Covering Index')
assign('safe-release','expand-contract','Expand/Contract|Branch by Abstraction|Modularization|Service Extraction|Database Decomposition|Strangler Fig|CDC Migration|Transitional Architecture')
assign('safe-release','shadow-parity','Shadow Traffic|Shadow Deployment|Dark Launch|Parallel Run|A/B Deployment')
assign('safe-release','progressive-route','Feature Flags|Canary Release|Progressive Delivery|Blue/Green Deployment|Rolling Deployment|Recreate Deployment')
assign('safe-release','desired-state','GitOps|Immutable Infrastructure|Infrastructure as Code')
assign('access-policy','credential-boundary','OAuth2|OIDC|mTLS|Service-to-Service Identity|Short-Lived Credentials|Token Exchange|Zero Trust')
assign('access-policy','rotate-key','Secrets Rotation')
assign('access-policy','least-network-path','Bastion Host|Network Segmentation|Defense in Depth|Service Mesh|Sidecar|Ambassador|Reverse Proxy|Gateway Offloading')
assign('access-policy','object-authorization','RBAC|ABAC|ReBAC|Policy-Based Access Control|Least Privilege|API Gateway Security')
assign('diagnostics','correlate-retries','Correlation ID|Request ID|Distributed Tracing|OpenTelemetry|Structured Logging|Centralized Logging')
assign('diagnostics','measure-signals','Metrics|Golden Signals|RED Method (Rate, Errors, Duration)|USE Method (Utilization, Saturation, Errors)')
assign('diagnostics','probe-business-path','Health Check|Synthetic Monitoring')
# Object patterns own their exact local mechanics even when another group also mentions them.
object_names={'Abstract Factory','Adapter','Bridge','Builder','Chain of Responsibility','Command','Composite','Decorator','Facade','Factory Method','Flyweight','Interpreter','Iterator','Mediator','Memento','Observer','Prototype','Proxy','Singleton','State','Strategy','Template Method','Visitor'}
for name in object_names:OVERRIDES[name]=('order-boundaries','object-patterns')

DIRECT={'Idempotency','Deduplication','Transactional Inbox','Transactional Outbox','Compensating Transaction','Compare-and-Swap / CAS','Optimistic Concurrency Control','Fencing Token','Reservation Pattern','Quorum Read/Write','Version Vector','Lamport Clock','Content-Based Router','Message Enricher','Message Filter','Message Translator','Splitter','Aggregator','Dead Letter Queue','Poison Message Handling','Backpressure','Resequencer','DAG','Cache Invalidation','TTL Cache','Cache Aside','Local Cache','Two-Level Cache','Write Through','Write Behind / Write Back','Projection','Read Model','Query Handler','Snapshotting','Indexing','Covering Index','Expand/Contract','Shadow Traffic','RBAC','ABAC','ReBAC','Correlation ID','Request ID','Single Flight','Refresh Ahead',*object_names}

# This describes the specific measured principle, rather than a complete protocol claim.
ACTIONS={
'provider-contract':'Compare o status externo AUTHORISED com o status accepted que a ordem aceita. Depois acompanhe a conversão de 10.000 centavos em R$ 100.',
'replace-policy':'Troque a função de taxa mantendo a operação da ordem e compare as taxas calculadas.',
'validate-before-side-effect':'Envie a ordem negativa e compare a escrita anterior com a coleção que permanece vazia após a validação.',
'deduplicate':'Entregue ORDER-1 duas vezes e ORDER-2 uma vez. Confira por que três entregas devem produzir dois efeitos e somar R$ 150.',
'commit-intention':'Interrompa o modelo entre salvar e publicar. Compare a ordem isolada com a ordem e a intenção que a mesma transação SQLite conserva.',
'compensate':'Observe a alocação falhar depois do débito de R$ 100 e acompanhe o crédito que recompõe os R$ 1.000.',
'version-conflict':'Compare a escrita baseada na versão 7 com a versão 8 já gravada. Releia e refaça 1.100 − 200 = R$ 900.',
'fence':'Faça a geração 101 voltar depois da 102 e confira a rejeição no destino, em vez de confiar somente na expiração do coordenador.',
'resource-key':'Envie dois operadores para o mesmo assessor e horário; compare a identidade do usuário com a identidade do recurso disputado.',
'majority-partition':'Separe A/B de C e conte quais grupos conseguem reunir dois dos três votos; observe o preço de recusar a escrita da minoria.',
'quorum-overlap':'Calcule 2 + 2 − 3 = 1 membro comum e compare com duas decisões que consultam somente um membro.',
'causal-versions':'Compare os vetores A:1/B:0 e A:0/B:1 antes de escolher um vencedor; acompanhe a detecção de concorrência.',
'logical-clock':'Receba o evento de clock 8 no participante de clock 3 e confira por que o próximo clock precisa ser 9.',
'prepared-participant':'Interrompa a comunicação após prepare e examine por que um participante não pode inventar commit ao vencer um tempo local.',
'route-enrich-aggregate':'Roteie seis entradas pelo tipo, acrescente a conta sintética e reúna as contagens; separe os mecanismos que alteram conteúdo daqueles que alteram destino.',
'retry-dlq':'Acompanhe a mensagem poison até a terceira tentativa e confira sua retirada da fila normal sem perder o item válido.',
'admission':'Ofereça 120 solicitações a uma capacidade de 20 e confira os 100 itens recusados antes de ocuparem o buffer.',
'consumer-topology':'Compare executar toda a lista em cada worker com atribuir cada identidade uma vez e publicar também para a assinatura de auditoria.',
'resequence-state':'Receba settled antes de reserved e accepted, reconstrua a ordem conhecida e confira cada transição permitida.',
'retry-budget':'Observe as esperas 1, 2 e 4, o jitter fixo e a abertura do circuito após três falhas; diferencie tempo de espera, admissão e isolamento.',
'dag-dependencies':'Tente publicar antes da transformação e acompanhe o escalonamento extract, transform e publish pelas dependências.',
'cache-key':'Faça A e B consultarem position e confira quais componentes da chave impedem compartilhar o recorte errado.',
'cache-expiry':'Avance de um valor com vencimento 10 para o instante 11 e examine qual decisão volta ao produtor.',
'write-policy':'Aplique o crédito de R$ 100 e interrompa a memória; compare o valor durável quando a confirmação exige ou não a escrita.',
'cache-levels':'Compare as cópias locais 1 e 2, invalide a cópia antiga e acompanhe a recarga pelo dono compartilhado do modelo.',
'replay-events':'Reproduza os fatos 1.000, +100 e −200 e conserve R$ 900 com a história que permite refazer a conta.',
'projection-checkpoint':'Observe dois eventos de atraso e avance o modelo de consulta de R$ 1.000 para R$ 900.',
'durable-transaction':'Execute UPDATE e rollback em SQLite com journal_mode=wal e confira o valor recuperado de 100.000 centavos.',
'snapshot-replay':'Recomece do snapshot do evento 2 e aplique só o débito restante, chegando aos mesmos R$ 900.',
'shard-route':'Encontre a chave 7 pela regra de propriedade e compare uma partição consultada com a varredura das três.',
'hash-remap':'Acrescente um quarto shard ao módulo anterior e conte as chaves remapeadas; use esse custo para comparar uma alternativa de hashing consistente.',
'covering-index':'Leia o EXPLAIN QUERY PLAN SQLite antes e depois do índice que contém account_key e cents.',
'expand-contract':'Leia amount com o consumidor antigo depois da mudança e compare a remoção imediata com a convivência de amount e amount_cents.',
'progressive-route':'Roteie cinco das cem requisições para a versão nova e examine qual população recebe a mudança e o que desviar tráfego não desfaz.',
'shadow-parity':'Calcule a mesma entrada nas duas funções puras, preserve o resultado primário e detecte a diferença 10/1.000.',
'desired-state':'Compare image/replicas declarados com o estado anterior e acompanhe a reconciliação do modelo.',
'object-authorization':'Avalie advisor/A/SYNTHETIC-1 contra o objeto B/SYNTHETIC-2 e identifique qual relação o papel sozinho deixou de conferir.',
'credential-boundary':'Avalie a audience position-api na API order-api e o vencimento 10 no instante 11; separe a decisão de política da prova criptográfica ausente.',
'rotate-key':'Retire old do conjunto aceito e repita a verificação do mesmo key_id, explicitando a assinatura que o modelo não executa.',
'least-network-path':'Tente o caminho browser→ledger e compare-o com as duas ligações explicitamente permitidas.',
'correlate-retries':'Reúna REQUEST-1 e REQUEST-2 sob ORDER-1 e confira três spans sem confundir tentativa e operação.',
'measure-signals':'Conte três entradas, um erro e a duração máxima 800 ms; diga qual sinal revela o trecho do provedor.',
'probe-business-path':'Compare health ok com a prova sintética da ordem que detecta provider_failed.',
'historical-cancellation':'Cancele um dos cinco leitores nas duas classes históricas e compare cinco cancelamentos com um cancelamento e quatro resultados.',
'historical-refresh':'Leia em 0,6, libere a renovação e repita em 1,05. Compare a espera anterior com a resposta renovada sem espera.',
'historical-date':'Formate 2026-10-05 e 2026-10-05T00:00:00Z em São Paulo. Conserve o dia civil e a conversão do instante.',
'historical-identity':'Use dois atores e duas chaves contra a mesma OPP aberta; observe criação 1→0 e o segundo claim recusado com 409.',
'object-patterns':'Execute a operação de objetos identificada pelo nome do conceito e compare seu estado ou resultado anterior e posterior.'}

OBJECT_ACTIONS={
'Abstract Factory':'Compare um validador básico misturado à taxa premium com a família premium que cria os dois contratos juntos. A ordem de 2.000 muda de recusada para aceita sem trocar sua taxa de 10.',
'Adapter':'Leia 10.000 centavos no provedor e observe o valor local de 100 que o consumidor consegue usar.',
'Bridge':'Combine os avisos standard e premium com os transportes memory e paper. Confira quatro entregas usando duas hierarquias independentes e sem criar uma subclasse para cada combinação.',
'Builder':'Mude o campo amount pelo passo nomeado de construção e confira o objeto final com valor 250.',
'Chain of Responsibility':'Passe a ordem de 2.000 pelos validadores de valor positivo e de limite 1.000. Confira qual responsabilidade interrompe a aceitação.',
'Command':'Guarde o crédito de 50 como uma operação executável e aplique-o depois ao valor 100, chegando a 150.',
'Composite':'Reúna uma ordem de 100 e um grupo com ordens de 50 e 25. O mesmo método de totalização percorre os grupos e soma 175.',
'Decorator':'Envolva a taxa original de 1 com um adicional de 2 e confira 3 sem mudar a classe da ordem.',
'Facade':'Use uma entrada para reunir a validação e a taxa, recebendo accepted e fee na mesma resposta.',
'Factory Method':'Compare o método de criação do criador básico com a sobrescrita do criador premium; confira as classes concretas devolvidas.',
'Flyweight':'Crie cinco referências ao mesmo símbolo e compare cinco identidades independentes com uma identidade compartilhada. O valor de cada ordem continua sendo próprio.',
'Interpreter':'Avalie a gramática pequena amount maior que 100 no contexto amount=250, sem executar uma string como código.',
'Iterator':'Percorra as ordens de 100 e 50 pelo gerador e confira os dois valores sem acessar a indexação interna da coleção.',
'Mediator':'Envie um evento ao coordenador e observe as duas notificações que ele encaminha para auditoria e risco.',
'Memento':'Guarde o estado local com amount=100, altere para 200 e restaure a cópia preservada. Diferencie restauração local de estorno financeiro.',
'Observer':'Registre um assinante, publique ORDER-1 e confira uma notificação recebida pelo callback.',
'Prototype':'Copie o objeto-base e acrescente premium à lista da cópia; confira que a lista do original permanece vazia.',
'Proxy':'Interponha a decisão de permissão antes da consulta da ordem. A chamada sem permissão recebe denied em vez de 100.',
'Singleton':'Compare duas instâncias independentes com duas consultas ao mesmo nome do registro local. Só a segunda condição conserva uma identidade no escopo deste processo.',
'State':'Aceite a ordem uma vez e tente a transição novamente. O comportamento do estado accepted recusa a segunda aceitação.',
'Strategy':'Mantenha a operação e a entrada 100, troque a função de taxa de 1% para 2% e confira 1 e 2.',
'Template Method':'Conserve a sequência normalizar e calcular taxa; a subclasse premium muda somente o passo da taxa e o resultado passa de 101 para 100,5.',
'Visitor':'Faça a ordem premium aceitar o visitante de taxa. A chamada escolhe visit_premium_order sem acrescentar essa operação ao fluxo que percorre as ordens.'}

decisions=json.loads((ROOT/'labs/architecture/mapping_decisions.json').read_text())
RELEVANT={}
for decision in decisions['observations']:
    for name in decision['names'].split('|'):
        if name in RELEVANT:raise RuntimeError('duplicate adjudication: '+name)
        RELEVANT[name]=decision
        if decision.get('action'):ACTIONS[decision['probe']]=decision['action']
for name in object_names:
    RELEVANT[name]={'case':'order-boundaries','probe':'object-patterns','basis':OBJECT_ACTIONS[name]}
NEW_ACTIONS={
'cache-aside':'Faça três leituras da posição. Observe o primeiro miss carregar e preencher a chave; os dois hits seguintes conservam uma única consulta à fonte.',
'negative-cache':'Consulte uma chave inexistente três vezes e compare três consultas à fonte com uma consulta e uma ausência explicitamente armazenada.',
'cache-warming':'Preencha a chave antes da primeira consulta e confira que essa consulta não precisa buscar o valor na fonte.',
'read-through':'Use somente cache.read nas três chamadas; acompanhe a API do cache invocando seu loader uma vez e guardando a resposta.',
'message-filter':'Envie os valores 100, −20 e 50. Observe a retirada da entrada negativa e confira duas mensagens válidas, que somam 150.',
'message-splitter':'Envie um envelope com duas ordens; confira duas mensagens individuais, soma 150 e preservação de BATCH-1 em ambas.',
'message-translation':'Traduza order_ref e amount_cents do provedor para order_id e amount do consumidor, conservando 10.000 centavos como R$ 100 e AUTHORISED como accepted.',
'ab-cohorts':'Distribua quatro usuários entre A e B; confira que os dois grupos recebem respostas visíveis diferentes e mantêm sua associação ao usuário.',
'gossip-membership':'Troque conjuntos de membros entre A/B e B/C por duas rodadas; confira que os três participantes conhecem A, B e C sem contar votos.',
'stateless-request':'Autentique a sessão fictícia na primeira instância e roteie a próxima consulta para a segunda. Compare o estado local ausente com a sessão obtida de seu dono compartilhado.',
'replica-lag':'Atualize o primário para a versão 2, observe a réplica na versão 1 e aplique a atualização para que ela também chegue à versão 2.',
'session-read-version':'Exija a versão 2 já observada pela sessão. Recuse a réplica na versão 1 e escolha o dono que consegue responder sem regredir.',
'priority-queue':'Insira standard, urgent e low nessa ordem; acompanhe o heap selecionando urgent, standard e low pelas prioridades.',
'delayed-queue':'Tente despachar no relógio 3 uma tarefa que só pode sair no relógio 5. Confira a espera e o instante de elegibilidade.',
'demand-backpressure':'Ofereça seis tarefas e deixe o produtor avançar somente quando existir vaga. Confira seis conclusões, nenhuma recusa e buffer máximo de duas.',
'rate-window':'Ofereça três chamadas no segundo 0 e uma no segundo 1. Com limite de duas por segundo, confira três admissões e uma recusa.',
' timeout-boundary':'Aguarde um evento asyncio que nunca é liberado e confira que o prazo encerra a espera com TimeoutError.',
'deadline-budget':'No instante 2, propague o deadline 5 do pai. Confira que o filho recebe somente três unidades, em vez de abrir um prazo novo de dez.',
'subscription-fanout':'Publique dois eventos para auditoria e risco. Confira dois eventos em cada assinatura e quatro entregas totais, sem dividir os eventos entre as assinaturas.',
'event-payload':'Compare a notificação que contém só o ID com o evento que carrega amount e status. Conte uma consulta à fonte no primeiro caso e zero no segundo.',
'consistent-ring':'Adicione o nó D ao anel com pontos virtuais e conte as chaves cujo próximo dono muda. Compare com o remapeamento do módulo de três para quatro shards.',
'cqrs-handlers':'Execute o comando de crédito pelo command handler. Leia a projeção separada pelo query handler antes e depois de consumir o evento; confira sua versão e seu contrato de consulta.',
'value-object':'Construa dois valores monetários iguais em instâncias distintas, recuse um valor negativo e tente alterar o objeto congelado.',
' transactional-inbox':'Entregue ORDER-1 duas vezes e ORDER-2 uma vez. A transação que une inbox e débito deve conservar duas linhas, dois efeitos e R$ 150.'}
NEW_ACTIONS['timeout-boundary']=NEW_ACTIONS.pop(' timeout-boundary')
NEW_ACTIONS['transactional-inbox']=NEW_ACTIONS.pop(' transactional-inbox')
ACTIONS.update(NEW_ACTIONS)

raw=[]
for concept in coverage['concepts']:
    entry=entry_by_concept.get(concept['concept_id'])
    if entry is None and concept['canonical_name']=='DDD':
        entry={'entry_id':'g10-introduction','group':10,'original_detail':'DDD organiza a linguagem e as regras do domínio segundo os limites do negócio.'}
    if entry is None:raise RuntimeError('concept without corpus occurrence')
    group=entry['group'];name=concept['canonical_name']
    decision=RELEVANT.get(name)
    case_id,probe=(decision['case'],decision['probe']) if decision else OVERRIDES.get(name,DEFAULTS[group])
    case=bycase[case_id]
    ref=ROOT/next(g['reference_path'] for g in coverage['groups'] if g['group']==group)
    text=ref.read_text();anchor=entry['entry_id']
    part=text.split(f'<span id="{anchor}" />',1)
    if len(part)==2:
        body=part[1].split('<span id=',1)[0]
        paragraphs=[p.strip() for p in re.split(r'\n\s*\n',body) if p.strip() and not p.strip().startswith('#')]
        meaning=paragraphs[0] if paragraphs else name
    else:
        chunks=re.split(r'(?m)^## +',text)
        wanted={name,entry.get('original_label',''),*concept.get('aliases',[])}
        matched=next((chunk.split('\n',1)[1] for chunk in chunks[1:] if chunk.split('\n',1)[0].strip() in wanted),None)
        if matched:
            paragraphs=[p.strip() for p in re.split(r'\n\s*\n',matched) if p.strip() and not p.strip().startswith('#')]
            meaning=paragraphs[0] if paragraphs else entry.get('original_detail') or name
        else:
            meaning=entry.get('original_detail') or name
    meaning=re.sub(r'\[([^]]+)\]\([^)]*\)',r'\1',meaning)
    meaning=re.sub(r'<[^>]*>','',meaning)
    meaning=re.split(r'(?<=\.)\s+',meaning)[0].replace('\n',' ')
    level='LOCAL_MECHANISM' if name in DIRECT else 'EXECUTABLE_PRINCIPLE_COMPARISON'
    if case_id in ['date-only','opportunity-entry']:
        level='HISTORICAL_SEMANTIC_TRANSFER'
    if decision is None:level='PENDING_SPECIFIC_PRACTICE'
    if probe=='object-patterns':command='python3 labs/architecture/object_patterns.py --concept '+shlex.quote(name)
    elif probe.startswith('historical-'):command=case['command']
    else:command=case['command']+' --probe '+probe
    limits=case['limit']
    if level=='EXECUTABLE_PRINCIPLE_COMPARISON':
        limits=f'O probe exercita um requisito ou um contraexemplo relacionado a {name}; não implementa o padrão completo. '+limits
    elif level=='HISTORICAL_SEMANTIC_TRANSFER':
        limits=f'O código histórico permite estudar {name} por transferência semântica; ele não foi classificado como uma implementação integral de DDD. '+limits
    if decision is None:
        command=None
    row=dict(concept_id=concept['concept_id'],canonical_name=name,corpus_entry_id=anchor,groups=concept['groups'],case_id=case_id,
             mechanism=meaning,exercise_action=(OBJECT_ACTIONS[name] if probe=='object-patterns' else ACTIONS[probe]) if decision else 'A prática específica deste conceito ainda está pendente. O exercício base desta família não demonstra esse mecanismo.',probe=probe,command=command,coverage_level=level,
             destinations={**case['destinations'],'concept':f'/jornadas/{case_id}/conceitos/#{concept["concept_id"]}'},
             original_explanation='/'+concept['explanation_path'].removeprefix('content/').removesuffix('index.mdx').removesuffix('.mdx').rstrip('/')+'/',
             original_reference='/'+str(ref.relative_to(ROOT)).removeprefix('content/').removesuffix('.mdx')+('/#'+anchor if len(part)==2 else '/'),
             limit=decision.get('scope_limit',limits) if decision else limits,execution_receipt='tasks/FBI-4991-arquitetura-nextra/execution/learning/receipts.json',
             historical_gate='SOURCE_PR_JIRA_EVIDENCE_PRESENT_REVIEW_PENDING' if case['corrected_sha'] else 'NOT_APPLICABLE_HYPOTHETICAL',
             independent_review='PENDING',specific_pattern_implementation_gap=level=='EXECUTABLE_PRINCIPLE_COMPARISON',
             learning_status='RELEVANT_BOUNDED_OBSERVATION' if decision else 'PENDING_SPECIFIC_PRACTICE',
             observation_source_file=('labs/architecture/object_patterns.py' if probe=='object-patterns' else ('labs/architecture/'+case_id+('/run.mjs' if case_id=='date-only' else '/run.py')) if probe.startswith('historical-') else decision.get('source_file','labs/architecture/financial.py')) if decision else None,
             adjudication_basis=decision['basis'] if decision else 'The actual probe does not execute the mechanism stated in the concept definition; its old unrelated command has been removed.',
             required_observation=None if decision else decisions['pending_examples'].get(name,'Construct a before/after financial scenario that specifically exercises '+name+': '+meaning))
    raw.append(row)

assert len(raw)==len({x['concept_id'] for x in raw})==310
matrix=dict(schema_version=1,scope='310 concepts individually adjudicated; only relevant bounded observations carry an executable command, and missing specific practices remain PENDING',
            concepts=raw,priority_entries=[dict(priority_id=p['priority_id'],concept_ids=p['concept_ids'],destinations=[next(x['destinations']['concept'] for x in raw if x['concept_id']==cid) for cid in p['concept_ids']]) for p in coverage['priority_entries']])
(LEARNING/'concept-matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n')
for case_id,case in bycase.items():
    rows=[r for r in raw if r['case_id']==case_id]
    out='---\ntitle: "Conceitos deste caso"\ndescription: "Mecanismos, comandos e limites de cada conceito ligado ao caso."\ndiataxis: explanation\n---\n\n# Conceitos: '+case['group'].lower()+'\n\n'
    out+='Este mapa conecta os conceitos ao mesmo problema. '+case['story']+'\n\n'
    out+=f'Comece pela [jornada]({case["destinations"]["journey"]}), execute o [tutorial]({case["destinations"]["tutorial"]}) e use a [referência]({case["destinations"]["reference"]}) para consultar parâmetros. Para resolver sua própria tarefa, siga o [guia]({case["destinations"]["how_to"]}).\n\n'
    out+='Cada entrada informa se você observa um mecanismo local ou se compara um princípio que uma implementação completa também precisaria atender. O segundo caso conserva a distância entre um modelo finito e um protocolo ou produto real.\n\n'
    for row in rows:
        out+='<span id="'+row['concept_id']+'" />\n\n## '+row['canonical_name']+'\n\n'
        out+=row['mechanism']+'\n\nNo caso desta família, faça a seguinte observação: '+row['exercise_action']+'\n\n'
        if row['command']:
            out+='```sh\n'+row['command']+'\n```\n\n'
        else:
            out+='Esta entrada permanece como uma lacuna de prática. A referência explica o mecanismo, mas a presença deste registro e dos quatro destinos não cumpre a experiência específica exigida para ele.\n\n'
        if row['command']:
            out+='O código desta observação está em `'+row['observation_source_file']+'`. O identificador do probe é `'+row['probe']+'`.\n\n'
            contract=object_contracts.get(row['canonical_name']) if row['probe']=='object-patterns' else financial_contracts.get(row['probe'])
            if contract:
                out+='Confira os valores do contrato antes e depois, e não apenas se as duas saídas são diferentes:\n\n```json\n'+json.dumps({'before':contract['before'],'after':contract['after']},ensure_ascii=False,indent=2)+'\n```\n\n'
        label={'LOCAL_MECHANISM':'um mecanismo local executado','EXECUTABLE_PRINCIPLE_COMPARISON':'uma comparação executável de princípio','HISTORICAL_SEMANTIC_TRANSFER':'uma transferência semântica a partir do código histórico','PENDING_SPECIFIC_PRACTICE':'uma prática específica pendente'}[row['coverage_level']]
        if row['command']:
            out+='O vínculo é '+label+'. '+row['limit']+'\n\n'
        else:
            out+='O exercício da família pode ser estudado como contexto; ele não conta como execução de '+row['canonical_name']+'.\n\n'
        out+=f'A [explicação do capítulo]({row["original_explanation"]}) amplia a decisão, e a [entrada de referência]({row["original_reference"]}) descreve o conceito para consulta. A [jornada do caso]({case["destinations"]["journey"]}) permite continuar com o mesmo problema.\n\n'
    path=ROOT/f'content/jornadas/{case_id}/conceitos.mdx';path.write_text(out)
    (path.parent/'_meta.js').write_text("export default { index: 'O caso', conceitos: 'Conceitos e prática' }\n")
    journey=path.parent/'index.mdx';text=journey.read_text()
    text=re.sub(r'\nEste caso reúne \d+ conceitos no \[mapa de mecanismos e práticas\].*?\n','\n',text)
    text+=f'\nEste caso reúne {len(rows)} conceitos no [mapa de mecanismos e práticas](/jornadas/{case_id}/conceitos/). Cada entrada informa se a prática específica está disponível ou pendente e conserva sua fronteira de conclusão.\n'
    journey.write_text(text)
    for section,key in [('explicacoes','explanation'),('tutoriais','tutorial'),('guias','how_to')]:
        p=ROOT/f'content/{section}/casos/{case_id}/index.mdx'
        current=re.sub(r'\nO \[mapa de conceitos deste caso\].*?\n','\n',p.read_text())
        text=current+f'\nO [mapa de conceitos deste caso](/jornadas/{case_id}/conceitos/) informa qual observação cada conceito compartilha com a prática e o que ela não comprova.\n'
        p.write_text(text)
summary='---\ntitle: "Todos os conceitos e seus casos"\ndescription: "A matriz dos 310 conceitos com quinze casos, quatro destinos e observações delimitadas."\ndiataxis: reference\n---\n\n# Todos os conceitos e seus casos\n\nA matriz adjudica os 310 conceitos canônicos do pedido. Cada entrada conserva a família, o caso e os quatro destinos Diátaxis. Somente um vínculo pertinente oferece um comando de prática; os demais identificam a experiência específica que ainda falta. Alguns vínculos mostram um mecanismo local diretamente; outros usam um contraexemplo executável para estudar um requisito do conceito. Um modelo de maioria, por exemplo, ajuda a discutir Raft, mas não executa Raft.\n\n'
summary+='| Caso | Conceitos | Destinos que conservam o mesmo problema |\n| --- | --- | --- |\n'
for case_id,case in bycase.items():
    count=sum(r['case_id']==case_id for r in raw);d=case['destinations']
    summary+=f'| [{case["title"]}](/jornadas/{case_id}/conceitos/) | {count} | [Explicação]({d["explanation"]}), [tutorial]({d["tutorial"]}), [guia]({d["how_to"]}) e [referência]({d["reference"]}). |\n'
supported=sum(r['learning_status']=='RELEVANT_BOUNDED_OBSERVATION' for r in raw)
pending=len(raw)-supported
counts={level:sum(r['coverage_level']==level for r in raw) for level in ['LOCAL_MECHANISM','EXECUTABLE_PRINCIPLE_COMPARISON','HISTORICAL_SEMANTIC_TRANSFER']}
summary+='\nOs 310 conceitos foram adjudicados contra a operação efetivamente executada. Há '+str(supported)+' vínculos com observação pertinente e '+str(pending)+' práticas específicas pendentes. As entradas pendentes não oferecem um comando de outro mecanismo como substituto. Os vínculos pertinentes também conservam os limites do modelo; uma observação de maioria não implementa Raft completo.\n\n'
summary+='## Os quarenta prioritários\n\nOs itens compostos conservam todos os seus conceitos. Cada link chega à entrada aplicada que contém mecanismo, comando e limite.\n\n'
for p in coverage['priority_entries']:
    refs=[next(r for r in raw if r['concept_id']==cid) for cid in p['concept_ids']]
    summary+=str(p['priority_id'])+'. '+p['original_label']+': '+', '.join(f'[{r["canonical_name"]}]({r["destinations"]["concept"]})' for r in refs)+'.\n'
summary+='\nA versão legível por máquina está em `tasks/FBI-4991-arquitetura-nextra/execution/learning/concept-matrix.json`. Os recibos locais ficam ao lado dela. A revisão independente avalia os mesmos hashes; a presença de um vínculo não preenche uma revisão pendente.\n'
(ROOT/'content/jornadas/matriz.mdx').write_text(summary)
print(json.dumps({'concepts':len(raw),'priority_entries':len(matrix['priority_entries']),'coverage_levels':counts,'relevant_observations':supported,'specific_practice_pending':pending},ensure_ascii=False))
