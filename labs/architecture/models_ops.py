"""Local availability, release, recovery and observability experiments."""
from copy import deepcopy
import json
import subprocess
import threading
from pathlib import Path


def item(case,probe,names,before,after,action,guarantee,limit):
    return dict(case=case,probe=probe,names=names,before=before,after=after,action=action,guarantee=guarantee,limit=limit)


def observations(case=None):
    if case in [None,'consensus']:
        def recover(mode):
            state={'running':mode!='cold','version':2 if mode=='hot' else 1,'role':'standby'};steps=[]
            if not state['running']:steps.extend(['restore','start']);state['running']=True
            if state['version']<2:steps.append('catch-up');state['version']=2
            steps.append('promote');state['role']='primary'
            return state,steps
        recovery={mode:recover(mode) for mode in ['cold','warm','hot']}
        yield item('consensus','standby-recovery-work',['Cold Standby','Warm Standby','Hot Standby','Active/Passive','Failover'],{'failed_primary_available':False},{'recovery_steps':{mode:steps for mode,(_,steps) in recovery.items()},'all_promoted':all(state['role']=='primary' for state,_ in recovery.values()),'all_versions':[state['version'] for state,_ in recovery.values()]},'Recupere a mesma versão com uma cópia fria, uma morna e uma quente. Execute os passos que faltam em cada uma antes de promover seu papel para primário.','Standby readiness changes the restore/start/catch-up work required before the role transition.','The steps are state transitions in a finite model, not measured RTO, restored backups or real database promotion.')
        clock,last_heartbeat,threshold=6,0,5;primary={'id':'A','healthy':True};standby={'id':'B','version':2,'role':'standby'}
        stale=clock-last_heartbeat>threshold
        if stale:primary['healthy']=False;standby['role']='primary'
        yield item('consensus','automatic-failover-detection',['Automatic Failover','Heartbeat'],{'primary_responded_at':last_heartbeat,'automatic_successor':None},{'heartbeat_stale':stale,'successor':standby['id'] if standby['role']=='primary' else None,'successor_version':standby['version'],'old_primary_healthy':primary['healthy']},'Avance o relógio de 0 para 6 com prazo 5, detecte o heartbeat antigo e promova a cópia que já alcançou a versão necessária.','A failure detector based on heartbeat age triggers the modeled role transition automatically.','A timeout suspects failure; this local model does not prove the old primary stopped or supply fencing under a network partition.')
        colocated=[{'zone':'A','region':'R1'},{'zone':'A','region':'R1'}];spread=[{'zone':'A','region':'R1'},{'zone':'B','region':'R2'}]
        survivors=lambda nodes,field,failed:sum(node[field]!=failed for node in nodes)
        yield item('consensus','failure-domain-spread',['Multi-AZ','Multi-Region'],{'survivors_after_zone_A_loss':survivors(colocated,'zone','A'),'survivors_after_region_R1_loss':survivors(colocated,'region','R1')},{'survivors_after_zone_A_loss':survivors(spread,'zone','A'),'survivors_after_region_R1_loss':survivors(spread,'region','R1')},'Distribua as duas instâncias entre zonas e regiões distintas e remova uma zona ou região inteira. Compare as instâncias que sobrevivem aos mesmos domínios de falha.','Replica placement across different failure domains leaves one instance after the declared zone or region outage.','Replication freshness, routing, shared dependencies, quorum and regulatory placement are not inferred from the survivor count.')
    if case in [None,'queue-workflow']:
        global_pool=threading.Semaphore(2);global_pool.acquire();global_pool.acquire();global_order_allowed=global_pool.acquire(blocking=False)
        quotes=threading.Semaphore(2);orders=threading.Semaphore(1);quotes.acquire();quotes.acquire();order_allowed=orders.acquire(blocking=False)
        global_pool.release();global_pool.release();quotes.release();quotes.release()
        if order_allowed:orders.release()
        yield item('queue-workflow','bulkhead-independent-pools',['Bulkhead'],{'order_allowed_while_quotes_fill_global_pool':global_order_allowed},{'order_allowed_with_separate_pool':order_allowed,'quote_capacity':2,'order_capacity':1},'Ocupe as duas vagas de cotações e tente executar uma ordem. Compare o pool global com os pools independentes de cotações e ordens.','A saturated dependency consumes only its own budget; the independent order pool retains capacity.','The actual semaphore admissions are local. Memory, CPU and cross-process resource isolation require additional budgets.')
        service={'running':False,'generation':1}
        before=service['running']
        def watchdog():
            if not service['running']:service['generation']+=1;service['running']=True
        watchdog();healthy_after=service['running']
        yield item('queue-workflow','watchdog-restart',['Self-Healing','Watchdog'],{'healthy':before,'generation':1},{'healthy_after_restart':healthy_after,'generation':service['generation']},'Pare o serviço lógico e execute a supervisão. Confira que ela cria uma nova geração e que a leitura de saúde volta a responder.','The supervisor detects the failed local state and rearms it through a replacement generation.','It is a finite restart model, without a real container, crash loop budget or a guarantee that every restart repairs the underlying cause.')
        def current_source():raise TimeoutError('controlled dependency timeout')
        cached={'balance':1000}
        def position_response():
            try:return {'balance':current_source(),'fresh':True,'writes_enabled':True}
            except TimeoutError:return {'balance':cached['balance'],'fresh':False,'writes_enabled':False}
        fallback=position_response()
        yield item('queue-workflow','fallback-limited-function',['Fallback','Graceful Degradation'],{'dependency_failure_result':'error'},{'response':fallback,'source':'last-known-cache'},'Provoque o timeout da fonte atual. Confira que a consulta limitada usa o último valor conhecido, sinaliza que ele não é atual e desabilita operações que exigiriam a informação fresca.','The fallback preserves a deliberately reduced read function and labels the stale result instead of silently claiming full service.','The cached value is synthetic; the acceptable age and permitted actions need the actual product contract.')
        order={'key':'ORDER-1','amount':100};outbox=[order];effects={};faults=[]
        def deliver(drop=False):
            if drop:faults.append('delivery_dropped');return
            for event in outbox:effects.setdefault(event['key'],event['amount'])
        deliver(drop=True);before_effects=len(effects);deliver();deliver()
        yield item('queue-workflow','chaos-delivery-experiment',['Chaos Engineering'],{'effects_after_injected_drop':before_effects},{'injected_faults':faults,'orders':1,'effects_after_recovery':len(effects),'debit':sum(effects.values()),'steady_invariant_restored':len(effects)==1},'Declare uma ordem e um efeito como estado esperado, injete a perda da primeira entrega e execute a recuperação com repetição. Confira a violação inicial e a recuperação sem débito duplicado.','A declared steady-state invariant is observed before/after an intentional fault and recovery experiment.','The fault is injected only in a controlled local model, not in a production system or distributed chaos platform.')
    if case in [None,'safe-release']:
        recreate=[2,0,2];rolling=[2];old,new=2,0
        while old:
            old-=1;rolling.append(old+new);new+=1;rolling.append(old+new)
        yield item('safe-release','rolling-recreate-capacity',['Rolling Deployment','Recreate Deployment'],{'recreate_ready_history':recreate,'minimum_ready':min(recreate)},{'rolling_ready_history':rolling,'minimum_ready':min(rolling),'new_instances':new},'Troque as duas instâncias encerrando todas antes de criar as novas e depois uma por vez. Conte a menor capacidade pronta de cada sequência.','Recreate produces a zero-ready interval in this schedule, while a one-at-a-time rolling replacement preserves one ready instance.','Readiness and resource capacity are assumed by the fixture; Kubernetes scheduling and actual service availability are not executed.')
        environments={'blue':{'version':1,'ready':True},'green':{'version':2,'ready':True}};route='blue';before_version=environments[route]['version']
        route='green';new_version=environments[route]['version'];route='blue';rollback_version=environments[route]['version']
        yield item('safe-release','blue-green-route',['Blue/Green Deployment'],{'visible_version':before_version},{'visible_after_switch':new_version,'visible_after_rollback':rollback_version,'blue_still_ready':environments['blue']['ready'],'provisioned_environments':len(environments)},'Mantenha blue e green prontos, altere a rota para green e volte a blue. Confira as versões visíveis e a capacidade antiga que precisou permanecer disponível.','Traffic changes between two already-provisioned environments and can return to the previous ready environment.','The route switch does not undo incompatible data written by the new environment; no deployment platform is contacted.')
        revisions={'revision-1':{'image':'v1','replicas':2},'revision-2':{'image':'v2','replicas':2}};selected='revision-2';actual={'image':'v1','replicas':0}
        plan=[{'field':key,'from':actual.get(key),'to':value} for key,value in revisions[selected].items() if actual.get(key)!=value]
        before_state=deepcopy(actual)
        for change in plan:actual[change['field']]=change['to']
        actual['replicas']=0;drifted=deepcopy(actual);actual=deepcopy(revisions[selected])
        yield item('safe-release','versioned-desired-reconcile',['GitOps','Infrastructure as Code'],{'observed':before_state},{'planned_fields':[change['field'] for change in plan],'selected_revision':selected,'drift_before_reconcile':drifted,'after_reconcile':actual},'Selecione a revisão 2 da fonte declarativa, calcule o plano e aplique-o. Depois introduza drift manual nas réplicas e reconcilie de novo pela mesma revisão.','A versioned desired-state source drives the plan and reconciliation instead of allowing manual runtime drift to become the desired source.','The revision store is a local model, not actual Git commits, Terraform state, a cluster operator or deployment proof.')
        old_instance={'id':'instance-1','image':'v1'};old_before=deepcopy(old_instance);new_instance={'id':'instance-2','image':'v2'};active=new_instance
        yield item('safe-release','immutable-replacement',['Immutable Infrastructure'],{'in_place_image_change_owner':'instance-1'},{'old_instance_unchanged':old_instance==old_before,'new_active_id':active['id'],'new_active_image':active['image'],'old_image_retained':old_instance['image']},'Crie a instância 2 com a imagem nova e altere o destino ativo, preservando a instância 1. Compare isso com editar a imagem do recurso existente.','The new infrastructure instance is created as a replacement while the prior instance remains unchanged.','Instance identity and images are logical fixtures, without a cloud API, image build or real infrastructure mutation.')
        calls=[];implementations={'legacy':lambda amount:amount,'new':lambda amount:amount};selected_impl='legacy'
        def facade(path,amount):
            owner=selected_impl if path=='/orders' else 'legacy';calls.append((path,owner));return implementations[owner](amount)
        old_result=facade('/orders',100);selected_impl='new';new_result=facade('/orders',100);position_result=facade('/positions',50)
        yield item('safe-release','strangler-abstraction-route',['Branch by Abstraction','Service Extraction','Strangler Fig','Transitional Architecture'],{'orders_owner':'legacy','result':old_result},{'calls':calls,'new_order_result':new_result,'legacy_position_result':position_result,'client_contract_preserved':old_result==new_result},'Faça o cliente usar a fachada, migre somente /orders para a implementação nova e mantenha /positions na antiga. Confira os donos chamados e o contrato observado pelo cliente.','An abstraction preserves the caller contract while routing one extracted capability to its new owner, leaving the rest on the legacy path during transition.','The services are logical functions. This does not implement independent deployment, a data migration or a transactional cutover.')
        shared=[{'domain':'orders','key':'A','amount':100},{'domain':'positions','key':'A','amount':1000}]
        stores={domain:{row['key']:row['amount'] for row in shared if row['domain']==domain} for domain in ['orders','positions']}
        stores['orders']['A']=150
        yield item('safe-release','decomposed-data-owners',['Database Decomposition','Modularization'],{'shared_rows':len(shared),'applications_share_same_mutable_table':True},{'order_value':stores['orders']['A'],'position_value':stores['positions']['A'],'separate_stores':stores['orders'] is not stores['positions'],'owner_count':len(stores)},'Extraia as linhas por dono, altere o armazenamento de ordens e confira que a posição não é reescrita pelo acesso direto à mesma tabela.','Data is split into stores with explicit capability owners, exposing the need for an integration contract between the formerly shared consumers.','The stores are local maps; schema migrations, foreign-key removal and cross-database reconciliation are not executed.')
    if case in [None,'diagnostics']:
        active,capacity,waiting=2,2,3;used_cpu,cpu_capacity=8,10;requests,window,failed=2,1,1;durations=[10,800]
        yield item('diagnostics','golden-use-resource-signals',['Golden Signals','USE Method (Utilization, Saturation, Errors)'],{'process_health':'ok','resource_saturation_measured':False},{'traffic_requests_per_second':requests/window,'maximum_duration_ms':max(durations),'failed_requests':failed,'queued_requests':waiting,'active_slots':active,'slot_capacity':capacity,'cpu_utilization':used_cpu/cpu_capacity},'Mantenha o processo saudável enquanto as duas vagas estão ocupadas e três pedidos aguardam. Calcule tráfego, duração, erros, utilização e saturação em seus grãos declarados.','The sample distinguishes healthy process status from traffic/latency/errors/saturation and from resource utilization/saturation/errors.','These are controlled sample measurements, not production percentiles, SLOs or a capacity benchmark.')
        root=Path(__file__).resolve().parent;python=root/'.venv/bin/python'
        if not python.exists():raise RuntimeError('Run python3 labs/architecture/setup_labs.py before the OpenTelemetry case.')
        result=subprocess.run([str(python),str(root/'otel_probe.py')],capture_output=True,text=True,check=True,timeout=10)
        captured=json.loads(result.stdout)
        yield item('diagnostics','opentelemetry-sdk-export',['OpenTelemetry','Distributed Tracing'],captured['before'],captured['after'],'Execute o SDK OpenTelemetry fixado, injete e extraia traceparent entre gateway e provider e exporte para memória. Confira o mesmo trace, o parent span e o erro, sem confundir dois spans com duas requisições.','The real SDK exports two parent/child spans in one trace, propagates context and records one failed span for one request.','The exporter is in memory with SDK 1.45.1. There is no collector, network service or claim of production instrumentation.')
