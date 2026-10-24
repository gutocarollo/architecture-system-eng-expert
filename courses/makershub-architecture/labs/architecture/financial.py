"""Controlled financial examples. These are not Faz or XP runtime implementations."""
import argparse
import asyncio
import heapq
import bisect
from dataclasses import dataclass, FrozenInstanceError
import hashlib
import json
import sqlite3
import tempfile
from collections import Counter, deque
from pathlib import Path
from invariants import validate
from additional_observations import for_case


def record(name, before, after, guarantee, limit):
    before=json.loads(json.dumps(before))
    after=json.loads(json.dumps(after))
    validate(name,before,after)
    return dict(probe=name, before=before, after=after, guarantee=guarantee, limit=limit)


def order_boundaries():
    provider = {'customer_ref': 'SYNTHETIC-1', 'status': 'AUTHORISED', 'cents': 10000}
    before = provider['status'] == 'accepted'
    mapped = {'account_id': provider['customer_ref'], 'status': {'AUTHORISED':'accepted'}[provider['status']], 'amount': provider['cents']/100}
    after = mapped['status'] == 'accepted'
    yield record('provider-contract', {'booked':before}, {'booked':after,'amount':mapped['amount']}, 'The adapter translates an external language at one boundary.', 'No provider is called; network and credentials are absent.')
    observed = []
    def policy(amount, strategy):
        return strategy(amount)
    rule_a, rule_b = lambda amount: amount * .01, lambda amount: amount * .02
    before = [policy(1000, rule_a), policy(1000, rule_a)]
    after = [policy(1000, rule_a), policy(1000, rule_b)]
    yield record('replace-policy', before, after, 'A strategy is supplied to the domain operation; the caller can exchange it.', 'A callable alone does not prove a full architecture or deployment boundary.')
    def command(account, amount):
        if amount <= 0:
            return 'rejected'
        observed.append({'account':account,'amount':amount})
        return 'accepted'
    command('SYNTHETIC-1', -5)
    unsafe_writes=[]
    unsafe_writes.append({'account':'SYNTHETIC-1','amount':-5})
    yield record('validate-before-side-effect', {'invalid_writes':len(unsafe_writes)}, {'invalid_writes':len(observed)}, 'The command checks an invariant before invoking its write port.', 'The example checks one invariant; it does not model a financial regulation.')



    @dataclass(frozen=True)
    class Money:
        cents:int
        currency:str='BRL'
        def __post_init__(self):
            if self.cents<0:raise ValueError('negative amount')
    first,second=Money(10000),Money(10000)
    try:Money(-1);invalid_rejected=False
    except ValueError:invalid_rejected=True
    try:first.cents=20000;immutable=False
    except FrozenInstanceError:immutable=True
    yield record('value-object',{'negative_constructed':True,'mutable':True},{'equal_values':first==second,'distinct_instances':first is not second,'invalid_rejected':invalid_rejected,'immutable':immutable},'A monetary value compares by its components, rejects an invalid amount and is immutable without an entity identity.','The fixture supports one currency and a nonnegative domain rule; it is not a universal monetary contract.')
    external={'order_ref':'ORDER-1','amount_cents':10000,'provider_state':'AUTHORISED'}
    translated={'order_id':external['order_ref'],'amount':external['amount_cents']/100,'status':{'AUTHORISED':'accepted'}[external['provider_state']]}
    yield record('message-translation',{'consumer_has_order_id':'order_id' in external,'amount_unit':'cents'},{'consumer_has_order_id':'order_id' in translated,'amount':translated['amount'],'amount_unit':'BRL','status':translated['status']},'The translator creates the consumer schema and changes both field names and the amount unit.','Translation must preserve meaning; unknown provider states would require an explicit error policy.')

def order_delivery():
    messages = [('ORDER-1',100),('ORDER-1',100),('ORDER-2',50)]
    before = sum(value for _,value in messages)
    inbox = {}
    for key, value in messages:
        inbox.setdefault(key,value)
    yield record('deduplicate', {'debit':before,'effects':len(messages)}, {'debit':sum(inbox.values()),'effects':len(inbox)}, 'Repeated delivery of the same semantic operation has one effect in this store.', 'The key lifetime, atomic storage and payload conflict policy remain design obligations.')
    unsafe_orders=[]; unsafe_published=[]
    unsafe_orders.append('ORDER-1')
    # The simulated crash interrupts the next external write.
    before = {'orders':len(unsafe_orders),'published':len(unsafe_published)}
    orders, outbox = [], []
    with tempfile.TemporaryDirectory(prefix='order-delivery-') as directory:
        db=sqlite3.connect(Path(directory)/'lab.sqlite')
        db.executescript('CREATE TABLE orders(order_key TEXT PRIMARY KEY); CREATE TABLE outbox(event_key TEXT PRIMARY KEY);')
        with db:
            db.execute('INSERT INTO orders VALUES (?)',('ORDER-1',))
            db.execute('INSERT INTO outbox VALUES (?)',('ORDER-1',))
        orders=db.execute('SELECT * FROM orders').fetchall()
        outbox=db.execute('SELECT * FROM outbox').fetchall()
        db.close()
    yield record('commit-intention', before, {'orders':len(orders),'recoverable_events':len(outbox)}, 'One local transaction preserves both an order and its delivery intention.', 'Delivery and recipient deduplication are still separate; this is SQLite, not PostgreSQL CDC.')
    def allocate(compensate):
        balance=1000
        balance-=100
        allocation_ok=False
        if not allocation_ok and compensate:
            balance+=100
        return balance
    yield record('compensate', {'balance_after_failed_allocation':allocate(False)}, {'balance_after_failed_allocation':allocate(True)}, 'A compensating credit offsets the prior debit when allocation fails.', 'Compensation is a new business action; it does not erase history or undo every external effect.')



    with tempfile.TemporaryDirectory(prefix='inbox-') as directory:
        db=sqlite3.connect(Path(directory)/'lab.sqlite')
        db.executescript('CREATE TABLE inbox(message_key TEXT PRIMARY KEY); CREATE TABLE debit(message_key TEXT PRIMARY KEY,amount INTEGER);')
        for key,value in messages:
            with db:
                inserted=db.execute('INSERT OR IGNORE INTO inbox VALUES (?)',(key,)).rowcount
                if inserted:db.execute('INSERT INTO debit VALUES (?,?)',(key,value))
        inbox_count=db.execute('SELECT count(*) FROM inbox').fetchone()[0]
        effects=db.execute('SELECT count(*),sum(amount) FROM debit').fetchone();db.close()
    yield record('transactional-inbox',{'effects':len(messages),'debit':sum(v for _,v in messages)},{'inbox_rows':inbox_count,'effects':effects[0],'debit':effects[1]},'A transaction records message consumption and its monetary effect together, with a unique message key.','Atomicity is local to SQLite; external side effects require their own idempotency contract.')

def reservation():
    state={'balance':1000,'version':7}
    stale_b=state['balance']
    def commit(expected_version,next_balance):
        if state['version']!=expected_version:return False
        state.update(balance=next_balance,version=state['version']+1);return True
    assert commit(7,state['balance']+100)
    before=stale_b-200
    stale_rejected=not commit(7,stale_b-200)
    assert state['balance']==1100
    assert commit(state['version'],state['balance']-200)
    after=state['balance']
    yield record('version-conflict', {'balance':before,'lost_credit':100}, {'stale_rejected':stale_rejected,'balance_after_reread':after}, 'The stale editor cannot silently overwrite a preceding credit.', 'The re-read must revalidate business intent; a retry is not always permissible.')
    accepted_generation=102
    def write_with_fence(enabled):
        state={'last_writer':'B','value':accepted_generation}
        reject=enabled and 101<state['value']
        if not reject:
            state.update(last_writer='expired-A',value=101)
        return state,reject
    before,_=write_with_fence(False)
    after,rejected=write_with_fence(True)
    after['stale_101_rejected']=rejected
    yield record('fence',before,after,'The destination compares an ordered generation, including delayed writers.','A random owner UUID is not an ordered fence; an external destination must perform this check.')
    held=set()
    accepted=0
    for actor in ['operator-A','operator-B']:
        key=('SYNTHETIC-ADVISOR', '2026-10-15T14:00')
        if key not in held:
            held.add(key); accepted+=1
    unsafe_held={(actor,'slot') for actor in ['operator-A','operator-B']}
    yield record('resource-key',{'accepted_with_actor_keys':len(unsafe_held)},{'accepted_with_slot_key':accepted},'The shared slot, rather than the caller, is the protected identity.','This set is one-process memory; distributed storage must claim atomically and manage expiry.')


def consensus():
    nodes={'A','B','C'}
    partitions=[{'A','B'},{'C'}]
    before=sum(bool(p) for p in partitions)
    after=sum(len(p)>=len(nodes)//2+1 for p in partitions)
    yield record('majority-partition',{'leaders':before},{'leaders':after,'minority_writes':0},'Only a partition with two of three members can authorize a new write.','This finite model is not Raft or Paxos: terms, durable logs, elections and message faults are not implemented.')
    write_quorum,read_quorum,total=2,2,3
    yield record('quorum-overlap',{'intersection_lower_bound':max(0,1+1-total)},{'intersection_lower_bound':write_quorum+read_quorum-total},'For three replicas, read two and write two have at least one common member.','Intersection alone does not prove linearizability; version selection and failure assumptions matter.')
    a,b={'A':1,'B':0},{'A':0,'B':1}
    incomparable=not(all(a[k]<=b[k] for k in a) or all(b[k]<=a[k] for k in a))
    yield record('causal-versions',{'last_write_only':'A','lost_branch':'B'},{'concurrent_detected':incomparable,'merged_vector':{'A':1,'B':1}},'A vector exposes concurrent branches before application-specific reconciliation.','The vector does not decide the financial meaning of merging two orders.')
    local,remote=3,8
    yield record('logical-clock',{'receive_clock':local+1},{'receive_clock':max(local,remote)+1},'A receive event advances beyond the causal sender clock.','Lamport order does not prove concurrency; hybrid clocks also need physical-clock policy.')
    def decide(prepared,coordinator_known,protected):
        if prepared and not coordinator_known:
            return 'wait_for_decision' if protected else 'commit_guessed'
        return 'coordinator_decision'
    yield record('prepared-participant',{'prepared_then_timeout':decide(True,False,False)},{'prepared_then_timeout':decide(True,False,True)},'A prepared participant cannot invent the coordinator decision.','This models blocking in atomic commit; it neither implements 2PC/3PC nor proves partition tolerance.')



    knowledge={peer:{peer} for peer in ['A','B','C']}
    before_sizes={peer:len(items) for peer,items in knowledge.items()}
    for _ in range(2):
        for left,right in [('A','B'),('B','C')]:
            merged=knowledge[left]|knowledge[right]
            knowledge[left]=set(merged);knowledge[right]=set(merged)
    yield record('gossip-membership',{'known_members':before_sizes},{'known_members':{peer:len(items) for peer,items in knowledge.items()},'all_agree':all(items=={'A','B','C'} for items in knowledge.values())},'Repeated peer exchanges disseminate membership without a central broadcaster.','Dissemination is not consensus; failures, tombstones and convergence under partitions are not implemented.')
    workers=[{},{}];workers[0]['SESSION-1']='SYNTHETIC-USER'
    before_request=workers[1].get('SESSION-1')
    shared_sessions={'SESSION-1':'SYNTHETIC-USER'}
    after_requests=[shared_sessions.get('SESSION-1') for _ in workers]
    yield record('stateless-request',{'second_worker_user':before_request},{'worker_users':after_requests,'local_session_counts':[len({}) for _ in workers]},'Application instances obtain session state outside local request-process memory, so routing to another instance preserves the request context.','The shared dictionary models an external owner, not a deployed session service or verified token.')


    primary={'version':1,'balance':1000};replica=dict(primary)
    primary.update(version=2,balance=1100)
    stale_read=dict(replica);replica.update(primary)
    yield record('replica-lag',{'replica_version':stale_read['version'],'primary_version':primary['version']},{'replica_version':replica['version'],'primary_version':primary['version'],'balance':replica['balance']},'An asynchronous replica may serve an older committed value and converges only after applying the update.','The model has one update and reliable replay, not a distributed replication protocol.')
    replica_old={'version':1,'balance':1000};minimum_seen=2
    selected=primary if replica_old['version']<minimum_seen else replica_old
    yield record('session-read-version',{'read_version':replica_old['version'],'regressed':replica_old['version']<minimum_seen},{'read_version':selected['version'],'regressed':selected['version']<minimum_seen,'balance':selected['balance']},'A session requires at least the version already observed or written and routes away from an older replica.','Version routing needs an explicit session token and a reachable owner; it is not global linearizability.')

def queue_workflow():
    source=[{'id':f'ORDER-{i}','kind':'trade' if i%2==0 else 'statement'} for i in range(6)]
    routed={'trade':[], 'statement':[]}
    for item in source:
        routed[item['kind']].append({**item,'account':'SYNTHETIC-1'})
    yield record('route-enrich-aggregate',{'one_untyped_batch':6},{'trade':len(routed['trade']),'statement':len(routed['statement']),'enriched':sum(len(v) for v in routed.values())},'A router chooses a destination; an enricher adds context and an aggregator can count each result.','The example does not guarantee distributed ordering or delivery.')
    queue=deque(['valid','poison'])
    delivered,dead=[],[]
    attempts=Counter()
    while queue:
        item=queue.popleft(); attempts[item]+=1
        if item=='poison':
            (queue if attempts[item]<3 else dead).append(item)
        else:
            delivered.append(item)
    unsafe_queue=deque(['poison']);unsafe_attempts=0
    while unsafe_queue and unsafe_attempts<6:
        item=unsafe_queue.popleft();unsafe_attempts+=1;unsafe_queue.append(item)
    yield record('retry-dlq',{'poison_attempts':unsafe_attempts,'dead_letters':0},{'poison_attempts':attempts['poison'],'dead_letters':len(dead),'delivered':len(delivered)},'A poison message exhausts three attempts and is retained outside the normal queue.','The six-attempt before trace is a bounded sample of an unbounded retry policy.')
    capacity,incoming=20,120
    yield record('admission',{'buffered':incoming,'rejected':0},{'buffered':min(capacity,incoming),'rejected':incoming-capacity},'Admission limits queued work before consuming unbounded memory.','A consumer semaphore alone cannot impose this limit on the producer.')
    events=[('ORDER-1',1),('ORDER-1',1),('ORDER-2',2)]
    seen=set(); assigned=[]
    for index,(key,seq) in enumerate(events):
        if key not in seen:
            seen.add(key);assigned.append((key,len(assigned)%2))
    yield record('consumer-topology',{'workers_each_execute_all':len(events)*2},{'shared_queue_effects':len(assigned),'worker_effects':[sum(worker==index for _,worker in assigned) for index in range(2)]},'Competing consumers divide work while separate subscriptions each receive the facts they need.','Retries still require an inbox; pub/sub is not a shared task queue.')
    before=['settled','reserved','accepted']
    sequence={'accepted':1,'reserved':2,'settled':3}
    ordered=sorted(before,key=sequence.__getitem__)
    allowed={'new':'accepted','accepted':'reserved','reserved':'settled'}
    invalid_first_rejected=allowed['new']!=before[0]
    state='new'
    for event in ordered:
        assert allowed[state]==event
        state=event
    yield record('resequence-state',{'states':before,'invalid_first':'settled'},{'states':ordered,'final':state,'invalid_first_rejected':invalid_first_rejected},'Sequence metadata enables ordering and a state machine rejects an invalid transition.','A missing earlier message needs timeout/recovery policy; sorting a batch is not a streaming resequencer.')
    failures=3; delay=[min(8,2**i) for i in range(failures)]
    failures_seen=0; circuit='closed'
    for _ in range(failures):
        if circuit=='open': break
        failures_seen+=1
        if failures_seen>=3: circuit='open'
    jitter=[base+offset for base,offset in zip(delay,[0.1,0.2,0.3])]
    yield record('retry-budget',{'attempt_times':[0,0,0],'final':'overload'},{'delays':delay,'jittered_delays':jitter,'attempts':failures_seen,'final':circuit+'-circuit'},'Budgeted attempts, exponential delay and fixed jitter spread work; the open circuit refuses more calls.','The jitter is deterministic for learning; timeouts, deadlines, rate limits and bulkheads have distinct owners.')
    dependency={'extract':set(),'transform':{'extract'},'publish':{'transform'}}
    done=set();order=[]
    while len(done)<len(dependency):
        ready=sorted(k for k,v in dependency.items() if k not in done and v<=done)
        assert ready,'cycle detected'
        done.update(ready);order.extend(ready)
    yield record('dag-dependencies',{'order':['publish','extract','transform']},{'order':order},'A task becomes eligible only after its prerequisites finish.','A DAG describes dependency; the loop does not implement a durable workflow engine or Airflow.')



    incoming=[{'id':'A','amount':100},{'id':'INVALID','amount':-20},{'id':'B','amount':50}]
    valid=[item for item in incoming if item['amount']>0]
    yield record('message-filter',{'accepted':len(incoming),'invalid_accepted':1},{'accepted':len(valid),'invalid_accepted':sum(item['amount']<=0 for item in valid),'valid_amount':sum(item['amount'] for item in valid)},'A filter drops the invalid item while preserving the two valid orders.','The predicate is a fixture, not a financial eligibility rule.')
    batch={'batch_id':'BATCH-1','orders':[{'id':'A','amount':100},{'id':'B','amount':50}]}
    children=[dict(order,batch_id=batch['batch_id']) for order in batch['orders']]
    yield record('message-splitter',{'handler_items':1,'individual_orders':0},{'handler_items':len(children),'individual_orders':len(children),'amount':sum(item['amount'] for item in children),'batch_ids':sorted({item['batch_id'] for item in children})},'A splitter converts one batch envelope into individual messages and retains their correlation.','Joining completion and recovering missing children are separate contracts.')


    ordinary=[('standard',1),('urgent',0),('low',2)]
    priority=[]
    for sequence,(name,rank) in enumerate(ordinary):heapq.heappush(priority,(rank,sequence,name))
    ordered=[heapq.heappop(priority)[2] for _ in range(len(priority))]
    yield record('priority-queue',{'processing_order':[name for name,_ in ordinary]},{'processing_order':ordered},'Priority metadata, with a stable sequence tie-breaker, changes which queued task is selected first.','A priority policy can starve low-priority work; that policy is not solved by the heap.')
    due=5;clock=3
    yield record('delayed-queue',{'dispatched_before_due':clock<due},{'dispatched_before_due':False,'dispatch_time':max(clock,due)},'Eligibility depends on a not-before time, so a task remains delayed until the clock reaches its due time.','This is a controlled clock, not a durable scheduled broker.')
    pending=list(range(6));buffer=[];processed=[];max_buffer=0
    while pending or buffer:
        while pending and len(buffer)<2:buffer.append(pending.pop(0));max_buffer=max(max_buffer,len(buffer))
        if buffer:processed.append(buffer.pop(0))
    yield record('demand-backpressure',{'maximum_buffer':6,'processed':6},{'maximum_buffer':max_buffer,'processed':len(processed),'rejected':0},'The producer advances only while downstream capacity is available; six tasks finish without buffering all six.','The synchronous schedule models demand; it is not a Reactive Streams implementation.')
    quota=2;windows={};accepted=0
    for second in [0,0,0,1]:
        if windows.get(second,0)<quota:windows[second]=windows.get(second,0)+1;accepted+=1
    yield record('rate-window',{'accepted':4,'rejected':0},{'accepted':accepted,'rejected':4-accepted,'per_second_limit':quota},'A fixed time window admits at most two calls in each second.','A boundary burst can span adjacent windows; distributed limit storage is not implemented.')
    async def bounded_wait():
        try:await asyncio.wait_for(asyncio.Event().wait(),timeout=0.001)
        except TimeoutError:return 'timeout'
        raise AssertionError('the never-released event must time out')
    yield record('timeout-boundary',{'waiting_state':'pending_without_bound'},{'waiting_state':asyncio.run(bounded_wait())},'A real asynchronous wait is cancelled by its timeout instead of remaining pending.','The timeout bounds this awaiter, not every external side effect or a worker thread.')
    parent_deadline=5;now=2;default_child_budget=10;child_budget=min(default_child_budget,parent_deadline-now)
    yield record('deadline-budget',{'child_budget':default_child_budget,'overruns_parent':now+default_child_budget>parent_deadline},{'child_budget':child_budget,'overruns_parent':now+child_budget>parent_deadline},'The child inherits the remaining parent budget instead of starting an independent longer deadline.','Cancellation of an external operation still depends on its own API contract.')


    event_ids=['EVENT-1','EVENT-2'];subscriptions={'audit':[],'risk':[]}
    for event_id in event_ids:
        for inbox in subscriptions.values():inbox.append(event_id)
    yield record('subscription-fanout',{'one_shared_queue_total_deliveries':len(event_ids)},{'audit':subscriptions['audit'],'risk':subscriptions['risk'],'total_deliveries':sum(map(len,subscriptions.values()))},'Independent subscriptions each receive the two events, unlike one work queue that divides the two tasks.','Each subscription needs its own retry and deduplication policy.')
    notification={'event_id':'EVENT-1','order_id':'ORDER-1'}
    carried={**notification,'amount':100,'status':'accepted'}
    source={'ORDER-1':{'amount':100,'status':'accepted'}}
    lookup=source[notification['order_id']]
    yield record('event-payload',{'source_lookups':1,'amount':lookup['amount']},{'source_lookups':0,'amount':carried['amount'],'status':carried['status']},'A notification identifies what changed; a carried-state event lets this consumer act without fetching the source.','A richer event also exposes more schema and data; it does not guarantee current source state.')

def cache_policy():
    requests=[('tenant-A','position'),('tenant-B','position')]
    unsafe={};safe={}
    for tenant,field in requests:
        unsafe.setdefault(field,tenant);safe.setdefault((tenant,field),tenant)
    yield record('cache-key',{'tenant_B_reads':unsafe['position']},{'tenant_B_reads':safe[('tenant-B','position')]},'Tenant and query scope belong in a key before a cached result is shared.','The tenant label is synthetic; real authorization must precede lookup.')
    expires_at,now=10,11
    yield record('cache-expiry',{'stale_returned':True},{'stale_returned':now<expires_at,'decision':'reload'},'TTL creates an explicit validity boundary and expiration returns control to the producer.','TTL does not prove source freshness or invalidate a value immediately after a write.')
    def durable_at_crash(write_through):
        durable,cache=1000,1000
        cache+=100
        if write_through: durable=cache
        cache=None
        return durable
    yield record('write-policy',{'write_behind_crash_durable_balance':durable_at_crash(False)},{'write_through_durable_balance':durable_at_crash(True)},'Acknowledging after durable write avoids losing a buffered credit during this crash.','Different ordering has different latency; neither alone gives cross-system atomicity.')
    local={'value':1};shared={'value':2}
    local.pop('value')
    local.update(shared)
    yield record('cache-levels',{'worker_A':1,'worker_B':2},{'worker_A':local['value'],'worker_B':shared['value']},'Invalidation permits the local level to reload from its shared owner.','Two copies still require freshness, errors, eviction and stampede contracts.')



    def read_position(use_cache):
        cache={};calls=0;values=[]
        for _ in range(3):
            if not use_cache or 'position' not in cache:
                calls+=1
                cache['position']=1000
            values.append(cache['position'])
        return {'source_calls':calls,'values':values,'cache_populated':bool(cache)}
    yield record('cache-aside',read_position(False),read_position(True),'A cache-aside miss loads from the source and populates the key; later reads hit that key.','This is one process; invalidation and concurrent misses require separate mechanisms.')
    def absent_position(cache_absence):
        cache={};calls=0;results=[]
        for _ in range(3):
            if 'missing' not in cache:
                calls+=1
                if cache_absence:cache['missing']=None
            results.append(cache.get('missing'))
        return {'source_calls':calls,'results':results,'absence_cached':'missing' in cache}
    yield record('negative-cache',absent_position(False),absent_position(True),'A known absence is represented by a cached sentinel and suppresses repeated source lookups.','An absence must expire; an absent key and a cached None must remain distinguishable.')
    def warming(warm):
        cache={};requests=0
        if warm:cache['position']=1000
        if 'position' not in cache:requests+=1;cache['position']=1000
        return {'request_path_source_calls':requests,'value':cache['position']}
    yield record('cache-warming',warming(False),warming(True),'Preloading a known key moves its initial fetch before the first user read.','Warming does not prove that the source is fresh or that all keys should be loaded.')


    class ReadThroughCache:
        def __init__(self,loader):self.loader=loader;self.values={}
        def read(self,key):
            if key not in self.values:self.values[key]=self.loader(key)
            return self.values[key]
    source_calls=[]
    def loader(key):source_calls.append(key);return 1000
    api=ReadThroughCache(loader)
    returned=[api.read('position') for _ in range(3)]
    yield record('read-through',{'caller_source_calls':3,'cache_api_owns_loading':False},{'caller_source_calls':0,'loader_calls':len(source_calls),'cache_api_owns_loading':True,'values':returned},'The caller uses only cache.read; the cache API invokes its loader on a miss and stores the result.','This is a local cache abstraction, not a distributed cache provider.')

def ledger_projection():
    events=[('credit',1000),('credit',100),('debit',200)]
    balance=sum(value if kind=='credit' else -value for kind,value in events)
    yield record('replay-events',{'mutable_balance_without_history':1000-200},{'replayed_balance':balance,'events':len(events)},'An append-only record can replay the credits and debit into a read position.','These are business events, not arbitrary row-change logs; audit storage alone is not Event Sourcing.')
    projection=1000
    for kind,value in events[1:]:
        projection+=value if kind=='credit' else -value
    yield record('projection-checkpoint',{'projection':1000,'lag_events':2},{'projection':projection,'lag_events':0},'A projection advances only after consuming its missing events.','The demonstration has no durable checkpoint, broker or read-your-writes API.')
    with tempfile.TemporaryDirectory(prefix='ledger-') as directory:
        db=sqlite3.connect(Path(directory)/'lab.sqlite')
        mode=db.execute('PRAGMA journal_mode=WAL').fetchone()[0]
        db.execute('CREATE TABLE balance(account_key TEXT PRIMARY KEY, cents INTEGER)')
        db.execute('INSERT INTO balance VALUES (?, ?)',('SYNTHETIC-1',100000));db.commit()
        db.execute('UPDATE balance SET cents=110000');db.rollback()
        cents=db.execute('SELECT cents FROM balance').fetchone()[0];db.close()
    yield record('durable-transaction',{'partial_update_visible':110000},{'rolled_back_cents':cents,'sqlite_journal_mode':mode},'A local transaction rolls back an incomplete change while SQLite uses its WAL mode.','This is a SQLite engine check, not a PostgreSQL recovery, replication or fsync proof.')
    snapshot=(2,1100); remaining=events[snapshot[0]:]
    rebuilt=snapshot[1]+sum(v if k=='credit' else -v for k,v in remaining)
    yield record('snapshot-replay',{'events_to_replay':3},{'events_to_replay':len(remaining),'balance':rebuilt},'A snapshot plus its following events reconstructs the same state with less replay.','A snapshot must match an event position; it does not replace the authoritative event history.')



    write_model={'balance':1000,'version':1};read_model={'display_balance':1000,'position_version':1};pending_events=[]
    def command_handler(credit):
        assert credit>0
        write_model['balance']+=credit;write_model['version']+=1
        pending_events.append({'amount':credit,'version':write_model['version']})
    def query_handler():return dict(read_model)
    command_handler(100)
    before_query=query_handler()
    for event in pending_events:
        read_model['display_balance']+=event['amount'];read_model['position_version']=event['version']
    after_query=query_handler()
    yield record('cqrs-handlers',{'write_balance':write_model['balance'],'query_balance':before_query['display_balance'],'query_version':before_query['position_version']},{'write_balance':write_model['balance'],'query_balance':after_query['display_balance'],'query_version':after_query['position_version'],'query_contract':'display_balance,position_version'},'A command handler validates and updates the write model; a query handler reads a separate projection contract, which advances by events.','The models share one process and memory. CQRS does not imply a broker, another database or Event Sourcing.')

def storage_partitions():
    rows=[{'key':i,'amount':i*10} for i in range(1,13)]
    shards={i:[] for i in range(3)}
    for row in rows:
        shards[row['key']%3].append(row)
    yield record('shard-route',{'partitions_scanned':3},{'partitions_scanned':1,'row_7_amount':next(r['amount'] for r in shards[7%3] if r['key']==7)},'A stable key and routing rule direct a lookup to its owning shard.','Python modulo is not consistent hashing and reassigns keys when the shard count changes.')
    amounts={'A':100,'B':200}; child_counts={'A':2,'B':3}
    naive=sum(amounts[key]*child_counts[key] for key in amounts)
    yield record('grain-join',{'sum_after_one_to_many_join':naive},{'sum_at_account_grain':sum(amounts.values())},'Aggregating children at the intended grain avoids multiplying the monetary value.','A unique key before a join does not prove uniqueness afterwards.')
    ring=lambda key,n: int(hashlib.sha256(key.encode()).hexdigest(),16)%n
    moved=sum(ring(str(i),3)!=ring(str(i),4) for i in range(100))
    yield record('hash-remap',{'shards':3,'moved_keys':0},{'shards':4,'modulo_moved_keys':moved},'Adding a modulo shard can move many key owners; a consistent ring aims to limit remapping.','This quantifies the baseline; it does not implement a production ring, virtual nodes or rebalance.')
    with tempfile.TemporaryDirectory(prefix='index-') as directory:
        db=sqlite3.connect(Path(directory)/'lab.sqlite')
        db.execute('CREATE TABLE position(account_key TEXT, cents INTEGER)')
        db.executemany('INSERT INTO position VALUES (?,?)',[(f'SYNTHETIC-{i}',i*100) for i in range(1000)])
        before=db.execute('EXPLAIN QUERY PLAN SELECT cents FROM position WHERE account_key=?',('SYNTHETIC-7',)).fetchone()[3]
        db.execute('CREATE INDEX position_lookup ON position(account_key,cents)')
        after=db.execute('EXPLAIN QUERY PLAN SELECT cents FROM position WHERE account_key=?',('SYNTHETIC-7',)).fetchone()[3]
        db.close()
    yield record('covering-index',{'query_plan':before},{'query_plan':after},'The lookup changes from scanning to an index that includes the selected value.','SQLite plan wording and index behavior do not establish a PostgreSQL query plan.')



    def ring_owner(key,nodes):
        points=sorted((int(hashlib.sha256(f'{node}-{replica}'.encode()).hexdigest(),16),node) for node in nodes for replica in range(16))
        position=bisect.bisect_left([point for point,_ in points],int(hashlib.sha256(key.encode()).hexdigest(),16))%len(points)
        return points[position][1]
    keys=[str(i) for i in range(100)]
    ring_moves=sum(ring_owner(key,['A','B','C'])!=ring_owner(key,['A','B','C','D']) for key in keys)
    yield record('consistent-ring',{'modulo_moved_keys':moved,'keys':100},{'ring_moved_keys':ring_moves,'keys':len(keys),'existing_owner_kept':len(keys)-ring_moves},'A hash ring assigns a key to its next virtual-node owner; adding D moves only the keys whose next owner becomes D.','The finite ring has 16 virtual points per node and does not implement replication or live rebalance.')

def safe_release():
    old={'amount':1000}; new={'amount_cents':100000}
    compatible={**old,**new}
    yield record('expand-contract',{'old_reader_value':new.get('amount')},{'old_reader_value':compatible['amount'],'new_reader_value':compatible['amount_cents']},'Expanding first keeps the old field while the new reader learns the new field.','Removing the old field requires evidence that old readers have retired.')
    traffic=list(range(100)); canary=[i for i in traffic if i<5]
    yield record('progressive-route',{'new_version_exposure':100},{'new_version_exposure':len(canary),'rollback_route':'old'},'A controlled route limits the first new-version population and can redirect it.','Synthetic exposure counts do not prove Kubernetes readiness or rollback of incompatible data.')
    primary=lambda amount: amount
    shadow=lambda amount: amount*100
    comparisons=[primary(10),shadow(10)]
    yield record('shadow-parity',{'silent_new_result':shadow(10)},{'visible_primary':comparisons[0],'shadow_mismatch':comparisons[0]!=comparisons[1]},'A shadow computation compares results while the primary owns the user-visible effect.','Both implementations must avoid duplicate writes; this probe uses pure functions.')
    desired={'image':'v2','replicas':2};actual={'image':'v1','replicas':1}
    actual.update(desired)
    yield record('desired-state',{'actual':{'image':'v1','replicas':1}},{'reconciled':actual},'A reconciler compares declared state with observed state before applying a change.','A dict update is a model of reconciliation, not GitOps, Terraform or immutable infrastructure deployment.')



    users=['USER-0','USER-1','USER-2','USER-3']
    before_responses=[{'user':user,'cohort':'A','fee':1} for user in users]
    responses=[{'user':user,'cohort':'A' if i%2==0 else 'B','fee':1 if i%2==0 else 2} for i,user in enumerate(users)]
    yield record('ab-cohorts',{'visible_cohorts':sorted({r['cohort'] for r in before_responses}),'fees':[r['fee'] for r in before_responses]},{'visible_cohorts':sorted({r['cohort'] for r in responses}),'fees':[r['fee'] for r in responses],'assignment_stable':all(r['user']==users[i] for i,r in enumerate(responses))},'Both A and B are user-visible treatments assigned to distinct stable cohorts.','This demonstrates cohort routing; experiment design, significance and rollout controls are not implemented.')

def access_policy():
    user={'role':'advisor','tenant':'A','account':'SYNTHETIC-1'}
    resource={'tenant':'B','account':'SYNTHETIC-2'}
    before=user['role']=='advisor'
    after=before and user['tenant']==resource['tenant'] and user['account']==resource['account']
    yield record('object-authorization',{'cross_tenant_allowed':before},{'cross_tenant_allowed':after},'Role, attributes and ownership must be checked against the specific resource.','No live roles, customer records or Faz permission contracts are inferred.')
    token={'subject':'synthetic-service','audience':'position-api','expires':10,'key_id':'old'}
    now=11
    yield record('credential-boundary',{'expired_token_accepted':True},{'accepted':token['expires']>now and token['audience']=='order-api'},'Expiration and audience constrain where and when a credential is accepted.','Claims are unsigned in this model; it does not implement OAuth2, OIDC, mTLS or key verification.')
    active_keys={'new'}
    yield record('rotate-key',{'old_key_accepted':token['key_id'] in {'old','new'}},{'old_key_accepted':token['key_id'] in active_keys},'Retiring a key makes a credential issued by that key inadmissible to this verifier.','Real rotation needs verified signatures, overlap windows and dependent-service rollout.')
    edges={('gateway','order-api'),('order-api','ledger')}
    yield record('least-network-path',{'direct_browser_ledger':True},{'direct_browser_ledger':('browser','ledger') in edges},'Explicit allowed edges reduce paths that bypass the application owner.','A set is a policy model, not a network firewall, bastion or service mesh.')


def diagnostics():
    spans=[{'request_id':'REQUEST-1','operation_id':'ORDER-1','stage':'gateway','duration_ms':10,'error':False},
           {'request_id':'REQUEST-1','operation_id':'ORDER-1','stage':'provider','duration_ms':800,'error':True},
           {'request_id':'REQUEST-2','operation_id':'ORDER-1','stage':'retry','duration_ms':20,'error':False}]
    related=[s for s in spans if s['operation_id']=='ORDER-1']
    yield record('correlate-retries',{'trace_one_request_spans':2},{'operation_spans':len(related),'requests':len({s['request_id'] for s in related})},'An operation identity relates two request attempts without confusing them.','A list of spans is not OpenTelemetry instrumentation or proof of cross-service context propagation.')
    requests={span['request_id'] for span in spans}
    failed_requests={span['request_id'] for span in spans if span['error']}
    errors=len(failed_requests); durations=sorted(s['duration_ms'] for s in spans)
    yield record('measure-signals',{'looks_healthy_from_average_only':True},{'spans':len(spans),'requests':len(requests),'operations':len({s['operation_id'] for s in spans}),'failed_requests':errors,'max_span_duration_ms':max(durations),'request_error_ratio':round(errors/len(requests),3),'observation_window_seconds':1,'request_rate_per_second':len(requests)/1},'Rate, errors and duration expose a slow failed dependency hidden by a vague status.','This sample cannot establish percentiles, an SLO or production capacity.')
    def health():return 'ok'
    def failed_provider():raise RuntimeError('controlled provider failure')
    def synthetic_order():
        try:failed_provider()
        except RuntimeError:return 'provider_failed'
        return 'completed'
    yield record('probe-business-path',{'health_endpoint':health(),'order_path':'unmeasured'},{'health_endpoint':health(),'synthetic_order':synthetic_order()},'A synthetic business-path check can fail while the process health endpoint stays green.','Only a controlled synthetic path ran; no real order is sent.')

CASES={name.replace('_','-'):value for name,value in list(globals().items()) if callable(value) and name in ['order_boundaries','order_delivery','reservation','consensus','queue_workflow','cache_policy','ledger_projection','storage_partitions','safe_release','access_policy','diagnostics']}


BASE_CASES=CASES

def execute_case(case):
    yield from BASE_CASES[case]()
    for observation in for_case(case):
        yield record(observation['probe'],observation['before'],observation['after'],observation['guarantee'],observation['limit'])

CASES={name:(lambda case=name:execute_case(case)) for name in BASE_CASES}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('case',choices=sorted(CASES))
    parser.add_argument('--probe')
    args=parser.parse_args()
    results=list(CASES[args.case]())
    if args.probe:
        results=[item for item in results if item['probe']==args.probe]
        if not results:
            raise SystemExit('unknown probe')
    for item in results:
        print(json.dumps(item,ensure_ascii=False,sort_keys=True))
    print(f'comparison=PASS case={args.case} probes={len(results)} inputs=SYNTHETIC runtime=LOCAL')

if __name__=='__main__':
    main()
