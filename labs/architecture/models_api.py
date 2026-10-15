"""Local message, HTTP-contract and proxy observations with synthetic payloads."""
import asyncio
import base64
import hashlib
import hmac
import json
from collections import deque


def item(probe,names,before,after,action,guarantee,limit):
    return dict(case='order-boundaries',probe=probe,names=names,before=before,after=after,action=action,guarantee=guarantee,limit=limit)


def observations():
    resources={'ORDER-1':{'status':'accepted','amount':100}};writes=[]
    def rest(method,path,body=None):
        if method=='GET':return 200,dict(resources[path.rsplit('/',1)[-1]])
        if method=='POST' and path=='/orders':resources[body['order_id']]=body;writes.append(body['order_id']);return 201,body
        return 405,{'error':'method not allowed'}
    status,representation=rest('GET','/orders/ORDER-1');writes_after_get=len(writes)
    created,_=rest('POST','/orders',{'order_id':'ORDER-2','amount':50});unsupported,_=rest('PATCH','/orders/ORDER-1')
    yield item('rest-resource-methods',['REST'],{'GET_with_unconditional_write_calls':1},{'GET_status':status,'GET_amount':representation['amount'],'GET_writes':writes_after_get,'POST_status':created,'total_writes':len(writes),'unsupported_method_status':unsupported},'Leia o recurso por GET, crie outro por POST e tente um método não atendido. Confira a ausência de escrita no GET e os códigos 200, 201 e 405.','Resource paths, method semantics and response status are explicit; GET does not become an operation that writes.','Requests are local dictionaries and function calls, without an HTTP server, caching intermediaries or complete REST constraints.')
    methods={'reserve':lambda amount:{'reserved_amount':amount},'release':lambda amount:{'released_amount':amount}}
    call={'method':'reserve','params':{'amount':100},'request_id':'REQUEST-1'}
    rpc_result=methods[call['method']](**call['params'])
    yield item('rpc-operation-contract',['RPC','Request/Reply'],{'unmatched_reply_request_id':'OTHER'},{'request_id':call['request_id'],'reply_request_id':call['request_id'],'result':rpc_result,'operation':call['method']},'Envie a operação reserve com seus parâmetros e correlacione a resposta com REQUEST-1. Diferencie esse contrato por operação da rota de recurso do exercício REST.','The dispatcher invokes an explicit operation and returns its result to the matching requester.','The finite request/reply dispatcher does not implement a remote transport, deadlines or an RPC framework.')
    backend_calls=[];checks=[]
    def order_backend(request):backend_calls.append('orders');return {'status':200,'body':request['body'],'method':request['method']}
    def position_backend(request):backend_calls.append('positions');return {'status':200,'body':{'balance':1100},'method':request['method']}
    routes={'/orders':order_backend,'/positions':position_backend}
    def gateway(request):
        checks.append('auth')
        if request.get('role')!='advisor':return {'status':403}
        return routes[request['path']](request)
    unauthorized=gateway({'path':'/orders','method':'POST','body':{'amount':100},'role':'guest'});calls_before=len(backend_calls)
    forwarded=gateway({'path':'/orders','method':'POST','body':{'amount':100},'role':'advisor'});position=gateway({'path':'/positions','method':'GET','body':None,'role':'advisor'})
    yield item('gateway-route-offload',['API Gateway','Gateway Routing','Gateway Offloading','Reverse Proxy','API Gateway Security'],{'unprotected_guest_backend_calls':1},{'guest_status':unauthorized['status'],'guest_backend_calls':calls_before,'routed_backends':backend_calls,'forwarded_method':forwarded['method'],'forwarded_amount':forwarded['body']['amount'],'entry_auth_checks':len(checks),'position_status':position['status']},'Tente uma chamada sem permissão e depois chamadas para ordens e posições. Confira que o gateway recusa antes do backend, escolhe a rota e preserva método, corpo e resposta no encaminhamento.','The entry point routes requests, offloads authentication checks and forwards the accepted method/payload to the selected backend.','This models gateway/proxy properties, not a deployed reverse proxy, token verification, TLS termination or every HTTP forwarding rule.')
    service_calls=[]
    def positions():service_calls.append('positions');return {'balance':1100}
    def orders():service_calls.append('orders');return [{'status':'pending'},{'status':'settled'}]
    def bff(client):
        position,order_rows=positions(),orders()
        if client=='mobile':return {'balance':position['balance'],'pending_count':sum(row['status']=='pending' for row in order_rows)}
        return {'position':position,'orders':order_rows}
    mobile,web=bff('mobile'),bff('web')
    yield item('bff-composed-view',['Backend for Frontend (BFF)','API Composition','Gateway Aggregation'],{'frontend_round_trips_per_view':2},{'frontend_round_trips_per_view':1,'mobile':mobile,'web_order_count':len(web['orders']),'backend_calls_for_two_views':len(service_calls)},'Monte a mesma visão a partir de posição e ordens para web e mobile. Observe uma chamada do cliente e os formatos distintos preparados no servidor.','A server-side composition calls two owners and returns a client-specific view, reducing client round trips without pretending the backend calls disappear.','Partial failures, freshness and authorization of each constituent service need separate contracts.')
    portfolio={'SYNTHETIC-1':{'account_id':'SYNTHETIC-1','balance':1100}}
    order_counts={'SYNTHETIC-1':2}
    representation={'__typename':'Account','account_id':'SYNTHETIC-1'}
    def portfolio_entity(ref):return portfolio[ref['account_id']]
    def order_entity(ref):return {'open_orders':order_counts[ref['account_id']]}
    composed={**portfolio_entity(representation),**order_entity(representation)}
    yield item('federated-entity-key',['GraphQL Federation'],{'join_by_unrelated_display_label':None},{'entity_type':representation['__typename'],'composed_account':composed,'subgraph_owners':['portfolio','orders']},'Passe a representação da entidade Account com sua chave aos dois subgraphs lógicos e componha balance e open_orders pelo mesmo identificador.','Entity-reference resolution joins fields owned by different subgraphs through the declared entity key instead of a display label.','This is the entity-key resolution property of federation. It does not include a GraphQL parser, supergraph schema, query planner or Apollo runtime.')
    def order_representation(state):return {'state':state,'links':{'cancel':'/orders/ORDER-1/cancel'} if state=='accepted' else {}}
    completed=order_representation('settled');followed=completed['links'].get('cancel')
    yield item('hypermedia-affordance',['HATEOAS'],{'hardcoded_client_attempts_cancel_after_settlement':True},{'representation_state':completed['state'],'cancel_link':followed,'client_attempts_cancel':followed is not None},'Mude a ordem de accepted para settled e deixe o cliente procurar a relação cancel na representação recebida. Confira que ele não inventa uma ação que o servidor deixou de oferecer.','The representation exposes state-dependent action links and the client follows an available relation rather than hardcoding every transition.','The exercise covers one affordance and not an entire hypermedia API or authorization policy.')
    polls=0;value=None
    for turn in range(3):
        polls+=1
        if turn==2:value='position-ready'
    async def long_poll():
        ready=asyncio.Event();requests=[0]
        async def request():requests[0]+=1;await ready.wait();return 'position-ready'
        waiting=asyncio.create_task(request());await asyncio.sleep(0);ready.set();return requests[0],await waiting
    long_requests,long_value=asyncio.run(long_poll())
    yield item('poll-vs-long-poll',['Polling','Long Polling'],{'periodic_requests_until_ready':polls,'value':value},{'long_poll_requests':long_requests,'value':long_value},'Consulte três vezes até a posição existir e compare com uma requisição que aguarda o evento de atualização antes de responder.','Polling issues repeated requests; long polling holds one request until the result becomes available.','The wait uses a local asyncio event, with no HTTP timeout, intermediary buffering or reconnect loop.')
    events=[{'id':1,'balance':1000},{'id':2,'balance':1100}]
    frames=''.join(f"id: {event['id']}\nevent: position\ndata: {json.dumps({'balance':event['balance']})}\n\n" for event in events)
    parsed=[]
    for block in frames.strip().split('\n\n'):
        fields=dict(line.split(': ',1) for line in block.splitlines());parsed.append({'id':int(fields['id']),'data':json.loads(fields['data'])})
    resumed=[event for event in parsed if event['id']>1]
    yield item('sse-event-resume',['Server-Sent Events'],{'reconnect_without_cursor_events':len(parsed)},{'content_type':'text/event-stream','resumed_event_ids':[event['id'] for event in resumed],'resumed_balance':resumed[0]['data']['balance'],'messages_are_server_to_client':True},'Codifique e leia registros id/event/data, desconecte depois do id 1 e retome com esse cursor. Confira que somente o id 2 é entregue de novo ao cliente.','SSE event records carry IDs and data; a server can honor the last received ID when selecting the resumed stream.','The record parser is local. HTTP streaming, browser EventSource, retry timing and proxy behavior are not executed.')
    def ws_encode(text,masked):
        payload=text.encode();assert len(payload)<126
        mask=b'ABCD' if masked else b''
        transformed=bytes(byte^mask[index%4] for index,byte in enumerate(payload)) if masked else payload
        return bytes([0x81,len(payload)|(0x80 if masked else 0)])+mask+transformed
    def ws_decode(frame):
        assert frame[0]==0x81
        size=frame[1]&0x7f;masked=bool(frame[1]&0x80);mask=frame[2:6] if masked else b'';payload=frame[6:6+size] if masked else frame[2:2+size]
        return bytes(byte^mask[index%4] for index,byte in enumerate(payload)).decode() if masked else payload.decode()
    to_server=deque([ws_encode('reserve:ORDER-1',True)]);to_client=deque([ws_encode('position:1100',False)])
    yield item('websocket-duplex-frames',['WebSocket'],{'server_push_requires_new_poll':True},{'client_to_server':ws_decode(to_server.popleft()),'server_to_client':ws_decode(to_client.popleft()),'client_frame_masked':True,'new_client_poll_for_server_message':False},'Envie um frame de texto mascarado do cliente e um frame independente do servidor. Decodifique os dois sentidos sem criar uma nova consulta para a mensagem do servidor.','Two independent text-frame directions share the duplex model; client frames are masked and server frames are decoded without a new poll.','Only small unfragmented text frames are modeled, without the HTTP upgrade handshake, extensions, control frames or a production WebSocket implementation.')
    key=b'synthetic-webhook-key';body=json.dumps({'event_id':'EVENT-1','amount':100},sort_keys=True).encode();signature=hmac.new(key,body,hashlib.sha256).hexdigest();inbox=set();effects=[]
    def callback(payload,signed):
        if not hmac.compare_digest(hmac.new(key,payload,hashlib.sha256).hexdigest(),signed):return 401
        event=json.loads(payload)
        if event['event_id'] not in inbox:inbox.add(event['event_id']);effects.append(event['amount'])
        return 200
    first,repeat,invalid=callback(body,signature),callback(body,signature),callback(body,'invalid')
    yield item('signed-webhook-callback',['Webhook'],{'polling_receiver_callback_effects':0},{'callback_status':first,'repeat_status':repeat,'invalid_signature_status':invalid,'effects':effects},'Receba o callback assinado, repita a mesma entrega e altere a assinatura. Confira um único efeito e a recusa 401 da mensagem que não passa na verificação.','The provider pushes the event to a callback; signature verification precedes the receiver effect and the event identity suppresses a repeat.','All keys and payloads are synthetic. Timestamp replay windows, secret distribution, TLS and a live callback server are not implemented.')
    class Proxy:
        def __init__(self,workload):self.workload=workload;self.policy={'version':1,'allowed':False};self.calls=0
        def send(self,payload):
            self.calls+=1
            return {'status':200 if self.policy['allowed'] else 403,'identity':self.workload,'payload':payload,'policy_version':self.policy['version']}
    proxies=[Proxy('order-service'),Proxy('position-service')];before=proxies[0].send('ORDER-1')['status']
    for proxy in proxies:proxy.policy={'version':2,'allowed':True}
    responses=[proxy.send('ORDER-1') for proxy in proxies]
    yield item('sidecar-outbound-policy',['Sidecar','Ambassador','Service Mesh'],{'old_policy_status':before},{'updated_statuses':[response['status'] for response in responses],'identities':[response['identity'] for response in responses],'policy_versions':[response['policy_version'] for response in responses],'workload_business_code_changed':False},'Faça cada workload usar seu proxy de saída. Atualize a política nos dois proxies e confira identidade, versão e resposta sem alterar a operação de negócio.','A companion outbound proxy adds transport policy and identity; distributing the same policy to both companion proxies exhibits one mesh control/data-plane property.','The proxies are logical local companions, not separate pods or a deployed service mesh. mTLS has its own distinct experiment.')
