"""Financial event-processing, choreography and durable-step observations."""
from collections import defaultdict,deque
import sqlite3
import tempfile
from pathlib import Path


def item(probe,names,before,after,action,guarantee,limit):
    return dict(case='queue-workflow',probe=probe,names=names,before=before,after=after,action=action,guarantee=guarantee,limit=limit)


def observations():
    stream=[{'offset':index,'amount':amount} for index,amount in enumerate([100,-20,50])]
    consumed=stream[0]['amount'];checkpoint=stream[0]['offset'];tail=[event for event in stream if event['offset']>checkpoint]
    recovered=consumed+sum(event['amount'] for event in tail)
    yield item('stream-offset-resume',['Event Streaming'],{'replay_all_after_first_effect':consumed+sum(event['amount'] for event in stream)},{'resume_offsets':[event['offset'] for event in tail],'position_after_resume':recovered,'last_offset':tail[-1]['offset']},'Consuma o offset 0, interrompa e retome somente depois do checkpoint. Confira offsets 1 e 2 e a posição 130, sem repetir o crédito inicial.','An ordered event log and an explicit consumer position let the consumer resume the remaining events.','The log is a local immutable fixture. Retention, partitioned offsets, broker transactions and durable checkpoint atomicity are separate concerns.')
    running=[];total=0
    for event in stream:total+=event['amount'];running.append(total)
    yield item('batch-stream-emission',['Batch Processing','Stream Processing'],{'batch_outputs_at_end':[sum(event['amount'] for event in stream)]},{'incremental_outputs':running,'final_position':total,'updates_before_last_event':len(running)-1},'Processe os três eventos como um lote completo e depois um por vez. Observe quando cada modelo produz uma posição e confira o mesmo total final.','Batch emits after the chosen finite input set completes; stream processing updates the result as each event arrives.','The finite input demonstrates emission semantics rather than an unbounded engine, watermark or event-time guarantee.')
    mapped=[('buy',100),('sell',20),('buy',50)];groups=defaultdict(list)
    for key,value in mapped:groups[key].append(value)
    reduced={key:sum(values) for key,values in groups.items()}
    yield item('mapreduce-grouping',['MapReduce'],{'ungrouped_partial_values':[value for _,value in mapped]},{'grouped_totals':reduced,'mapped_records':len(mapped)},'Mapeie as ordens para pares de tipo e valor, agrupe pela chave e reduza cada grupo. Confira buy=150 e sell=20.','The map/group/reduce stages aggregate values per key instead of confusing all partial values with one total.','This is local grouping, not a distributed shuffle, combiner or fault-tolerant MapReduce runtime.')
    prefix=stream[:2];tail=stream[2:];batch=sum(event['amount'] for event in prefix);speed=sum(event['amount'] for event in tail)
    yield item('lambda-disjoint-views',['Lambda Architecture'],{'batch_plus_overlapping_all_stream':batch+sum(event['amount'] for event in stream)},{'batch_cutoff_offset':1,'batch_value':batch,'speed_after_cutoff':speed,'merged_position':batch+speed},'Defina o cutoff no offset 1, mantenha o lote até esse ponto e a visão rápida somente depois dele. Compare a soma sobreposta incorreta com 80 + 50 = 130.','Batch and speed-layer views cover disjoint input positions before being merged, preventing double counting at their boundary.','The example models the Lambda view boundary, without two deployed engines, backfill orchestration or full event-time handling.')
    def processor(events):return sum(event['amount'] for event in events)
    old_bug=sum(abs(event['amount']) for event in stream);rebuilt=processor(stream);stream_with_new=stream+[{'offset':3,'amount':10}]
    yield item('kappa-one-log-replay',['Kappa Architecture'],{'buggy_projection_before_replay':old_bug},{'replayed_position':rebuilt,'position_after_new_event':processor(stream_with_new),'processing_implementations':1,'log_offsets':[event['offset'] for event in stream_with_new]},'Corrija a interpretação do débito e reexecute o mesmo processador sobre o log. Acrescente um evento e confira que a mesma lógica atende reconstrução e continuidade.','One retained event log and one processing path support replay and ongoing processing rather than a separate batch algorithm.','Retention, reprocessing isolation and operational cutover of a new stream version are not implemented.')
    incoming=deque([{'kind':'order-placed','amount':100}]);balance=[1000];event_trace=[]
    def cash_on_order(event):balance[0]-=event['amount'];incoming.append({'kind':'funds-reserved','amount':event['amount']})
    def risk_on_reserved(event):incoming.append({'kind':'allocation-failed','amount':event['amount']})
    def cash_on_failure(event):balance[0]+=event['amount'];incoming.append({'kind':'compensated','amount':event['amount']})
    subscribers={'order-placed':[cash_on_order],'funds-reserved':[risk_on_reserved],'allocation-failed':[cash_on_failure]}
    while incoming:
        event=incoming.popleft();event_trace.append(event['kind'])
        for subscriber in subscribers.get(event['kind'],[]):subscriber(event)
    yield item('choreographed-compensation',['Choreography','Choreography Saga'],{'debit_without_reaction_to_failed_allocation':900},{'final_balance':balance[0],'event_trace':event_trace,'top_level_step_coordinator':False},'Publique order-placed e deixe cada participante reagir ao fato que conhece. Observe funds-reserved, allocation-failed e compensated recomporem o saldo sem um coordenador que chame todos os passos.','Local subscribers emit the next facts and a compensation handler reacts to the failure, exhibiting choreographed saga collaboration.','Delivery, duplicate events, distributed recovery and cycles are not solved by this in-memory choreography.')
    outgoing=deque();trace=[]
    def submit():outgoing.append('ORDER-1');trace.append('caller-returned');return 'accepted'
    result=submit()
    try:outgoing.popleft();raise RuntimeError('controlled worker failure')
    except RuntimeError:trace.append('worker-failed')
    yield item('fire-forget-return',['Fire-and-Forget'],{'caller_waiting_for_failed_handler':True},{'caller_result':result,'trace':trace,'caller_completed_before_failure':trace.index('caller-returned')<trace.index('worker-failed')},'Retorne ao chamador depois de emitir a intenção e provoque a falha do worker mais tarde. Diferencie a confirmação da chamada da conclusão do trabalho.','The caller does not await the later handler result, so its successful return does not prove eventual delivery or business completion.','The outgoing queue is not durable and no delivery guarantee is claimed.')
    sources={'orders':['ORDER-1','ORDER-2'],'settlements':['SETTLEMENT-1']};merged=[]
    for owner,messages in sources.items():
        for message in messages:merged.append((owner,message))
    yield item('fanin-source-correlation',['Fan-in'],{'single_source_messages':len(sources['orders'])},{'merged_messages':len(merged),'source_counts':{owner:sum(source==owner for source,_ in merged) for owner in sources},'identities':[message for _,message in merged]},'Reúna o fluxo de ordens e o de liquidações preservando a origem de cada mensagem. Confira três entradas e as duas contagens por fonte.','Multiple input streams converge into one correlated output without discarding source ownership.','The finite merge does not order independent clocks or wait for a distributed completeness barrier.')
    with tempfile.TemporaryDirectory(prefix='workflow-checkpoint-') as directory:
        path=Path(directory)/'workflow.sqlite';db=sqlite3.connect(path)
        db.executescript("CREATE TABLE progress(workflow_key TEXT PRIMARY KEY,phase TEXT); CREATE TABLE effects(effect_key TEXT PRIMARY KEY); INSERT INTO progress VALUES ('ORDER-1','validated');")
        with db:db.execute("INSERT INTO effects VALUES ('credit:ORDER-1')");db.execute("UPDATE progress SET phase='credited' WHERE workflow_key='ORDER-1'")
        db.close()
        resumed=sqlite3.connect(path);phase=resumed.execute("SELECT phase FROM progress WHERE workflow_key='ORDER-1'").fetchone()[0]
        if phase=='credited':
            with resumed:resumed.execute("INSERT INTO effects VALUES ('notify:ORDER-1')");resumed.execute("UPDATE progress SET phase='complete' WHERE workflow_key='ORDER-1'")
        effects=resumed.execute('SELECT effect_key FROM effects ORDER BY effect_key').fetchall();final=resumed.execute("SELECT phase FROM progress WHERE workflow_key='ORDER-1'").fetchone()[0];resumed.close()
    yield item('durable-workflow-resume',['Workflow Engine'],{'restart_from_beginning_credit_attempts':2},{'phase_loaded_after_reopen':phase,'final_phase':final,'effect_keys':[key for key, in effects],'credit_effects':sum(key.startswith('credit:') for key, in effects)},'Interrompa depois de persistir credited, feche a conexão e reabra o arquivo de progresso. Confira que a retomada executa a notificação e não repete o crédito já registrado.','A persisted workflow identity and phase drive recovery after process-state loss, skipping the completed local step.','The local effects and checkpoints share SQLite transactions. External activity retries, timers, worker leasing and a full durable-workflow framework are not implemented.')
