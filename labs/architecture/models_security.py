"""Synthetic signed-token models and real TLS handshakes over local socket pairs."""
import base64
import hashlib
import hmac
import json
import socket
import ssl
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

KEYS={'old':b'synthetic-learning-old-key','new':b'synthetic-learning-new-key'}
ISSUER='https://learning-issuer.invalid'


def b64(data):return base64.urlsafe_b64encode(data).rstrip(b'=').decode()
def unb64(data):return base64.urlsafe_b64decode(data+'='*(-len(data)%4))
def sign(claims,kid='new'):
    header=b64(json.dumps({'alg':'HS256','typ':'JWT','kid':kid},sort_keys=True).encode());body=b64(json.dumps(claims,sort_keys=True).encode());message=f'{header}.{body}'
    return message+'.'+b64(hmac.new(KEYS[kid],message.encode(),hashlib.sha256).digest())
def verify(token,trusted,audience,nonce=None,now=1):
    header,body,signature=token.split('.');metadata=json.loads(unb64(header))
    if metadata['alg']!='HS256' or metadata['kid'] not in trusted:raise ValueError('untrusted algorithm/key')
    calculated=hmac.new(trusted[metadata['kid']],f'{header}.{body}'.encode(),hashlib.sha256).digest()
    if not hmac.compare_digest(calculated,unb64(signature)):raise ValueError('invalid signature')
    claims=json.loads(unb64(body))
    if claims.get('iss')!=ISSUER or claims.get('aud')!=audience or not claims.get('sub') or claims.get('exp',0)<=now:raise ValueError('invalid token claims')
    if nonce is not None and claims.get('nonce')!=nonce:raise ValueError('invalid nonce')
    return claims

def denied(function):
    try:function();return False
    except (ValueError,KeyError):return True

def item(probe,names,before,after,action,guarantee,limit):
    return dict(case='access-policy',probe=probe,names=names,before=before,after=after,action=action,guarantee=guarantee,limit=limit)


@lru_cache(maxsize=1)
def tls_observation():
    with tempfile.TemporaryDirectory(prefix='learning-mtls-') as directory:
        root=Path(directory)
        def openssl(*args):subprocess.run(['openssl',*args],cwd=root,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
        openssl('req','-x509','-newkey','rsa:2048','-nodes','-days','1','-keyout','ca.key','-out','ca.crt','-subj','/CN=LearningCA','-addext','basicConstraints=critical,CA:TRUE','-addext','keyUsage=critical,keyCertSign,cRLSign')
        for name,common_name,purpose in [('server','localhost','serverAuth'),('client','learning-order-service','clientAuth')]:
            openssl('req','-new','-newkey','rsa:2048','-nodes','-keyout',name+'.key','-out',name+'.csr','-subj','/CN='+common_name)
            extensions='basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage='+purpose+'\n'
            if name=='server':extensions+='subjectAltName=DNS:localhost\n'
            (root/(name+'.ext')).write_text(extensions)
            openssl('x509','-req','-in',name+'.csr','-CA','ca.crt','-CAkey','ca.key','-CAcreateserial','-out',name+'.crt','-days','1','-sha256','-extfile',name+'.ext')
        def handshake(require_client,present_client):
            server_context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);server_context.load_cert_chain(root/'server.crt',root/'server.key')
            server_context.load_verify_locations(root/'ca.crt');server_context.verify_mode=ssl.CERT_REQUIRED if require_client else ssl.CERT_NONE
            client_context=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);client_context.load_verify_locations(root/'ca.crt')
            if present_client:client_context.load_cert_chain(root/'client.crt',root/'client.key')
            server_socket,client_socket=socket.socketpair();server_socket.settimeout(3);client_socket.settimeout(3)
            def server():
                try:
                    with server_context.wrap_socket(server_socket,server_side=True) as channel:
                        peer=bool(channel.getpeercert());payload=channel.recv(64);channel.sendall(b'accepted');return {'accepted':payload==b'ORDER-1','peer_authenticated':peer}
                except (ssl.SSLError,OSError):return {'accepted':False,'peer_authenticated':False}
            def client():
                try:
                    with client_context.wrap_socket(client_socket,server_hostname='localhost') as channel:
                        server_authenticated=bool(channel.getpeercert());channel.sendall(b'ORDER-1');reply=channel.recv(64);return {'accepted':reply==b'accepted','server_authenticated':server_authenticated}
                except (ssl.SSLError,OSError):return {'accepted':False,'server_authenticated':False}
            with ThreadPoolExecutor(max_workers=2) as executor:
                server_future=executor.submit(server);client_future=executor.submit(client)
                return server_future.result(timeout=5),client_future.result(timeout=5)
        one_way_server,_=handshake(False,False);anonymous_server,_=handshake(True,False);trusted_server,trusted_client=handshake(True,True)
        return {'before':{'client_without_certificate_accepted':one_way_server['accepted']},'after':{'client_without_certificate_accepted':anonymous_server['accepted'],'trusted_client_accepted':trusted_server['accepted'],'client_authenticated_by_server':trusted_server['peer_authenticated'],'server_authenticated_by_client':trusted_client['server_authenticated'],'payload_exchange_completed':trusted_client['accepted']}}


def observations():
    verifier='synthetic-verifier-'*3;challenge=b64(hashlib.sha256(verifier.encode()).digest());grant={'code':'CODE-1','client':'learning-client','redirect':'https://learning-client.invalid/callback','challenge':challenge,'used':False}
    def redeem(code,submitted_verifier,redirect):
        if code!=grant['code'] or redirect!=grant['redirect'] or grant['used']:raise ValueError('invalid/reused code')
        if b64(hashlib.sha256(submitted_verifier.encode()).digest())!=grant['challenge']:raise ValueError('invalid PKCE verifier')
        grant['used']=True
        return sign({'iss':ISSUER,'aud':'order-api','sub':'SYNTHETIC-USER','scope':'order:read','exp':10})
    wrong_verifier=denied(lambda:redeem('CODE-1','wrong',grant['redirect']));wrong_redirect=denied(lambda:redeem('CODE-1',verifier,'https://other.invalid/callback'))
    access=redeem('CODE-1',verifier,grant['redirect']);resource_claims=verify(access,{'new':KEYS['new']},'order-api');replay=denied(lambda:redeem('CODE-1',verifier,grant['redirect']))
    yield item('oauth-code-pkce',['OAuth2'],{'code_without_binding_can_be_replayed':True},{'wrong_verifier_rejected':wrong_verifier,'wrong_redirect_rejected':wrong_redirect,'code_reuse_rejected':replay,'resource_subject':resource_claims['sub'],'resource_scope':resource_claims['scope']},'Troque o código por token usando o verificador PKCE e a redirect URI vinculada. Antes da troca válida, tente os dois valores errados; depois tente reutilizar o código.','The local authorization-code model binds verifier and redirect, permits one code redemption and issues an audience/scope-limited signed access token.','A teaching model of RFC 6749/7636 message checks; it is not an authorization-server library, browser login, refresh flow or production OAuth security implementation.')
    identity={'iss':ISSUER,'aud':'learning-client','sub':'SYNTHETIC-USER','nonce':'NONCE-1','exp':10}
    identity_token=sign(identity);claims=verify(identity_token,{'new':KEYS['new']},'learning-client',nonce='NONCE-1')
    wrong_nonce=denied(lambda:verify(identity_token,{'new':KEYS['new']},'learning-client',nonce='OTHER'))
    wrong_aud=denied(lambda:verify(identity_token,{'new':KEYS['new']},'other-client',nonce='NONCE-1'))
    tampered=identity_token[:-2]+'AA';bad_signature=denied(lambda:verify(tampered,{'new':KEYS['new']},'learning-client',nonce='NONCE-1'))
    yield item('oidc-id-token-validation',['OIDC'],{'claims_read_without_signature_or_client_binding':True},{'verified_subject':claims['sub'],'wrong_nonce_rejected':wrong_nonce,'wrong_audience_rejected':wrong_aud,'tampered_signature_rejected':bad_signature},'Valide o ID token assinado e repita com nonce diferente, audience diferente e assinatura alterada. Confira que conhecer um sub no JSON não basta para aceitar a identidade.','The ID-token validation property checks issuer, audience, nonce, expiration and the configured HS256 signature before accepting the subject.','The synthetic client uses a preconfigured shared key. Discovery, JWKS, key negotiation, all claim rules and an actual OpenID Provider are not implemented.')
    payload={'iss':ISSUER,'aud':'order-api','sub':'order-service','scope':'order:read','exp':10};old=sign(payload,'old');new=sign(payload,'new')
    overlap={'old':KEYS['old'],'new':KEYS['new']};retired={'new':KEYS['new']}
    yield item('signed-key-rotation',['Secrets Rotation'],{'old_token_accepted_during_overlap':not denied(lambda:verify(old,overlap,'order-api'))},{'new_token_accepted':not denied(lambda:verify(new,retired,'order-api')),'old_token_rejected_after_retirement':denied(lambda:verify(old,retired,'order-api')),'tampered_new_token_rejected':denied(lambda:verify(new[:-2]+'AA',retired,'order-api'))},'Emita tokens com old e new, aceite ambos na janela de sobreposição e retire old do verificador. Confira a validação criptográfica, a recusa do token antigo e a recusa da assinatura alterada.','A signed credential remains valid through the overlap and becomes inadmissible after its signing key is removed from trust.','Keys are fixed synthetic HMAC material. Secret storage, asymmetric key distribution and coordinated live-service rotation are outside the experiment.')
    def client_credentials(client,secret):
        if client!='order-service' or secret!='synthetic-client-secret':raise ValueError('unknown service client')
        return sign(payload)
    bad_client=denied(lambda:client_credentials('rogue','wrong'));service_token=client_credentials('order-service','synthetic-client-secret');service=verify(service_token,{'new':KEYS['new']},'order-api')
    yield item('signed-service-identity',['Service-to-Service Identity'],{'self_declared_service_header_accepted':True},{'unauthenticated_client_rejected':bad_client,'authenticated_service_subject':service['sub'],'resource_audience':service['aud'],'permission_scope':service['scope']},'Autentique o cliente de serviço antes de emitir a credencial e valide sua assinatura no recurso. Compare com aceitar um nome de serviço apenas declarado pelo chamador.','The resource authenticates a signed service principal and validates its intended audience/scope rather than trusting a caller-supplied service label.','Client secrets and tokens are synthetic; there is no real identity provider, protected key store or live service deployment.')
    subject=sign({'iss':ISSUER,'aud':'gateway','sub':'SYNTHETIC-USER','scope':'order:read position:read','exp':10})
    verified=verify(subject,{'new':KEYS['new']},'gateway')
    exchanged=sign({'iss':ISSUER,'aud':'order-api','sub':verified['sub'],'scope':'order:read','act':{'sub':'gateway-service'},'exp':5})
    exchange_claims=verify(exchanged,{'new':KEYS['new']},'order-api')
    yield item('downscoped-token-exchange',['Token Exchange'],{'original_token_wrong_resource_rejected':denied(lambda:verify(subject,{'new':KEYS['new']},'order-api'))},{'exchanged_audience':exchange_claims['aud'],'exchanged_scope':exchange_claims['scope'],'subject':exchange_claims['sub'],'actor':exchange_claims['act']['sub'],'expires':exchange_claims['exp']},'Valide o token destinado ao gateway e troque-o por uma credencial mais curta para order-api. Confira o usuário preservado, o ator do serviço e a redução de escopo.','The exchanged credential is bound to the target resource and a narrower delegated scope, preserving subject and actor identities.','This is an RFC 8693-style claim transformation model, without a token-exchange endpoint or a complete delegation authorization policy.')
    def trusted_request(token,inside_network):
        checked=verify(token,{'new':KEYS['new']},'order-api')
        if checked['sub']!='order-service' or checked['scope']!='order:read':raise ValueError('policy denied')
        return True
    rogue=sign({'iss':ISSUER,'aud':'order-api','sub':'rogue','scope':'order:read','exp':10})
    yield item('verify-internal-request',['Zero Trust'],{'internal_origin_alone_grants_access':True},{'internal_rogue_rejected':denied(lambda:trusted_request(rogue,True)),'verified_service_allowed':trusted_request(service_token,True),'internal_flag_bypasses_verification':False},'Marque os dois pedidos como internos. Recuse o serviço rogue mesmo com token assinado válido e aceite somente o principal e a permissão esperados para o recurso.','Network location does not replace per-request identity and resource-policy verification in the tested boundary.','This demonstrates one zero-trust access property, not an organization-wide zero-trust architecture, device posture or continuous risk engine.')
    edges={('workstation','bastion'),('bastion','ledger-admin')};hops=[]
    def connect(source,destination,role):
        if (source,destination) not in edges or role!='admin':return False
        hops.append((source,destination));return True
    direct=connect('workstation','ledger-admin','admin');first=connect('workstation','bastion','admin');second=connect('bastion','ledger-admin','admin')
    yield item('bastion-admin-hop',['Bastion Host'],{'unrestricted_direct_admin_path':True},{'direct_path_allowed':direct,'authorized_two_hops':first and second,'hops':hops,'non_admin_rejected':not connect('workstation','bastion','advisor')},'Tente o acesso administrativo direto e depois os dois saltos permitidos via bastion. Repita o primeiro salto com uma pessoa sem papel administrativo.','Administrative access is funneled through an authenticated jump boundary and direct access to the protected target is denied.','The graph executes authorization and routing decisions, not SSH, a real bastion host, firewall rules or session recording.')
    tls=tls_observation()
    yield item('mutual-tls-peer-certs',['mTLS'],tls['before'],tls['after'],'Execute três handshakes TLS por socketpair: servidor sem exigir cliente, servidor exigindo cliente ausente e cliente com certificado confiável. Confira a autenticação dos dois pares e a troca de ORDER-1.','Real SSLContext handshakes reject a client missing its certificate when mutual verification is required and authenticate both trusted peers before exchanging data.','Certificates and keys are generated only in a temporary directory and removed. No listening port, external connection, production CA or service configuration is changed.')
