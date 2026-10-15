"""Applied domain exercises over explicit synthetic financial contracts."""
from dataclasses import dataclass
from copy import deepcopy


def item(probe,names,before,after,action,guarantee,limit):
    return dict(case='order-boundaries',probe=probe,names=names,before=before,after=after,action=action,guarantee=guarantee,limit=limit)


def observations():
    class Basket:
        def __init__(self,limit):self.limit=limit;self._amounts=[]
        def add(self,amount):
            if amount<=0 or sum(self._amounts)+amount>self.limit:raise ValueError('basket invariant')
            self._amounts.append(amount)
        @property
        def amounts(self):return tuple(self._amounts)
    bypassed=[50,80];basket=Basket(100);basket.add(50)
    try:basket.add(80);refused=False
    except ValueError:refused=True
    yield item('aggregate-root-invariant',['Aggregate','Aggregate Root'],{'bypassed_total':sum(bypassed),'exceeds_limit':sum(bypassed)>100},{'protected_total':sum(basket.amounts),'second_add_refused':refused,'public_children_are_tuple':isinstance(basket.amounts,tuple)},'Tente acrescentar 50 e 80 a uma cesta com limite 100. Compare a escrita direta dos filhos com a única entrada pública da raiz, que preserva o total válido.','The root owns the public mutation operation and checks the invariant spanning its children before accepting the next item.','The aggregate is in memory; Python private attributes are a convention and distributed transaction boundaries are not established.')
    @dataclass
    class Account:
        account_key:str
        balance:int
    source,target=Account('SOURCE',1000),Account('TARGET',0)
    class TransferService:
        def transfer(self,debit,credit,amount):
            if amount<=0 or debit.balance<amount:raise ValueError('invalid transfer')
            debit.balance-=amount;credit.balance+=amount
    TransferService().transfer(source,target,100)
    yield item('domain-service-transfer',['Domain Service'],{'credit_without_debit_total':1100},{'source_balance':source.balance,'target_balance':target.balance,'conserved_total':source.balance+target.balance},'Transfira 100 entre duas entidades pelo serviço de domínio e confira a conservação do total, em vez de creditar o destino isoladamente.','A domain operation involving two entities preserves the stated transfer invariant without belonging naturally to either entity alone.','Only an in-memory operation is executed; durable atomic transfer, fees and real financial rules are not claimed.')
    class Repository:
        def __init__(self,find,save):self._find=find;self._save=save
        def get(self,key):return Account(key,self._find(key))
        def save(self,account):self._save(account.account_key,account.balance)
    dict_store={'A':1000};row_store=[['A',1000]]
    a=Repository(dict_store.__getitem__,lambda key,value:dict_store.__setitem__(key,value))
    def find_row(key):return next(value for row_key,value in row_store if row_key==key)
    def save_row(key,value):
        for row in row_store:
            if row[0]==key:row[1]=value;return
    b=Repository(find_row,save_row)
    values=[]
    for repo in [a,b]:account=repo.get('A');account.balance+=100;repo.save(account);values.append(repo.get('A').balance)
    yield item('repository-storage-contract',['Repository'],{'domain_storage_shapes':['dictionary','row-list']},{'domain_account_type':type(a.get('A')).__name__,'balances_from_each_adapter':values},'Troque o armazenamento entre dicionário e lista de linhas mantendo get/save e a entidade Account usados pela operação. Confira 1.100 nas duas implementações.','The repository presents a domain collection contract while storage representation changes behind it.','The adapters are local fakes, without SQL mapping, identity maps or unit-of-work concurrency.')
    operations=[];app_account=Account('A',1000)
    def application_service(amount):
        operations.append('load')
        if amount<=0:operations.append('reject');return False
        operations.append('domain-credit');app_account.balance+=amount;operations.append('save');return True
    accepted=application_service(-100)
    yield item('application-service-order',['Application Service'],{'save_before_validation_calls':1},{'accepted':accepted,'operations':operations,'balance':app_account.balance,'save_calls':operations.count('save')},'Envie um comando inválido ao serviço de aplicação. Siga carregamento, validação e rejeição e confira que ele não manda persistir uma operação recusada.','The application service coordinates the use case and calls domain behavior before persistence instead of embedding a write before validation.','The ordering model does not supply an ORM transaction, authentication or a production application layer.')
    @dataclass(frozen=True)
    class Transfer:
        amount:int
        source_key:str
        target_key:str
    def factory(amount,source,target):
        if amount<=0 or source==target:raise ValueError('invalid transfer construction')
        return Transfer(amount,source,target)
    created=factory(100,'A','B')
    try:factory(-100,'A','B');invalid=False
    except ValueError:invalid=True
    yield item('domain-factory-validity',['Factory'],{'raw_invalid_amount':-100},{'created_amount':created.amount,'created_source':created.source_key,'created_target':created.target_key,'invalid_construction_rejected':invalid},'Construa a transferência pela fábrica e tente repetir com valor negativo. Confira que uma transferência inválida não chega a existir pelo contrato público.','A factory centralizes the valid construction of the domain object and rejects invalid combinations.','The construction rule belongs only to this hypothetical transfer fixture.')
    accounts=[{'key':'A','balance':1000,'active':True},{'key':'B','balance':5000,'active':False},{'key':'C','balance':500,'active':True}]
    def eligible(account):return account['balance']>=1000 and account['active']
    duplicated_filter=[row['key'] for row in accounts if row['balance']>=1000]
    specified=[row['key'] for row in accounts if eligible(row)]
    independently_validated=[row['key'] for row in accounts if eligible(row)]
    yield item('specification-reuse',['Specification'],{'query_candidates':duplicated_filter,'validator_candidates':independently_validated},{'query_candidates':specified,'validator_candidates':independently_validated,'same_predicate_result':specified==independently_validated},'Aplique a mesma specification na seleção e na validação das três contas fictícias. Confira que a conta inativa deixa de aparecer como candidata em apenas um caminho.','One named criterion is reused across selection and validation, eliminating the duplicated inconsistent predicate in this fixture.','The threshold is a synthetic teaching rule, not an advisor or customer eligibility rule from Faz.')
    upstream_v1={'available':1000};upstream_v2={'settled_balance':1000,'reserved_balance':200}
    def portfolio_consumer(contract):return contract['available']
    def order_consumer(contract):return contract['available']>=900
    broken=[]
    for name,consumer in [('portfolio-screen',portfolio_consumer),('order-check',order_consumer)]:
        try:consumer(upstream_v2)
        except KeyError:broken.append(name)
    portfolio_contract={'available':upstream_v2['settled_balance']}
    trading_contract={'available':upstream_v2['settled_balance']-upstream_v2['reserved_balance']}
    effects={'portfolio-screen':portfolio_consumer(portfolio_contract),'order-check':order_consumer(trading_contract)}
    context_edges={'portfolio':['portfolio-screen','trading-adapter'],'trading-adapter':['order-check']}
    impacted=set(context_edges['portfolio']);impacted.update(context_edges['trading-adapter'])
    yield item('context-contract-change',['Bounded Context','Context Map','DDD','Ubiquitous Language','Customer/Supplier'],{'uncoordinated_change_breaks_consumers':broken,'old_shared_available':upstream_v1['available']},{'portfolio_available':effects['portfolio-screen'],'trading_order_900_allowed':effects['order-check'],'trading_available':trading_contract['available'],'impacted_consumers':sorted(impacted),'broken_after_context_adaptation':0},'Altere o contrato do fornecedor de available para settled_balance e reserved_balance. Execute os dois consumidores, identifique os quebrados no mapa e adapte os significados de disponibilidade em cada contexto.','An actual schema change exposes affected consumers; bounded contexts give available different meanings, and the supplier/consumer agreement restores explicit contracts and a shared vocabulary within each context.','The context map and language belong to this hypothetical business exercise. They do not assert the canonical Faz glossary or a historical organizational decision.')
    foreign={'provider_state':'AUTHORISED'}
    def conforming_consumer(payload):return payload['provider_state']=='AUTHORISED'
    yield item('conformist-contract',['Conformist'],{'local_consumer_assumes_accepted':foreign['provider_state']=='accepted'},{'consumer_uses_upstream_state':conforming_consumer(foreign),'translation_layer_added':False},'Adapte o consumidor para usar diretamente provider_state=AUTHORISED, sem criar tradução local. Compare essa escolha com o adaptador semântico do caso anterior.','The downstream deliberately adopts the upstream vocabulary and schema, including its coupling cost.','The exercise demonstrates the relationship choice, not a recommendation to accept every provider concept.')
    shared={'fee_rate':.01};a=shared;b=shared;a['fee_rate']=.02;coupled_fee=b['fee_rate']*100
    separate_a={'fee_rate':.01};separate_b={'fee_rate':.01};separate_a['fee_rate']=.02
    yield item('separate-ways-change',['Separate Ways'],{'unrelated_context_fee_after_shared_mutation':coupled_fee},{'changed_context_fee':separate_a['fee_rate']*100,'independent_context_fee':separate_b['fee_rate']*100,'integration_edges':0},'Mude a política de taxa de um contexto e execute o outro. Compare o objeto compartilhado acidentalmente com contratos independentes sem integração.','Choosing separate ways prevents an unrelated context from inheriting the other context change through a shared mutable object.','Duplication has a maintenance cost; this fixture does not decide the real organizational boundary.')
    def shared_round(cents):return (cents+50)//100
    consumers=[lambda cents:shared_round(cents),lambda cents:shared_round(cents)]
    outputs=[consumer(149) for consumer in consumers]
    changed=[(149+51)//100 for _ in consumers]
    yield item('shared-kernel-impact',['Shared Kernel'],{'independent_rounding_results':[1,2]},{'shared_results':outputs,'consumers_affected_by_shared_rule_change':sum(a!=b for a,b in zip(outputs,changed)),'changed_results':changed},'Execute os dois consumidores com a mesma regra compartilhada e altere o arredondamento do kernel. Observe que ambos mudam e precisam do mesmo acordo de versão.','The shared kernel makes a small domain rule genuinely shared and exposes the joint impact of changing it.','The rounding is synthetic. Joint ownership and release coordination are required rather than inferred from a common helper.')
    internal={'settled_cents':100000};clients=[lambda payload:payload['balance'],lambda payload:payload['balance']]
    failures=0
    for client in clients:
        try:client(internal)
        except KeyError:failures+=1
    def open_service():return {'balance':internal['settled_cents']/100,'contract_version':1}
    results=[client(open_service()) for client in clients]
    yield item('open-host-service',['Open Host Service'],{'clients_broken_by_internal_schema':failures},{'client_balances':results,'public_contract_version':open_service()['contract_version'],'internal_field_exposed': 'settled_cents' in open_service()},'Altere o armazenamento interno para settled_cents e mantenha uma operação pública versionada para os dois clientes. Confira que a forma interna não vaza para o contrato público.','A stable public service contract supports multiple consumers while internal representation changes behind it.','Version governance, authentication and remote transport are not provided by this local contract exercise.')
