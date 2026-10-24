"""Executable object-level mechanisms in an isolated financial order scenario."""
from copy import deepcopy
from functools import lru_cache
from collections import defaultdict
from types import MappingProxyType
from invariants import validate_object

class Order:
    def __init__(self,amount=100): self.amount=amount
    def fee(self): return self.amount*.01
    def accept(self,visitor): return visitor.visit_order(self)

class PremiumOrder(Order):
    def fee(self): return self.amount*.005
    def accept(self,visitor): return visitor.visit_premium_order(self)

class OrderFactory:
    def create(self): return Order()

class PremiumOrderFactory(OrderFactory):
    def create(self): return PremiumOrder()

class BasicProductFamily:
    def create_validator(self): return lambda amount: 0<amount<=1000
    def create_fee_calculator(self): return lambda amount: amount*.01

class PremiumProductFamily:
    def create_validator(self): return lambda amount: 0<amount<=5000
    def create_fee_calculator(self): return lambda amount: amount*.005

class OrderFamily:
    def __init__(self,factory): self.factory=factory
    def pair(self): return self.factory.create_validator(), self.factory.create_fee_calculator()

class Builder:
    def __init__(self): self.fields={}
    def amount(self,value): self.fields['amount']=value;return self
    def build(self): return Order(**self.fields)

class Tree:
    def __init__(self,*children): self.children=children
    def total(self): return sum(c.total() if isinstance(c,Tree) else c.amount for c in self.children)

class FeeDecorator:
    def __init__(self,order,surcharge): self.order,self.surcharge=order,surcharge
    def fee(self): return self.order.fee()+self.surcharge

class Workflow:
    def __init__(self): self.state='new'
    def accept(self):
        if self.state!='new': raise ValueError('invalid transition')
        self.state='accepted'

class Template:
    def run(self,amount): return self.normalize(amount)+self.fee(amount)
    def normalize(self,amount): return amount
    def fee(self,amount): return 1

class PremiumTemplate(Template):
    def fee(self,amount): return .5

class FeeVisitor:
    def visit_order(self,order): return order.fee()
    def visit_premium_order(self,order): return order.fee()

class EventBus:
    def __init__(self): self.listeners=[]
    def subscribe(self,callback): self.listeners.append(callback)
    def publish(self,event):
        for listener in self.listeners: listener(event)

@lru_cache(maxsize=10)
def shared_symbol(symbol): return MappingProxyType({'symbol':symbol})

_registry={}
def registry(name):
    if name not in _registry: _registry[name]=object()
    return _registry[name]


def mechanisms():
    validator,calculator=OrderFamily(PremiumProductFamily()).pair()
    mismatched=BasicProductFamily().create_validator()
    yield 'Abstract Factory', {'accepted':mismatched(2000),'fee':calculator(2000)}, {'accepted':validator(2000),'fee':calculator(2000)}, 'One product family creates its compatible validator and fee calculator together.'
    provider={'cents':10000}
    yield 'Adapter', provider.get('amount'), provider['cents']/100, 'The boundary translates cents into the domain amount.'
    class MemoryTransport:
        def send(self,kind,amount):return f'{kind}:memory:{amount}'
    class PaperTransport:
        def send(self,kind,amount):return f'{kind}:paper:{amount}'
    class Notice:
        kind='standard'
        def __init__(self,transport):self.transport=transport
        def deliver(self,amount):return self.transport.send(self.kind,amount)
    class PremiumNotice(Notice):kind='premium'
    delivered=[notice(transport()).deliver(100) for notice in [Notice,PremiumNotice] for transport in [MemoryTransport,PaperTransport]]
    yield 'Bridge', {'coupled_variant_classes':4}, {'abstraction_types':2,'transport_types':2,'deliveries':delivered}, 'The notice abstraction hierarchy and the transport implementation hierarchy vary independently through composition.'
    yield 'Builder', 100, Builder().amount(250).build().amount, 'Construction accumulates chosen fields before returning an order.'
    validators=[lambda value: value>0,lambda value: value<=1000]
    yield 'Chain of Responsibility', True, all(check(2000) for check in validators), 'Each validator can stop a request before the next responsibility.'
    commands=[]
    commands.append(lambda:100+50)
    yield 'Command', 100, commands.pop()(), 'The requested credit is represented as an executable value.'
    yield 'Composite', 100, Tree(Order(100),Tree(Order(50),Order(25))).total(), 'Leaves and groups share a recursive total operation.'
    yield 'Decorator', Order().fee(), FeeDecorator(Order(),2).fee(), 'A wrapper extends behavior while retaining the wrapped order.'
    def settle(amount): return {'accepted':amount>0,'fee':Order(amount).fee()}
    yield 'Facade', 'two-separate-calls', settle(100), 'One entrance coordinates validation and fee calculation.'
    yield 'Factory Method', type(Order()).__name__, type(PremiumOrderFactory().create()).__name__, 'An overridable creation operation selects the concrete order.'
    before=[{'symbol':'SYNTHETIC'} for _ in range(5)]
    after=[shared_symbol('SYNTHETIC') for _ in range(5)]
    yield 'Flyweight', len({id(x) for x in before}),len({id(x) for x in after}), 'Five orders share one immutable-style symbol object; per-order amounts stay separate.'
    expression=['amount','>',100]
    context={'amount':250}
    yield 'Interpreter', False, context[expression[0]]>expression[2], 'A small explicit grammar is evaluated against the order context; no eval is used.'
    def values(orders):
        for order in orders: yield order.amount
    yield 'Iterator', [100], list(values([Order(100),Order(50)])), 'Traversal provides elements without exposing storage indexing.'
    notifications=[]
    def mediate(event): notifications.extend([('audit',event),('risk',event)])
    mediate('ORDER-1')
    yield 'Mediator',1,len(notifications),'A coordinator routes one order event to audit and risk participants.'
    order={'amount':100};saved=deepcopy(order);order['amount']=200;order=deepcopy(saved)
    yield 'Memento',200,order['amount'],'An explicit saved snapshot restores a previous local state; business reversals still need events.'
    observed=[];bus=EventBus();bus.subscribe(observed.append);bus.publish('ORDER-1')
    yield 'Observer',0,len(observed),'A registered observer receives the published state change.'
    original={'amount':100,'tags':[]};cloned=deepcopy(original);cloned['tags'].append('premium')
    yield 'Prototype',original['tags'],cloned['tags'],'A prototype copy can be customized without mutating the original.'
    def proxy(allowed): return Order().amount if allowed else 'denied'
    yield 'Proxy',Order().amount,proxy(False),'A substitute checks permission before delegating to the target.'
    before=[object(),object()];after=[registry('orders'),registry('orders')]
    yield 'Singleton',len({id(x) for x in before}),len({id(x) for x in after}),'The local registry returns one instance for one name within this process.'
    flow=Workflow();flow.accept()
    try: flow.accept();result='accepted-twice'
    except ValueError: result='second-transition-rejected'
    yield 'State','accepted-twice',result,'Behavior depends on the current state and rejects a transition outside its contract.'
    calculate=lambda amount,rule:rule(amount)
    yield 'Strategy',calculate(100,lambda a:a*.01),calculate(100,lambda a:a*.02),'The caller supplies a fee algorithm without replacing the order operation.'
    yield 'Template Method',Template().run(100),PremiumTemplate().run(100),'The operation preserves a sequence while a subclass changes the fee step.'
    yield 'Visitor',0,PremiumOrder().accept(FeeVisitor()),'A separate visitor performs an operation over an order through its public contract.'

if __name__=='__main__':
    import argparse
    import json
    parser=argparse.ArgumentParser()
    parser.add_argument('--concept')
    args=parser.parse_args()
    count=0
    for name,before,after,mechanism in mechanisms():
        if args.concept and name!=args.concept: continue
        validate_object(name,before,after)
        count+=1
        print(json.dumps(dict(concept=name,before=before,after=after,mechanism=mechanism),ensure_ascii=False))
    if not count: raise SystemExit('unknown object concept')
    print(f'comparison=PASS object_mechanisms={count} scope=LOCAL_FINANCIAL_MODEL')
