"""Executable structural properties of financial application architectures."""
from collections import deque


def item(probe,names,before,after,action,guarantee,limit):
    return dict(case='order-boundaries',probe=probe,names=names,before=before,after=after,action=action,guarantee=guarantee,limit=limit)


def observations():
    class Ledger:
        def __init__(self):self.balance=1000;self.callers=[]
        def credit(self,amount,caller):
            if amount<=0:raise ValueError('positive credit required')
            self.callers.append(caller);self.balance+=amount
    unsafe=Ledger();unsafe.credit(100,'view')
    model=Ledger();shown=[]
    def view(dto):shown.append(f"Balance {dto['balance']}")
    def controller(amount):model.credit(amount,'controller');view({'balance':model.balance})
    controller(100)
    yield item('mvc-controller-model-view',['MVC'],{'view_writes':unsafe.callers.count('view')},{'view_writes':model.callers.count('view'),'controller_writes':model.callers.count('controller'),'rendered':shown},'Execute o crédito pelo controlador e confira que a apresentação recebe apenas os dados finais, sem realizar a escrita do modelo.','The controller changes the model and selects a view; the view renders a DTO and never owns the write.','A local role model; routing, templates and a web framework are not implemented.')
    passive_view=[];reads=[0]
    def load_model():reads[0]+=1;return {'balance':1100}
    def presenter():passive_view.append(f"R$ {load_model()['balance']},00")
    presenter()
    yield item('mvp-passive-view',['MVP'],{'view_source_reads':1,'display':'1100'},{'view_source_reads':0,'presenter_source_reads':reads[0],'display':passive_view[0]},'Substitua a view por uma lista que recebe chamadas do presenter. Confira quem lê o modelo e quem transforma a informação para apresentação.','The presenter loads and prepares the model result; a passive view only receives the display value.','The recording view models the interface boundary rather than a full UI toolkit.')
    display={'text':'1000'};listeners=[];vm={'balance':1000}
    listeners.append(lambda value:display.update(text=str(value)))
    def set_balance(value):
        vm['balance']=value
        for callback in listeners:callback(value)
    set_balance(1100)
    yield item('mvvm-binding',['MVVM'],{'view_after_plain_assignment':'1000'},{'view_after_bound_assignment':display['text'],'view_model_balance':vm['balance'],'binding_callbacks':len(listeners)},'Altere a propriedade balance do view model e observe o callback de binding atualizar a apresentação sem uma chamada explícita de renderização no comando.','A binding propagates an observable view-model property change into the view.','The model covers one-way binding; validation, two-way binding and UI lifecycle remain outside it.')
    child_values={'orders':100,'fees':50};control_events=[]
    class Agent:
        def __init__(self,name):self.name=name;self.abstraction=0;self.presentation='0'
        def control(self,value):self.abstraction=value;self.presentation=str(value);control_events.append(self.name)
    children=[Agent(name) for name in child_values];parent=Agent('parent')
    for child in children:child.control(child_values[child.name])
    parent.control(sum(child.abstraction for child in children))
    yield item('pac-agent-controls',['PAC'],{'shared_view_last_child_value':list(child_values.values())[-1]},{'parent_total':parent.abstraction,'parent_display':parent.presentation,'controls_visited':control_events},'Faça dois controles filhos atualizarem suas abstrações e peça ao controle pai para compor o total. Compare com a última escrita isolada de uma apresentação compartilhada.','Each agent owns abstraction, presentation and control; parent control coordinates the child agents.','This is a small hierarchical PAC model, not a recommendation to adopt PAC in MakersHub.')
    trace=[]
    stores={'memory-A':[],'memory-B':[]}
    def domain_order(amount,save_port):
        trace.append('domain');
        if amount<=0:raise ValueError('positive amount')
        save_port({'amount':amount});return amount
    def application(amount,port):trace.append('application');return domain_order(amount,port)
    def entry(amount,port):trace.append('presentation');return application(amount,port)
    for name in stores:entry(100,stores[name].append)
    imports_before={'domain':{'postgres_driver'},'adapter':set()}
    imports_after={'domain':{'save_port'},'adapter':{'save_port'}}
    yield item('inward-ports-and-layers',['Layered / N-Tier','Clean Architecture','Onion Architecture','Hexagonal / Ports & Adapters'],{'domain_imports_storage_driver':'postgres_driver' in imports_before['domain']},{'domain_imports_storage_driver':'postgres_driver' in imports_after['domain'],'saved_per_adapter':{k:len(v) for k,v in stores.items()},'call_order':trace[:3]},'Siga presentation, application e domain e troque a implementação da porta de gravação entre dois adaptadores. Confira a regra e os imports do domínio.','Ordered invocation exhibits layers; the domain depends on its port and two replaceable adapters implement that port, exhibiting the inward dependency property of Clean/Onion/Hexagonal designs.','Only these boundary properties are modeled. The four styles have further distinctions not erased by sharing the exercise.')
    modules={'orders':{'internal':[]},'positions':{'internal':[]}}
    component_calls=[]
    def order_component(amount):component_calls.append('orders.public.place');modules['orders']['internal'].append(amount);return amount
    def position_component(amount):component_calls.append('positions.public.project');modules['positions']['internal'].append(amount)
    position_component(order_component(100))
    yield item('module-public-contract',['Modular Monolith','Component-Based Architecture','Vertical Slice Architecture'],{'cross_module_internal_writes':1},{'cross_module_internal_writes':0,'public_calls':component_calls,'order_feature_parts':['validate','place','persist'],'single_process':True},'Execute a ordem pelo contrato público do módulo e atualize posições pelo contrato do outro módulo. Examine o agrupamento da validação, do handler e da persistência na fatia de ordens.','Public component contracts separate modules in one process; the order feature groups the steps of one vertical use case.','The model demonstrates module and feature boundaries, not automatic proof of a repository-wide architecture.')
    plugins={'standard':lambda amount:amount*.01}
    missing_before='premium' not in plugins
    plugins['premium']=lambda amount:amount*.005
    yield item('microkernel-plugin',['Microkernel / Plugin Architecture'],{'premium_available':not missing_before},{'premium_available':'premium' in plugins,'fee':plugins['premium'](1000),'core_dispatch_branches_added':0},'Registre um plugin premium no catálogo e execute a política pelo contrato já usado pelo núcleo. Confira que o dispatcher não ganha um novo condicional.','A stable kernel invokes a registered extension through a shared contract.','Isolation, signing, lifecycle and dependency policy of untrusted plugins are not implemented.')
    blackboard={'available_funds':1000,'order_amount':100};rounds=0
    def risk(board):
        if board['available_funds']>=board['order_amount']:board['risk_approved']=True
    def allocator(board):
        if board.get('risk_approved'):board['allocation']='reserved'
    before=blackboard.get('allocation')
    while 'allocation' not in blackboard:
        rounds+=1
        for specialist in [allocator,risk]:specialist(blackboard)
    yield item('blackboard-specialists',['Blackboard Architecture'],{'allocation':before},{'allocation':blackboard['allocation'],'rounds':rounds,'risk_approved':blackboard['risk_approved']},'Execute os especialistas na ordem em que alocação tenta agir antes de risco. Observe o quadro de fatos permitir que a próxima rodada conclua a alocação.','Independent specialists read and contribute to a shared problem state until their prerequisites become available.','The fixture has monotonic facts and two rounds; conflict resolution and an unrestricted expert scheduler are outside it.')
    class CounterActor:
        def __init__(self):self.mailbox=deque();self.state=0
        def send(self,delta):self.mailbox.append(delta)
        def process(self):
            while self.mailbox:self.state+=self.mailbox.popleft()
    stale_reads=[0,0];unsafe_count=stale_reads[0]+1;unsafe_count=stale_reads[1]+1
    actor=CounterActor();actor.send(1);actor.send(1);actor.process()
    yield item('actor-mailbox-writer',['Actor Model','Single Writer Principle'],{'counter_after_two_stale_writers':unsafe_count},{'counter':actor.state,'mailbox_empty':not actor.mailbox,'state_writer_count':1},'Envie dois incrementos ao ator e deixe somente seu consumidor de mailbox escrever o estado. Compare com dois leitores que gravam a partir do mesmo valor antigo.','A private state owner serializes messages and provides a single writer for this actor.','The mailbox is local; supervision, distributed actors and message durability are not claimed.')
    producer={'balance':1000};events=deque();projection={'balance':1000};handlers=[]
    def accept_credit(amount):producer['balance']+=amount;events.append({'kind':'credited','amount':amount})
    handlers.append(lambda event:projection.update(balance=projection['balance']+event['amount']))
    accept_credit(100);before_projection=projection['balance']
    while events:
        event=events.popleft()
        for handler in handlers:handler(event)
    yield item('event-driven-handler',['Event-Driven Architecture'],{'projection_before_event_dispatch':before_projection},{'projection_after_event_dispatch':projection['balance'],'producer_balance':producer['balance'],'producer_direct_projection_writes':0},'Aceite o crédito no produtor e observe a projeção só avançar quando seu handler recebe o evento. Inspecione que o produtor não chama a projeção diretamente.','The producer emits a fact and a subscribed handler reacts to it asynchronously in the local schedule.','Transport, delivery guarantees and cross-process execution are not part of this event-driven property model.')
    service_store={'balance':1000};service_calls=[]
    def account_service(operation,amount):
        service_calls.append(operation)
        if operation=='credit':service_store['balance']+=amount
        return service_store['balance']
    results=[account_service('credit',100),account_service('read',0)]
    failed_service=lambda:(_ for _ in ()).throw(RuntimeError('isolated service'))
    try:failed_service()
    except RuntimeError:pass
    survivor=account_service('read',0)
    yield item('service-boundaries',['Microservices','SOA'],{'shared_failure_stops_balance_read':True},{'balance_results':results,'read_after_other_service_failure':survivor,'public_operations':service_calls},'Execute o mesmo contrato de conta por duas operações e provoque uma falha no serviço vizinho. Confira que a leitura do dono da conta continua independente.','An explicit business service owns its store and operation contract; the other service failure does not mutate or prevent its operation in this controlled schedule.','Services are logical local participants. Network independence, deployment, discovery and distributed transactions are not proven.')
    external={'balance':1000};local_counts=[]
    def invocation(event):
        local={'counter':0};local['counter']+=1;local_counts.append(local['counter'])
        external['balance']+=event.get('credit',0)
        return external['balance']
    outputs=[invocation({'credit':100}),invocation({})]
    yield item('serverless-invocation',['Serverless'],{'next_fresh_local_balance':1000},{'invocation_balances':outputs,'local_counters':local_counts,'state_owner':'external_port'},'Inicie cada invocação com memória local nova e conserve o crédito pela porta externa. Confira que a segunda invocação vê 1.100 sem depender de um processo aquecido.','The handler tolerates fresh invocation memory and keeps authoritative state outside that ephemeral environment.','No cloud runtime, billing, autoscaling or vendor-specific execution contract is simulated.')
    cells=[{}, {}, {}];processed=[]
    for key in range(12):
        owner=key%len(cells);cells[owner][key]=key+1
    for owner,cell in enumerate(cells):
        for key in cell:cell[key]+=1;processed.append((owner,key))
    yield item('space-based-grid',['Space-Based Architecture'],{'central_store_failure_processed':0},{'grid_partitions':len(cells),'processed':len(processed),'value_sum':sum(sum(cell.values()) for cell in cells),'per_partition':[len(cell) for cell in cells],'external_database_calls':0},'Distribua as doze entradas pelo dono da chave e execute a alteração dentro de cada partição em memória. Confira a distribuição e a soma sem consultar um banco central.','A partitioned memory grid owns data and co-locates processing; the same owner partitions can serve shared cache reads to different logical workers.','The grid is a finite local model, without durable replication, network partitions or a deployed distributed-cache product.')
    def cell_request(cell):
        if cell=='A':raise RuntimeError('cell A unavailable')
        return 'accepted-B'
    completed=[]
    for cell in ['A','B']:
        try:completed.append(cell_request(cell))
        except RuntimeError:pass
    yield item('cell-failure-boundary',['Cell-Based Architecture'],{'shared_failure_successes':0},{'isolated_cell_successes':len(completed),'responses':completed},'Provoque a falha da célula A e continue o pedido destinado à célula B. Confira que a recuperação não redireciona silenciosamente dados de A para B.','Independent cells contain one failure while the other cell completes its own request.','Capacity, routing safety, replication and failover between real regions remain outside this local failure-boundary experiment.')

    cache_grid=[{},{}];source_calls=[0]
    def source_value(key):source_calls[0]+=1;return 1000
    def shared_cache_read(worker,key):
        owner=sum(key.encode())%len(cache_grid)
        if key not in cache_grid[owner]:cache_grid[owner][key]=source_value(key)
        return cache_grid[owner][key]
    values=[shared_cache_read('worker-A','POSITION-1'),shared_cache_read('worker-B','POSITION-1')]
    shared=item('distributed-cache-owner',['Distributed Cache'],{'independent_worker_cache_source_calls':2},{'shared_owner_source_calls':source_calls[0],'worker_values':values,'owner_partitions':len(cache_grid)},'Faça dois workers lógicos consultarem a mesma posição pelo dono da chave no cache compartilhado. Confira que a segunda leitura não volta à fonte.','Different logical workers use the same partition owner and share its populated cache entry, unlike independent per-worker caches.','The owners are local dictionaries; the experiment isolates shared-owner cache semantics without claiming a networked cache product or cross-machine durability.')
    shared['case']='cache-policy'
    yield shared
