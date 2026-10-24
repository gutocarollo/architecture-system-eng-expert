"""Deterministic concurrency schedules with explicit atomic-model boundaries."""
import asyncio
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor


def item(probe,names,before,after,action,guarantee,limit):
    return dict(case='reservation',probe=probe,names=names,before=before,after=after,action=action,guarantee=guarantee,limit=limit)


def observations():
    async def bounded():
        gate=asyncio.Semaphore(2);state={'active':0,'maximum':0,'completed':0}
        async def work():
            async with gate:
                state['active']+=1;state['maximum']=max(state['maximum'],state['active'])
                await asyncio.sleep(0)
                state['active']-=1;state['completed']+=1
        await asyncio.gather(*(work() for _ in range(4)))
        return state
    bounded_state=asyncio.run(bounded())
    yield item('semaphore-permits',['Semaphore'],{'unbounded_simultaneous_tasks':4},{'maximum_simultaneous_tasks':bounded_state['maximum'],'completed':bounded_state['completed'],'active_at_end':bounded_state['active']},'Execute quatro tarefas que cedem a execução enquanto seguram a permissão. Confira no máximo duas dentro da seção e quatro conclusões.','A real asyncio semaphore bounds concurrent entry to two and releases its permits after each task.','The semaphore is local to this event loop and does not limit the producer buffer or sum capacity across processes.')
    barrier=threading.Barrier(2)
    def pool_task(value):barrier.wait(timeout=3);return threading.get_ident(),value*2
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(pool_task,[1,2,3,4]))
    ids={ident for ident,_ in results};partials=[value for _,value in results]
    yield item('reused-thread-workers',['Thread Pool','Worker Pool','Fork/Join','Scatter/Gather'],{'new_worker_per_task':4},{'threads_used':len(ids),'tasks_completed':len(results),'partials':partials,'joined_total':sum(partials)},'Submeta quatro tarefas a duas threads reutilizadas, aguarde as respostas e reúna os resultados parciais. Confira a quantidade de executores e o total composto.','The executor reuses two workers, forks four computations and joins their four results into one total.','No process pool, distributed worker, work durability or network scatter/gather is claimed.')
    queues={'A':deque([1,2]),'B':deque()};executed={'A':[],'B':[]}
    stolen=queues['A'].pop();executed['B'].append(stolen)
    while queues['A']:executed['A'].append(queues['A'].popleft())
    yield item('idle-worker-steal',['Work Stealing'],{'idle_B_completed':0,'A_remaining_work':2},{'A_completed':executed['A'],'B_completed':executed['B'],'unique_completed':len(set(executed['A']+executed['B']))},'Deixe B ocioso enquanto A tem duas tarefas. Faça B retirar uma tarefa elegível da outra ponta da fila de A e confira uma execução de cada tarefa.','An idle worker steals eligible queued work from another worker while task ownership changes exactly once in this schedule.','The deques are manipulated sequentially; a real concurrent deque requires its own atomicity and memory-order guarantees.')
    class ReaderWriter:
        def __init__(self):self.readers=0;self.writer=False
        def read(self):
            if self.writer:return False
            self.readers+=1;return True
        def write(self):
            if self.writer or self.readers:return False
            self.writer=True;return True
    rw=ReaderWriter();both_read=[rw.read(),rw.read()];blocked=not rw.write();rw.readers-=2;writer_acquired=rw.write();reader_blocked=not rw.read()
    yield item('reader-writer-exclusion',['Reader/Writer Lock'],{'uncoordinated_writer_during_two_reads':True},{'simultaneous_readers':sum(both_read),'writer_blocked_during_reads':blocked,'writer_acquired_after_release':writer_acquired,'reader_blocked_during_write':reader_blocked},'Adquira duas leituras, tente a escrita, libere as leituras e depois tente ler durante a escrita. Confira as duas formas diferentes de exclusão.','Concurrent readers are compatible with each other and incompatible with an exclusive writer in the finite state model.','This is a serialized lock-state schedule, not a thread-safe RWLock implementation or a fairness proof.')
    lock={'held':True};attempts=0;acquired=False
    for turn in range(5):
        attempts+=1
        if not lock['held']:lock['held']=True;acquired=True;break
        if turn==2:lock['held']=False
    yield item('spinlock-active-attempts',['Spinlock'],{'owner_paused_initially_held':True},{'active_attempts':attempts,'acquired_after_scheduled_release':acquired,'blocking_sleep_calls':0},'Execute tentativas ativas enquanto a trava está ocupada e programe sua liberação depois da terceira tentativa. Conte quatro tentativas até a aquisição.','The contender repeatedly tests the lock state without blocking, consuming execution steps while the owner is paused.','The model uses serialized test-and-set steps, not a hardware spinlock, CPU benchmark or permission to spin while waiting for HTTP.')
    counter=[0];completed={'A':0,'B':0}
    def cas(expected,new):
        if counter[0]!=expected:return False
        counter[0]=new;return True
    a_read,b_read=counter[0],counter[0]
    if cas(a_read,a_read+1):completed['A']+=1
    b_retry_needed=not cas(b_read,b_read+1)
    if cas(counter[0],counter[0]+1):completed['A']+=1
    yield item('cas-system-progress',['Lock-Free'],{'mutex_owner_paused_blocks_all':True},{'counter':counter[0],'A_completed':completed['A'],'B_completed':completed['B'],'B_retry_needed':b_retry_needed},'Faça A e B lerem o mesmo contador, deixe A ganhar o CAS e pause B depois de sua falha. Confira que A ainda consegue concluir outra operação.','The CAS retry pattern permits system progress while one contender stalls; this schedule also shows why that is not a per-thread bounded completion guarantee.','The CAS primitive is atomic by model assumption. This is a concrete progress/starvation schedule, not a universal proof for a native-memory implementation.')
    class Spsc:
        def __init__(self):self.slots=[None,None];self.head=0;self.tail=0
        def put(self,value):
            steps=2
            if self.tail-self.head==len(self.slots):return False,steps
            self.slots[self.tail%len(self.slots)]=value;self.tail+=1
            return True,steps+2
        def take(self):
            steps=2
            if self.head==self.tail:return None,steps
            value=self.slots[self.head%len(self.slots)];self.head+=1
            return value,steps+2
    q=Spsc();puts=[q.put(10),q.put(20),q.put(30)];takes=[q.take(),q.take(),q.take()]
    yield item('bounded-spsc-steps',['Wait-Free'],{'retry_loop_steps_have_no_per_operation_bound':True},{'put_results':[ok for ok,_ in puts],'take_values':[value for value,_ in takes],'maximum_steps':max(steps for _,steps in puts+takes)},'Preencha a fila SPSC de duas posições, tente a terceira inclusão e faça três retiradas. Confira que até a recusa por cheia e o resultado vazio terminam em até quatro passos do modelo.','With one producer, one consumer and atomic ordered index publication, each straight-line operation returns success/full/empty in at most four modeled steps without a retry loop.','The bounded-step argument belongs to this SPSC atomic-index model; Python execution time, allocation, native memory ordering and multiple producers are not covered.')
    class Subscription:
        def __init__(self,values):self.values=deque(values);self.demand=0;self.received=[];self.cancelled=False
        def request(self,n):
            if n<=0:raise ValueError('positive demand')
            self.demand+=n
            while self.demand and self.values and not self.cancelled:self.received.append(self.values.popleft());self.demand-=1
        def cancel(self):self.cancelled=True
    subscription=Subscription([1,2,3,4]);initial=len(subscription.received);subscription.request(2);first=list(subscription.received);subscription.request(1);subscription.cancel();subscription.request(10)
    yield item('reactive-demand-contract',['Reactive Streams'],{'unrequested_push_count':4},{'delivered_before_request':initial,'after_request_two':first,'delivered_after_request_three_and_cancel':subscription.received,'unconsumed':len(subscription.values)},'Solicite dois elementos e depois mais um. Cancele antes do quarto e confira que uma solicitação posterior não reativa a assinatura cancelada.','Demand gates delivery and cancellation stops subsequent onNext-style emissions in this local publisher/subscriber contract.','No Reactive Streams library, asynchronous serialization rule or full TCK conformance is claimed.')
