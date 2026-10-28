"""Bounded protocol and storage observations, not production protocol implementations."""
import sqlite3
import tempfile
from pathlib import Path
from copy import deepcopy


def item(case,probe,names,before,after,action,guarantee,limit):
    return dict(case=case,probe=probe,names=names,before=before,after=after,action=action,guarantee=guarantee,limit=limit)


def observations():
    accepted={'A':(7,'ORDER-A'),'B':(7,'ORDER-A'),'C':None};promised={node:7 for node in accepted}
    replies=[]
    for node in ['A','B']:
        if 8>promised[node]:promised[node]=8;replies.append(accepted[node])
    carried=max((reply for reply in replies if reply),key=lambda pair:pair[0])[1]
    for node in ['A','B']:accepted[node]=(8,carried)
    yield item('consensus','paxos-accepted-carry',['Paxos'],{'new_round_proposal':'ORDER-B','would_replace_chosen_value':True},{'new_round_proposal':carried,'accepted_nodes':sum(value==(8,'ORDER-A') for value in accepted.values()),'ballot':8},'Prepare a rodada 8 em dois acceptors que já aceitaram ORDER-A na rodada 7. Proponha ORDER-B e confira por que o novo proposer precisa carregar o valor previamente aceito.','A prepare quorum reports accepted values; the proposer carries the value at the highest accepted ballot rather than inventing a different value.','A finite single-decree Paxos schedule with reliable local messages; persistence, liveness and arbitrary faults are not implemented.')
    follower=[(1,'A'),(2,'B')];leader=[(1,'A'),(3,'D'),(3,'E')]
    def append(log,previous_index,previous_term,entries):
        if previous_index>len(log) or (previous_index and log[previous_index-1][0]!=previous_term):return False
        del log[previous_index:];log.extend(entries);return True
    rejected=not append(follower,2,3,[(3,'E')]);length_after_reject=len(follower)
    retried=append(follower,1,1,leader[1:])
    yield item('consensus','raft-log-prefix',['Raft'],{'blind_append_accepts_mismatched_prefix':True},{'mismatched_prefix_rejected':rejected,'length_after_rejection':length_after_reject,'retry_accepted':retried,'matches_leader':follower==leader,'log_terms':[term for term,_ in follower]},'Envie AppendEntries com prevLogIndex=2 e prevLogTerm=3 para uma réplica cujo termo no índice 2 é 2. Confira a recusa e a repetição a partir do prefixo comum.','The follower checks the previous index/term before appending; a retry from a matching prefix replaces conflicting suffix entries.','This isolates Raft log matching, without election, durable storage, commitment or a complete replicated state machine.')
    voters={node:{'term':2,'voted_for':None} for node in ['A','B','C']}
    def vote(node,candidate,term):
        state=voters[node]
        if term<state['term'] or (state['term']==term and state['voted_for'] not in [None,candidate]):return False
        state.update(term=term,voted_for=candidate);return True
    a_votes=sum(vote(node,'A',2) for node in ['A','B']);c_votes=sum(vote(node,'C',2) for node in ['B','C'])
    yield item('consensus','election-one-vote',['Leader Election'],{'candidates_with_unrestricted_votes':2},{'A_votes':a_votes,'C_votes':c_votes,'elected_candidates':sum(count>=2 for count in [a_votes,c_votes]),'B_voted_for':voters['B']['voted_for']},'Faça B votar em A no termo 2 e depois receber C no mesmo termo. Confira que B não vota nos dois candidatos e que só A reúne a maioria.','A voter remembers its vote in the term and refuses a second different candidate in that term.','The fixture does not implement log freshness, randomized timeouts, persistence or all election transitions.')
    lease={'owner':'A','expires':5};clock=6
    acquired=clock>=lease['expires']
    if acquired:lease.update(owner='B',expires=clock+5)
    old_release=lease['owner']=='A'
    yield item('reservation','lease-expiry-owner',['Lease'],{'B_can_acquire_unexpired_static_lock':False},{'B_acquired_after_expiry':acquired,'owner':lease['owner'],'old_owner_release_allowed':old_release,'expires':lease['expires']},'Avance o relógio além da validade de A, deixe B adquirir a autorização e tente liberar a lease com a identidade antiga de A.','Expiry makes the abandoned authorization reclaimable, while owner comparison prevents an old owner from releasing the new lease.','The model uses a controlled clock; expiration is not destination fencing and does not stop an old external side effect.')
    with tempfile.TemporaryDirectory(prefix='shared-claim-') as directory:
        path=Path(directory)/'coordination.sqlite';a=sqlite3.connect(path);b=sqlite3.connect(path)
        a.execute('CREATE TABLE claims(resource_key TEXT PRIMARY KEY,owner TEXT)');a.commit()
        a.execute('INSERT INTO claims VALUES (?,?)',('ORDER-1','A'));a.commit()
        try:b.execute('INSERT INTO claims VALUES (?,?)',('ORDER-1','B'));b.commit();second_allowed=True
        except sqlite3.IntegrityError:b.rollback();second_allowed=False
        old_release=b.execute('DELETE FROM claims WHERE resource_key=? AND owner=?',('ORDER-1','B')).rowcount;b.commit()
        rows=a.execute('SELECT count(*) FROM claims').fetchone()[0];a.close();b.close()
    yield item('reservation','shared-arbiter-lock',['Distributed Lock'],{'independent_local_locks_allow_both':True},{'second_connection_allowed':second_allowed,'wrong_owner_deleted_rows':old_release,'held_claims':rows},'Use duas conexões independentes ao mesmo coordenador SQLite. Dispute a chave ORDER-1 e tente liberar a chave com o dono errado.','Both participants use one atomic unique-key arbiter instead of independent local locks; ownership is checked at release.','SQLite is local to this machine. The experiment proves shared-arbiter coordination, not a networked lease service under partitions.')
    with tempfile.TemporaryDirectory(prefix='pessimistic-') as directory:
        path=Path(directory)/'ledger.sqlite';a=sqlite3.connect(path,timeout=0);b=sqlite3.connect(path,timeout=0)
        a.execute('CREATE TABLE balance(cents INTEGER)');a.execute('INSERT INTO balance VALUES (100000)');a.commit()
        a.execute('BEGIN IMMEDIATE');a.execute('UPDATE balance SET cents=cents+10000')
        try:b.execute('BEGIN IMMEDIATE');blocked=False
        except sqlite3.OperationalError:blocked=True
        a.commit();b.execute('BEGIN IMMEDIATE');b.execute('UPDATE balance SET cents=cents+5000');b.commit()
        final=b.execute('SELECT cents FROM balance').fetchone()[0];a.close();b.close()
    yield item('reservation','pessimistic-writer-lock',['Pessimistic Locking'],{'uncoordinated_stale_balance':105000},{'second_writer_blocked_before_release':blocked,'balance_after_serial_writes':final},'Mantenha BEGIN IMMEDIATE aberto no primeiro escritor. Confira a recusa imediata da segunda conexão, finalize a primeira e repita a segunda escrita.','The writer obtains exclusion before changing the record; the second writer cannot begin its write transaction until release.','This is SQLite database-writer exclusion, not PostgreSQL row locking or a recommendation to hold locks during network calls.')
    cash,units=1000,1;held={'cash':100,'units':1,'state':'trying'}
    cash-=held['cash'];units-=held['units'];held['state']='prepared'
    cancelled_cash,cancelled_units=cash+held['cash'],units+held['units']
    held['state']='confirmed';confirmed={'cash':cash,'units':units,'state':held['state']}
    yield item('order-delivery','tcc-resource-states',['TCC — Try/Confirm/Cancel'],{'immediate_debit_after_peer_refusal':900},{'cancelled_cash':cancelled_cash,'cancelled_units':cancelled_units,'confirmed':confirmed},'Reserve dinheiro e unidade na fase Try. Siga uma cópia pela confirmação e outra pelo cancelamento; confira quais recursos ficam disponíveis em cada caminho.','Try holds resources; Confirm consumes the hold, while Cancel releases the same held resources.','The two local outcomes model one reservation contract; distributed recovery, timeout races and idempotent callbacks remain separate obligations.')
    phases=['canCommit','preCommit'];participants={'A':'waiting','B':'waiting'}
    for phase in phases:
        for node in participants:participants[node]=phase
    all_precommitted=all(state=='preCommit' for state in participants.values())
    decision='commit' if all_precommitted else 'wait'
    yield item('consensus','three-phase-precommit',['Three-Phase Commit / 3PC'],{'two_phase_prepared_timeout':'wait_for_coordinator'},{'phases_before_timeout':phases,'all_precommitted':all_precommitted,'decision_under_synchronous_no_partition_assumption':decision,'decision_if_partition_possible':'wait'},'Faça os dois participantes reconhecerem canCommit e preCommit. Compare a decisão no modelo síncrono declarado com o caso em que uma partição ainda é possível.','The extra precommit state distinguishes the modeled 3PC decision from an uncertain 2PC prepare, under the explicit timing and no-partition assumptions.','This is not a partition-tolerant atomic commit implementation; the autonomous commit decision is not generalized outside those assumptions.')
    deliveries=[True,True];retry_effects=sum(deliveries)
    once_ack_lost=int(deliveries[0]);once_delivery_lost=int(False)
    yield item('order-delivery','at-most-once-loss',['At-Most-Once Delivery'],{'retry_without_dedup_effects':retry_effects},{'ack_lost_effects_without_retry':once_ack_lost,'delivery_lost_effects_without_retry':once_delivery_lost,'maximum_attempts':1},'Perdida a confirmação, compare repetir sem deduplicação com fazer somente uma tentativa. Depois perca a própria entrega e observe que nenhuma tentativa adicional a recupera.','At most one attempt avoids repeat delivery in this fixture but can lose the operation entirely.','This is a sender-attempt model, not a broker delivery guarantee or proof of the external effect.')
    physical=1005;local=(1006,1);remote=(1010,3);wall=max(physical,local[0],remote[0])
    logical=max(local[1],remote[1])+1 if wall==local[0]==remote[0] else (remote[1]+1 if wall==remote[0] else local[1]+1 if wall==local[0] else 0)
    yield item('consensus','hybrid-clock-receive',['Hybrid Logical Clock'],{'naive_physical_receive_time':physical},{'hybrid_wall':wall,'hybrid_logical':logical,'causal_order_preserved':(wall,logical)>remote},'Receba o evento 1010:3 com relógio físico em 1005 e relógio local em 1006:1. Confira a parte física máxima e o contador lógico que conserva a ordem causal.','The receive rule combines the physical maximum with a logical counter when the received wall component wins.','The one receive schedule does not synchronize physical clocks or prove a distributed implementation under every skew pattern.')
    with tempfile.TemporaryDirectory(prefix='cdc-') as directory:
        db=sqlite3.connect(Path(directory)/'source.sqlite')
        db.executescript('CREATE TABLE source(account_key TEXT PRIMARY KEY,cents INTEGER); CREATE TABLE changes(sequence INTEGER PRIMARY KEY AUTOINCREMENT,account_key TEXT,cents INTEGER); CREATE TRIGGER capture_update AFTER UPDATE ON source BEGIN INSERT INTO changes(account_key,cents) VALUES (NEW.account_key,NEW.cents); END;')
        db.execute('INSERT INTO source VALUES (?,?)',('SYNTHETIC-1',100000));db.commit()
        db.execute('UPDATE source SET cents=999');db.rollback()
        rolled_back_changes=db.execute('SELECT count(*) FROM changes').fetchone()[0]
        db.execute('UPDATE source SET cents=110000');db.commit()
        rows=db.execute('SELECT sequence,account_key,cents FROM changes WHERE sequence>0 ORDER BY sequence').fetchall()
        target={key:cents for _,key,cents in rows};db.close()
    yield item('order-delivery','cdc-committed-change',['Change Data Capture (CDC)','CDC Migration','Dual Write Migration'],{'independent_target_cents_after_second_write_failure':100000},{'captured_committed_changes':len(rows),'rolled_back_changes':rolled_back_changes,'target_cents':target['SYNTHETIC-1']},'Atualize a origem dentro de uma transação que faz rollback e depois numa que faz commit. Leia o feed capturado e aplique o valor no destino da migração.','A database trigger captures only the committed after-image visible to the feed reader, allowing a destination to catch up instead of relying on a second independent application write.','Trigger-based CDC in SQLite is not WAL decoding, Debezium or a cross-database atomic transaction; cutover still requires reconciliation.')
    with tempfile.TemporaryDirectory(prefix='outbox-cdc-') as directory:
        db=sqlite3.connect(Path(directory)/'source.sqlite')
        db.executescript('CREATE TABLE orders(order_key TEXT PRIMARY KEY); CREATE TABLE outbox(event_key TEXT PRIMARY KEY); CREATE TABLE feed(sequence INTEGER PRIMARY KEY AUTOINCREMENT,event_key TEXT); CREATE TRIGGER capture_outbox AFTER INSERT ON outbox BEGIN INSERT INTO feed(event_key) VALUES (NEW.event_key); END;')
        with db:db.execute('INSERT INTO orders VALUES (?)',('ORDER-1',));db.execute('INSERT INTO outbox VALUES (?)',('EVENT-1',))
        feed=db.execute('SELECT sequence,event_key FROM feed WHERE sequence>0').fetchall();db.close()
    yield item('order-delivery','outbox-cdc-feed',['Outbox + CDC'],{'order_saved_external_delivery_intention_lost':True},{'captured_outbox_events':[key for _,key in feed],'resume_after_sequence':feed[-1][0]},'Grave a ordem e a outbox na mesma transação e acompanhe o capturador da outbox gerar EVENT-1 no feed com uma posição de retomada.','The transactional outbox is the captured table, and its committed insert becomes the CDC feed item.','The learning connector is a SQLite trigger plus feed query; transport, source-log offsets and recipient deduplication are not implemented.')
    primary={'version':2};replica={'version':1};ack_before=True
    sync_ack=replica['version']>=primary['version'];replica.update(primary);ack_after=replica['version']>=primary['version']
    yield item('consensus','synchronous-replica-ack',['Synchronous Replication'],{'writer_ack_before_replica_applied':ack_before},{'ack_while_replica_behind':sync_ack,'ack_after_replica_applied':ack_after,'read_version_after_ack':replica['version']},'Mantenha a réplica na versão 1 enquanto o primário está na 2. Confira que a confirmação sincronizada espera a aplicação e que a leitura dessa réplica após a confirmação vê a versão 2.','The writer acknowledgement is ordered after this replica applies the write, providing the tested after-ack visibility property.','This bounded primary/replica schedule does not alone prove linearizability, all replica routing or consistency under partitions.')
    a,b,c={'version':2},{'version':1},{'version':1}
    before_c=c['version'];b.update(a);c.update(b)
    yield item('consensus','cascading-replication',['Cascading Replication'],{'C_before_B_relay':before_c},{'A_version':a['version'],'B_version':b['version'],'C_version':c['version'],'C_source':'B'},'Aplique a versão de A em B e só depois replique B em C. Observe que C depende do intermediário, em vez de consultar diretamente A.','Replication follows A to B to C, exposing the intermediate replica as the source of the final replica.','The model has one ordered update, no WAL streams, failover or network delay.')
    writes={'A':[('CREDIT-A',100)],'B':[('CREDIT-B',50)]};merged={key:value for events in writes.values() for key,value in events}
    site_balances={site:1000+sum(v for _,v in events) for site,events in writes.items()}
    yield item('consensus','multi-writer-reconcile',['Active/Active','Multi-Leader','Multi-Primary'],{'last_absolute_balance_wins':site_balances['B'],'lost_credit':100},{'sites_accepting_writes':len(writes),'merged_balance':1000+sum(merged.values()),'unique_credits':len(merged)},'Aceite um crédito distinto em A e B. Compare a última substituição absoluta de saldo com a reconciliação das identidades dos dois créditos.','Both sites accept writes and reconciliation preserves distinct additive credits instead of choosing one absolute snapshot.','This merge is valid only for the declared independent credits; noncommutative debits and invariants need a business conflict policy.')
    source={'balance':1000};alias=source;alias['balance']=1100
    original={'balance':1000};copied=dict(original);copied['balance']=1100
    yield item('reservation','copy-on-write-snapshot',['Copy-on-Write'],{'reader_original_after_shared_mutation':source['balance']},{'reader_original':original['balance'],'writer_new_copy':copied['balance'],'different_objects':original is not copied},'Mantenha um leitor com o snapshot anterior, copie antes da escrita e altere a nova cópia. Confira que o leitor continua em 1.000 enquanto a cópia chega a 1.100.','A writer changes a new copy instead of mutating the snapshot held by the old reader.','The fixture is a flat dictionary; deep object graphs, memory reclamation and lock-free publication require additional contracts.')
    directory={'SYNTHETIC-7':'B'};shards={'A':{},'B':{'SYNTHETIC-7':700}}
    owner=directory['SYNTHETIC-7'];value=shards[owner]['SYNTHETIC-7']
    yield item('storage-partitions','directory-shard',['Directory-Based Sharding'],{'lookup_in_default_A':shards['A'].get('SYNTHETIC-7')},{'directory_owner':owner,'value':value},'Mude a localização da chave 7 para B no diretório e resolva o dono antes de consultar. Confira que adivinhar A não encontra a posição.','An explicit directory maps an entity key to its owning shard, independently of a hash function.','Directory durability, stale entries and live moves are not modeled.')
    boundaries=[(0,100),(100,200)];key=100;owners=[index for index,(lo,hi) in enumerate(boundaries) if lo<=key<hi]
    yield item('storage-partitions','range-boundary',['Range Sharding'],{'inclusive_upper_boundary_owners':[0,1]},{'half_open_boundary_owners':owners,'key':key},'Procure a chave 100 nos intervalos 0 até antes de 100 e 100 até antes de 200. Confira que a borda pertence a um único shard.','Half-open ranges assign the boundary key to exactly one shard rather than overlapping owners.','Range balancing, splits and hotspot control are separate concerns.')
    account={'key':'SYNTHETIC-1','region':'BR'};regions={'BR':{},'US':{}};regions[account['region']][account['key']]=1000
    yield item('storage-partitions','geographic-owner',['Geographic Sharding'],{'all_accounts_owner':'US'},{'account_region':account['region'],'BR_rows':len(regions['BR']),'US_rows':len(regions['US'])},'Use a região declarada da conta fictícia para escolher a partição e confira onde seu valor foi guardado.','A geographic attribute chooses the data owner rather than a key hash.','The geography is hypothetical and is not a claim about a regulatory residency rule.')
    wide={'account_key':'SYNTHETIC-1','contact_label':'Synthetic contact','cents':100000};contact={k:v for k,v in wide.items() if k in ['account_key','contact_label']};position={k:v for k,v in wide.items() if k in ['account_key','cents']}
    joined={**contact,**position}
    yield item('storage-partitions','vertical-attributes',['Vertical Partitioning'],{'position_read_columns':sorted(wide)},{'position_read_columns':sorted(position),'contact_columns':sorted(contact),'rejoin_preserves_row':joined==wide},'Separe os atributos de contato dos atributos de posição pela mesma chave. Confira quais colunas a consulta de posição precisa ler e reuna a linha somente quando necessário.','Vertical partitions divide attributes while preserving the key needed to reconstruct the logical entity.','The example models attribute ownership and does not measure physical page savings or authorization by itself.')
    log=[]
    for version,value in enumerate([1000,1100],1):log.append({'key':'A','version':version,'value':value})
    latest=max((entry for entry in log if entry['key']=='A'),key=lambda e:e['version'])
    yield item('storage-partitions','log-structured-latest',['Log Structured Storage'],{'in_place_record_history':1},{'append_records':len(log),'latest_value':latest['value'],'latest_version':latest['version']},'Acrescente a nova versão em vez de sobrescrever a antiga e resolva a leitura pelo registro mais recente da chave.','Updates append records and reads resolve the latest version, exposing the read/compaction work introduced by a log-structured representation.','This is a tiny append-log model, not an LSM tree with SSTables, bloom filters or crash recovery.')
    updates=[('POSITION-A',1000+i) for i in range(10)];batch={}
    for key,value in updates:batch[key]=value
    yield item('storage-partitions','coalesced-snapshot-writes',['Write Amplification Control'],{'physical_snapshot_writes':len(updates)},{'physical_batch_writes':len(batch),'latest_snapshot':batch['POSITION-A'],'updates_in_acknowledged_batch':len(updates)},'Agrupe dez substituições do mesmo snapshot de posição antes de confirmar o lote e grave o último valor uma vez. Compare as escritas físicas necessárias.','Coalescing repeated overwrites of one snapshot reduces physical writes before the batch acknowledgement.','This applies to replaceable snapshots, not ten independent ledger facts. No per-update durability is promised before the batch flush.')

    class SerializedOwner:
        def __init__(self):self.balance=1000;self.version=1;self.history=[]
        def write(self,amount):self.balance+=amount;self.version+=1;self.history.append(('write',self.version,self.balance))
        def read(self):self.history.append(('read',self.version,self.balance));return self.balance
    owner=SerializedOwner();initial=owner.read();owner.write(100);after_write=owner.read()
    yield item('consensus','owner-latest-read',['Strong Consistency'],{'read_from_uncoordinated_stale_replica_after_write':1000},{'read_before_write':initial,'read_after_completed_write':after_write,'latest_version':owner.version,'ordered_history':[list(event) for event in owner.history]},'Leia 1.000, conclua o crédito de 100 no dono serializado e faça outra leitura sem carregar um token de sessão. Confira a versão e a ordem das operações no histórico.','Every read in this single-owner schedule observes the latest preceding completed write, independently of a client session hint.','This is one serialized-owner history, not a universal linearizability proof or a distributed strong-consistency system under failures.')
    delivered=[];attempts=0
    def send_until_ack(retry):
        nonlocal attempts
        acknowledged=False
        while not acknowledged:
            attempts+=1;delivered.append('EVENT-1')
            acknowledged=attempts>1
            if not retry:break
        return acknowledged
    before_ack=send_until_ack(False);before_attempts=attempts;delivered.clear();attempts=0;after_ack=send_until_ack(True)
    yield item('order-delivery','at-least-once-ack-retry',['At-Least-Once Delivery'],{'acknowledged':before_ack,'attempts':before_attempts},{'acknowledged':after_ack,'attempts':attempts,'deliveries':len(delivered),'unique_event_ids':len(set(delivered))},'Entregue EVENT-1 e perca somente sua confirmação. Repita até receber a confirmação e conte as duas entregas da mesma identidade.','Retry after an ambiguous acknowledgement restores acknowledgement while admitting repeat delivery of the same event.','Only this bounded acknowledgement-loss schedule is modeled; an exactly-once effect still needs the recipient transaction or idempotency mechanism.')
