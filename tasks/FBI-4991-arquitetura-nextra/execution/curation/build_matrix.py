#!/usr/bin/env python3
"""Create a complete, evidence-bound author matrix without laundering partial matches."""
import collections,datetime,gzip,hashlib,json,re
from pathlib import Path
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
load=lambda name:json.loads((BASE/name).read_text())
coverage=json.loads((ROOT/'tasks/architecture-course-2026-10-14/evidence/coverage.json').read_text())
selections=load('source-selections.json');sources=load('sources.json');metadata=load('github-metadata.json');licenses=load('licenses.json');revision_licenses=load('revision-licenses.json');skills=load('skill-candidates.json');trending=load('trending-monthly.json')
learning=json.loads((ROOT/'tasks/FBI-4991-arquitetura-nextra/execution/learning/concept-matrix.json').read_text())
learning_by_id={x['concept_id']:x for x in learning['concepts']}
heading_slugs=load('heading-slugs.json')
assert {x['concept_id'] for x in coverage['concepts']}==set(selections)

# These are explicit semantic findings, not exceptions to the requirement.
GAPS={}
def gaps(ids,reason):
 for key in ids.split():GAPS[key]=reason

gaps('a-b-deployment','O controller Canary não demonstra a distribuição por atributo de usuário exigida por A/B.')
gaps('actor-model single-writer-principle','A base de atores está verificada; falta uma aplicação OSS consumidora que delimite a propriedade e a escrita do estado.')
gaps('clean-architecture onion-architecture','Immich declara adoção parcial de Hexagonal; isso não demonstra todas as regras de dependência de Clean ou Onion.')
gaps('cell-based-architecture space-based-architecture pac vertical-slice-architecture three-phase-commit-3pc','O candidato disponível é framework, template, workshop ou demo. Falta uma aplicação OSS real que implemente o mecanismo completo.')
gaps('customer-supplier conformist shared-kernel separate-ways','Context Mapper fornece o modelo de exemplo; falta a decisão e a implementação dos vínculos em um produto OSS real.')
gaps('ubiquitous-language ddd modular-monolith','Os contextos nomeados GitLab são evidência parcial. Não demonstram sozinhos negociação de linguagem, o método DDD inteiro ou todas as fronteiras de um monólito modular.')
gaps('distributed-lock','A base Mutex e o servidor de leases não demonstram ainda o uso completo da trava por uma aplicação consumidora delimitada.')
gaps('reservation-pattern','O carrinho Medusa comprova idempotência; falta rastrear a reserva e os caminhos de confirmar e cancelar do estoque.')
gaps('outbox-cdc','A persistência Fineract e o Event Router Debezium estão separados. Falta uma aplicação que conecte sua outbox ao CDC em configuração verificável.')
gaps('transactional-inbox exactly-once-semantics','Deduplicação do broker não demonstra a transação que une inbox e efeito externo nem exactly once de ponta a ponta.')
gaps('saga choreography-saga orchestration-saga compensating-transaction','O coordenador Seata TCC é adjacente. Falta o fluxo real de uma aplicação OSS que execute as etapas e as compensações da Saga correspondente.')
gaps('write-through write-behind-write-back two-level-cache','A implementação Redisson está verificada; falta a configuração e o uso do mecanismo em uma aplicação OSS consumidora.')
gaps('warm-standby cold-standby','A fonte encontrada é documentação primária. Falta uma aplicação ou configuração operacional OSS que mostre o procedimento correspondente.')
gaps('pessimistic-locking','@Version comprova concorrência otimista. Falta o caminho de bloqueio pessimista no aplicativo consumidor.')
gaps('fork-join','A execução concorrente foi localizada. Falta demonstrar a junção dos resultados da mesma operação.')
gaps('lock-free wait-free','Operações atômicas ou ausência de mutex não provam a propriedade de progresso. Falta a análise do algoritmo e de seu limite de passos.')
gaps('load-shedding','A interrupção por backpressure não comprova descarte ou recusa de carga na fronteira de admissão da aplicação escolhida.')
gaps('eventual-consistency','Reconstruir estado por histórico não demonstra sozinho a consistência eventual entre uma escrita e a visão de leitura do produto.')
gaps('oauth2 oidc','O arquivo de token exchange prova uma parte do protocolo. Falta o caminho de autorização e validação usado pela aplicação consumidora para o protocolo inteiro.')
gaps('secrets-rotation','Criar uma credencial temporária não comprova a rotação da credencial estática. Falta o caminho de rotação e sua aplicação no banco.')
gaps('serverless','O controlador Knative implementa a plataforma; falta uma aplicação OSS consumidora com função, trigger e configuração de execução.')
gaps('retry-queue','O tracker de entrega futura não prova a transferência e o consumo de uma fila de nova tentativa da aplicação.')
gaps('strangler-fig','Next.js implementa o roteamento necessário, mas falta uma migração identificada de uma aplicação OSS real entre o sistema anterior e o novo.')
gaps('backend-for-frontend-bff api-composition gateway-aggregation','A fronteira Gitaly é um serviço. Falta a composição de múltiplas APIs para uma apresentação específica e seu consumidor real.')
gaps('hateoas','URLs no retorno da API não demonstram navegação orientada por relações e ações disponíveis.')
gaps('golden-signals','Os dashboards têm sinais úteis; falta conferir conjuntamente tráfego, erros, latência e saturação da mesma fronteira observada.')
gaps('use-method-utilization-saturation-errors','O dashboard apresenta utilização e saturação. Falta comprovar o eixo de erros para cada recurso coberto.')
gaps('opentelemetry','O trecho Loki usa tracing; é necessário provar a API OpenTelemetry efetivamente usada, em vez de inferir o SDK pelo nome de um span.')
gaps('metrics','O trecho de tracing não demonstra os instrumentos de métricas e seus labels. Falta o arquivo do produto que cria e atualiza essas métricas.')
gaps('memento','O log de sessão não demonstra ainda um snapshot opaco preservado e restaurado sem quebrar o encapsulamento.')
gaps('bridge','O wrapper de logging pode ser Adapter. Falta demonstrar duas hierarquias que variam independentemente.')
gaps('abstract-factory factory-method','A configuração genérica do plugin não demonstra ainda os métodos de criação e as famílias de produtos do padrão.')
gaps('adapter facade proxy','O aplicativo FastAPI compõe middlewares. Falta o contrato específico do Adapter, da Facade ou do Proxy para fechar esses itens.')
gaps('decorator','O middleware é um candidato de composição, mas falta rastrear o wrapper que conserva o contrato do objeto ou função decorado.')
gaps('iterator interpreter','A árvore e o visitor foram localizados; falta o contrato de percurso ou o executor das expressões que demonstra esse conceito.')
gaps('mediator','O serviço de escrita não demonstra ainda um mediador central que desacople os participantes.')
gaps('specification','A consulta SQL do produto não demonstra um contrato Specification composto e reutilizado pelo domínio.')
gaps('stateless-services','Um recurso API não prova ausência de estado local necessário em todos os caminhos do serviço.')
gaps('tcc-try-confirm-cancel','Seata implementa o coordenador e o recurso TCC. Falta uma aplicação consumidora OSS real com reserva, confirmação e cancelamento de negócio.')
gaps('kappa-architecture','Uma tarefa de stream não prova o reprocessamento pelo mesmo log nem a ausência de um caminho batch separado.')
gaps('lambda-architecture','As ingestões batch e Kafka foram localizadas; falta ligar as visões ao caminho de consulta e à reconciliação do mesmo dado.')
gaps('event-carried-state-transfer','Os eventos externos estão localizados. Falta conferir que o payload leva o estado necessário e que o consumidor não depende de uma consulta ao produtor.')
gaps('correlation-id','Request ID está verificado. Falta propagar uma identidade de operação entre as requisições e mensagens da mesma jornada.')
gaps('cqrs','Fineract separa leitura e escrita, mas a base JPA é persistência. Falta selecionar e confrontar uma base específica de CQRS com esse uso.')
gaps('horizontal-partitioning','A base define partições; falta uma aplicação consumidora com tabela ou modelo particionado e a regra de roteamento explícitos.')
gaps('geographic-sharding multi-region','O catálogo do servidor implementa placement. Falta uma configuração OSS de aplicação que liga sua população de dados e suas operações às regiões.')
gaps('mapreduce','O motor e a definição de job estão verificados; falta um job consumidor OSS de negócio que ligue Mapper, Reducer e dados.')
gaps('ambassador','A injeção de sidecar foi localizada. Falta demonstrar o proxy que representa o cliente no caminho de saída para a dependência remota.')

# These replacements were read in actual product code after the first author inventory.
for repaired in 'tcc-try-confirm-cancel choreography-saga strangler-fig geographic-sharding multi-region kappa-architecture lambda-architecture outbox-cdc transactional-inbox event-carried-state-transfer retry-queue horizontal-partitioning hateoas eventual-consistency golden-signals use-method-utilization-saturation-errors modular-monolith exactly-once-semantics mapreduce cell-based-architecture ambassador lock-free wait-free conformist serverless vertical-slice-architecture customer-supplier a-b-deployment pac three-phase-commit-3pc space-based-architecture shared-kernel separate-ways clean-architecture onion-architecture ddd ubiquitous-language warm-standby cold-standby bridge actor-model single-writer-principle distributed-lock reservation-pattern fork-join pessimistic-locking load-shedding specification stateless-services two-level-cache write-through write-behind-write-back backend-for-frontend-bff open-host-service published-language api-composition gateway-aggregation adapter facade proxy decorator factory-method abstract-factory iterator interpreter mediator memento oauth2 oidc metrics cqrs secrets-rotation saga orchestration-saga compensating-transaction opentelemetry correlation-id'.split():
 GAPS.pop(repaired,None)

GROUP_SKILLS={1:['architecture','microservices','ddd-specific'],2:['microservices','consensus','locking'],3:['microservices','event-driven','redpanda'],4:['cqrs','event-store'],5:['db','sql','storage','sharding'],6:['cache'],7:['resilience'],8:['concurrency','concurrency-specific'],9:['api','microservices'],10:['architecture','ddd-specific'],11:['migration'],12:['release','gitops'],13:['high-availability'],14:['k8s-security','identity','security'],15:['tracing','metrics','observability'],16:['workflow','workflow-specific'],17:['patterns','gof']}
TREND_SKILL={1:'frontend',2:'process',3:'api',4:'process',5:'process',6:'process',7:'observability',8:'process',9:'api',10:'process',11:'release',12:'release',13:'observability',14:'security',15:'observability',16:'process',17:'process'}
OVERRIDES={**{k:['outbox','event-driven','microservices'] for k in ['transactional-outbox','transactional-inbox','outbox-cdc']},**{k:['saga','workflow-specific']for k in ['saga','choreography-saga','orchestration-saga','compensating-transaction']},**{k:['consensus','locking']for k in ['paxos','raft','consensus','quorum','quorum-read-write','lease','distributed-lock','fencing','fencing-token']},**{k:['cache']for k in ['single-flight','cache-stampede-protection']},'version-vector':['crdt'],'abac':['abac','security'],'rbac':['rbac','k8s-security'],'zero-trust':['identity','security'],'secrets-rotation':['secrets'],'short-lived-credentials':['secrets'],'mvp':['frontend','patterns'],'mvvm':['frontend','patterns'],'mvc':['frontend','architecture'],'component-based-architecture':['frontend']}

def source_item(original):
 value=dict(sources.get(original,{}))
 value.setdefault('url',original)
 repo=value.get('repo') or '/'.join(original.split('/')[3:5])
 value['repo']=repo
 value['repository_metadata']=metadata.get(repo,{})
 if value.get('revision'):
  value['license']=revision_licenses.get(repo+'@'+value['revision'],{})
 else:value['license']=licenses.get(repo,{})
 return value

def evidence(source,terms):
 if source.get('http_status')!=200 or source.get('kind')!='FILE':return []
 text=(ROOT/source['artifact']).read_text(errors='replace');lines=text.splitlines();out=[]
 for term in terms:
  matches=[(index,line)for index,line in enumerate(lines)if term.lower()in line.lower()]
  def score(match):
   index,line=match;stripped=line.strip()
   if stripped.startswith(('import ','package ','use ','#include ','*','//','/*','# ')):return -2
   return sum(token in line for token in ['(',')','=','return ','await ','.'])+(1 if index>20 else 0)
  if matches:
   index,line=max(matches,key=score)
   start=max(0,index-2);end=min(len(lines),index+5)
   out.append({'term':term,'start_line':start+1,'end_line':end,'excerpt':'\n'.join(lines[start:end]),'url':source['url'].split('#')[0]+f'#L{start+1}-L{end}'})
 return out

def skill_item(key):
 candidate=skills[key];item=source_item(candidate['url']);item['key']=key
 item['scope']='FAMILY_GUIDANCE'
 if item.get('http_status')==200:
  text=(ROOT/item['artifact']).read_text(errors='replace')
  first_lines=text.splitlines()[:18];item['declared_scope_excerpt']='\n'.join(first_lines)
 return item

entries=[]
for concept in coverage['concepts']:
 key=concept['concept_id'];sel=selections[key];group=min(g for g in concept['groups'] if g!=18)
 bases=[source_item(u)for u in sel['base_urls']];apps=[source_item(u)for u in sel['application_urls']]
 candidates=[skill_item(k)for k in OVERRIDES.get(key,GROUP_SKILLS[group])]
 candidates.sort(key=lambda x:x['repository_metadata'].get('stars',0),reverse=True)
 for rank,item in enumerate(candidates,1):item['stars_rank_in_subject_candidate_set']=rank
 primary_skill=candidates[0];trend=skill_item(TREND_SKILL[group]);trend['role']='ADJACENT_PROCESS_SUPPORT_NOT_PATTERN_IMPLEMENTATION'
 trend['trending']=next((r for r in trending['rows'] if r['repo']==trend['repo']),None)
 issues=[]
 if key in GAPS:issues.append({'kind':'SEMANTIC_GAP','reason':GAPS[key]})
 if sel.get('application_kind')!='PRODUCT_OSS':issues.append({'kind':'REAL_APPLICATION_MISSING','reason':'O localizador é '+sel.get('application_kind','UNKNOWN')+'. Ele não satisfaz a aplicação OSS real exigida.'})
 for role,items in [('base',bases),('application',apps),('skill',[primary_skill])]:
  for item in items:
   if item.get('kind') in ['FILE','UNRESOLVED_REVISION'] and item.get('http_status')!=200:issues.append({'kind':'SOURCE_UNAVAILABLE','role':role,'url':item['url']})
   if role=='application' and (item.get('license',{}).get('license_spdx')=='Elastic-2.0' or 'sustainable use' in item.get('license',{}).get('excerpt','').lower()):issues.append({'kind':'APPLICATION_NOT_OSS','role':role,'url':item['url'],'reason':'A revisão tem licença source available; ela não é contada como aplicação OSS.'})
   if item.get('license',{}).get('status')!='READ':issues.append({'kind':'LICENSE_UNRESOLVED','role':role,'url':item['url']})
 body_evidence=[{'role':role,'source_url':item['url'],'hits':evidence(item,sel.get('verification_terms',[]))} for role,items in [('base',bases),('application',apps)]for item in items]
 found={hit['term']for file in body_evidence for hit in file['hits']}
 missing=[term for term in sel.get('verification_terms',[])if term not in found]
 if sel.get('verification_terms') and not found:issues.append({'kind':'MECHANISM_NOT_LOCATED','reason':'Nenhum localizador textual do mecanismo foi encontrado nos arquivos selecionados.'})
 # Textual hits are receipts for navigation, never a substitute for the semantic finding above.
 status='PENDING' if issues else 'AUTHOR_SOURCE_MATCH'
 entries.append({'concept_id':key,'canonical_name':concept['canonical_name'],'groups':concept['groups'],'primary_group':group,'priority_entries':concept['priority_entries'],'status':status,'independent_review':'PENDING','base':bases,'application':apps,'application_kind':sel.get('application_kind'),'mechanism':sel['mechanism'],'limits':sel['limits'],'decision_evidence':sel.get('decision_evidence',[]),'research_packet':sel.get('research_packet'),'classification_basis':sel.get('classification_basis'),'source_evidence':body_evidence,'source_locator_terms_not_found':missing,'skill':primary_skill,'skill_candidates':candidates,'skill_candidate_universe':'Only the explicitly selected public SKILL.md candidates in this row; stars compare their parent repositories, not individual skill quality.','trend_support':trend,'issues':issues,'learning':learning_by_id.get(key),'original_reference_paths':concept['reference_paths'],'not_applicable':False})
summary={'canonical_concepts':len(entries),'author_source_matches':sum(e['status']=='AUTHOR_SOURCE_MATCH'for e in entries),'pending_concepts':sum(e['status']=='PENDING'for e in entries),'independently_reviewed_concepts':0,'not_applicable_exemptions':0,'issues_by_kind':dict(collections.Counter(i['kind']for e in entries for i in e['issues']))}
result={'schema_version':'1.0','purpose':'Reconcile the complete 310-concept catalog with exact public sources, dated skill popularity, source licenses and explicit semantic gaps. AUTHOR_SOURCE_MATCH is an author claim awaiting independent review, not a completion certificate.','scope':{'workspace':str(ROOT),'branch':'docs/FBI-4991-arquitetura-aplicada','base_sha':'23d5d158d3a964dceba296296368ec14bcd8970b','generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'source_inventory_sha256':hashlib.sha256((BASE/'existing-sections.json').read_bytes()).hexdigest(),'coverage_sha256':hashlib.sha256((ROOT/'tasks/architecture-course-2026-10-14/evidence/coverage.json').read_bytes()).hexdigest()},'summary':summary,'trend_snapshot':trending,'concepts':entries}
# The full raw receipts remain normalized in sources.json and revision-licenses.json.
def compact_source(source):
 fields=['kind','repo','path','revision','url','http_status','observed_utc','sha256','remote_sha256','original_artifact_sha256','artifact_sha256','artifact_sanitization','artifact','key','scope','stars_rank_in_subject_candidate_set','role','trending']
 compact={k:source[k]for k in fields if k in source}
 compact['license']={k:source.get('license',{}).get(k)for k in ['status','license_spdx','license_expression','url','revision','path','classification_basis']if source.get('license',{}).get(k)is not None}
 meta=source.get('repository_metadata',{});compact['repository_metadata']={k:meta[k]for k in ['stars','observed_utc','archived','pushed_at']if k in meta}
 return compact
serial_entries=[]
for entry in entries:
 compact=dict(entry)
 for role in ['base','application','skill_candidates']:compact[role]=[compact_source(x)for x in entry[role]]
 for role in ['skill','trend_support']:compact[role]=compact_source(entry[role])
 serial_entries.append(compact)
result['concepts']=serial_entries
result['skill_catalog']={key:skill_item(key)for key in skills}
(BASE/'matrix.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
contents=(BASE/'matrix.json').read_bytes()
compressed=gzip.compress(contents,compresslevel=9,mtime=0)
(BASE/'matrix.json.gz').write_bytes(compressed)
publication={'schema_version':1,'source':'matrix.json','archive':'matrix.json.gz','encoding':'gzip','contents_sha256':hashlib.sha256(contents).hexdigest(),'archive_sha256':hashlib.sha256(compressed).hexdigest(),'source_bytes':len(contents),'archive_bytes':len(compressed),'unpack_command':'python3 tasks/FBI-4991-arquitetura-nextra/execution/curation/unpack_matrix.py','note':'The uncompressed generated JSON is local. Static MDX pages do not load this archive during the site build.'}
(BASE/'matrix.publication.json').write_text(json.dumps(publication,indent=2))
publications=[publication]
for stem in ['sources']:
 source_path=BASE/(stem+'.json');source_contents=source_path.read_bytes();source_archive=gzip.compress(source_contents,compresslevel=9,mtime=0)
 (BASE/(stem+'.json.gz')).write_bytes(source_archive)
 record={'schema_version':1,'source':stem+'.json','archive':stem+'.json.gz','encoding':'gzip','contents_sha256':hashlib.sha256(source_contents).hexdigest(),'archive_sha256':hashlib.sha256(source_archive).hexdigest(),'source_bytes':len(source_contents),'archive_bytes':len(source_archive)}
 (BASE/(stem+'.publication.json')).write_text(json.dumps(record,indent=2));publications.append(record)
(BASE/'publication-index.json').write_text(json.dumps(publications,indent=2))

# Render searchable pages with one canonical heading per concept.
DEST=ROOT/'content/referencia/curadoria';DEST.mkdir(parents=True,exist_ok=True)
group_info={g['group']:g for g in coverage['groups']if g['group']!=18}
slugs={g:Path(v['reference_path']).stem for g,v in group_info.items()}

def safe_mdx_text(value):
 parts=re.split(r'(`+[^`]*`+)',value)
 return ''.join(part if part.startswith('`') else part.replace('<','&lt;').replace('>','&gt;').replace('{','&#123;').replace('}','&#125;')for part in parts)

def link_item(item):
 path=item.get('path') or item['repo'];rev=item.get('revision','')
 label=item['repo']+' / '+Path(path).name+((' @ '+rev[:8])if rev else '')
 license=item.get('license',{});spdx=license.get('license_expression') or license.get('license_spdx') or 'identificador não determinado'
 suffix='; licença ['+spdx+']('+license['url']+')'if license.get('url')else '; licença pendente de comprovação'
 return '['+label+']('+item['url']+')'+suffix

for group,info in group_info.items():
 rows=[e for e in entries if e['primary_group']==group]
 title='Curadoria: '+info['title']
 text='---\ntitle: '+json.dumps(title,ensure_ascii=False)+'\ndescription: '+json.dumps('Fontes, skills, versões, licenças e lacunas dos conceitos de '+info['title']+'.',ensure_ascii=False)+'\ndiataxis: reference\n---\n\n# '+title+'\n\n'
 text+='Esta página conserva os conceitos canônicos desta família, com links diretos para as fontes. A contagem de estrelas compara os packs candidatos identificados em cada item. O [método e o recorte datado de tendência](/referencia/curadoria/#como-comparamos-skills) explicam o universo e o período; uma orientação de apoio não implementa o padrão no programa.\n\n'
 text+='Uma correspondência autoral significa que o autor selecionou o mecanismo e suas fontes. A revisão independente desta nova matriz ainda é um gate separado. Uma pendência continua sendo requisito aberto; nenhum conceito recebeu dispensa por não se aplicar.\n\n'
 for row in rows:
  if heading_slugs[row['concept_id']]!=row['concept_id']:text+='<span id=\"'+row['concept_id']+'\" />\n\n'
  text+='## '+row['canonical_name']+'\n\n'
  text+='O identificador canônico é `'+row['concept_id']+'`. '
  if row['status']=='PENDING':text+='**A curadoria deste item permanece pendente.** '+ ' '.join(i.get('reason','A fonte ou a licença precisa ser verificada.')for i in row['issues'])+'\n\n'
  else:text+='**Há uma correspondência autoral com fontes primárias.** A revisão independente precisa conferir esta versão.\n\n'
  text+=safe_mdx_text(row['mechanism'])+'\n\n'
  text+='A base de estudo é '+ '; '.join(link_item(i)for i in row['base'])+'. A aplicação ou candidato de aplicação é '+ '; '.join(link_item(i)for i in row['application'])+'.\n\n'
  skill=row['skill'];stars=skill['repository_metadata'].get('stars');observed=skill['repository_metadata'].get('observed_utc','')
  text+='A orientação pública selecionada é '+link_item(skill)+'. Seu pack tinha **'+str(stars)+' estrelas** na consulta `'+observed+'`. Ele ocupa a primeira posição por estrelas entre as '+str(len(row['skill_candidates']))+' candidatas de assunto selecionadas para este item; esse recorte não é um ranking de todas as skills existentes.\n\n'
  app_hits=[h for f in row['source_evidence']if f['role']=='application'for h in f['hits']]
  if app_hits:
   h=app_hits[0]
   text+='Para localizar o mecanismo, comece pelo [trecho que contém `'+h['term']+'`]('+h['url']+'). O localizador textual ajuda a encontrar o código; a leitura do fluxo e os limites abaixo determinam o que ele comprova.\n\n'
  text+=safe_mdx_text(row['limits'])+'\n\n'
  for decision in row.get('decision_evidence',[]):
   text+='A decisão pública que sustenta esta leitura está na [fonte do responsável pelo produto]('+decision['url']+'). '+safe_mdx_text(decision.get('claim',''))+'\n\n'
  if row['learning']:
   l=row['learning'];text+='No curso, [abra o caso aplicado]('+l['destinations']['journey']+') e [consulte a ação e o probe deste conceito]('+l['destinations']['concept']+'). A prática local ensina o recorte declarado; ela não substitui o código OSS nem comprova uma implantação na nossa stack.\n\n'
 text+='Volte à [matriz completa da curadoria](/referencia/curadoria/).\n'
 (DEST/(slugs[group]+'.mdx')).write_text(text)

packs=['obra/superpowers','mattpocock/skills','addyosmani/agent-skills','wshobson/agents','wondelai/skills','mblode/agent-skills','j4flmao/agent-skills','diagrid-labs/dapr-skills','redpanda-data/skills']
ranked=sorted((metadata[r]for r in packs),key=lambda d:d.get('stars',0),reverse=True)
old={x['repoURL'].removeprefix('https://github.com/'):x for name in ['github-snapshot.json','github-snapshot-supplement.json']for x in json.loads((ROOT/'tasks/architecture-course-2026-10-14/evidence'/name).read_text())}
text='---\ntitle: Curadoria dos 310 conceitos\ndescription: Matriz completa de skills, frameworks e aplicações OSS, com versões, licenças, tendência datada e lacunas explícitas.\ndiataxis: reference\n---\n\n# Curadoria dos 310 conceitos\n\n'
text+='Esta matriz responde ao pedido de uma orientação de agente, uma base de biblioteca ou framework e uma aplicação OSS real para cada conceito. Os **310 conceitos canônicos** possuem uma entrada própria com fontes e situação. Nesta versão autoral, **'+str(summary['author_source_matches'])+'** têm correspondência proposta entre mecanismo e fontes primárias, enquanto **'+str(summary['pending_concepts'])+'** conservam pendências. A revisão independente da nova matriz ainda não foi concluída; esses números não certificam o aceite integral. Nenhum conceito foi dispensado como “não aplicável”.\n\n'
text+='Uma biblioteca mostra como o mecanismo é implementado. Um produto OSS mostra seu uso ou a execução desse mecanismo num sistema real, incluindo produtos de infraestrutura. Um sample, template ou workshop continua identificado como demonstração, mesmo quando executável. Uma documentação ou um localizador que apenas contém o nome do conceito não fecha a correspondência.\n\n'
text+='## Consulte por família\n\n| Família | Conceitos canônicos nesta página | Correspondências autorais | Pendências |\n| --- | ---: | ---: | ---: |\n'
for g,info in group_info.items():
 rows=[e for e in entries if e['primary_group']==g];n=sum(e['status']=='AUTHOR_SOURCE_MATCH'for e in rows)
 text+='| ['+info['title']+'](/referencia/curadoria/'+slugs[g]+'/) | '+str(len(rows))+' | '+str(n)+' | '+str(len(rows)-n)+' |\n'
text+='\nUm conceito presente em várias famílias aparece uma vez nesta curadoria, na primeira família canônica. Sua entrada conserva todos os grupos e os vínculos com os quarenta prioritários. Use a busca do curso pelo nome ou pelo ID do conceito para chegar diretamente à referência.\n\n'
text+='## Como comparamos skills\n\nO universo de popularidade reúne os nove packs abaixo, descobertos nas referências existentes e nas fontes públicas pertinentes. O ranking compara **estrelas totais dos repositórios**, medidas separadamente nos horários indicados. Ele não mede a qualidade de uma skill individual. Dentro de cada conceito, a primeira posição compara somente os SKILL.md candidatos daquele assunto, com seus escopos declarados. Um pack de método pode apoiar a decisão e ainda não ensinar o mecanismo específico.\n\n'
text+='| Posição no universo de packs | Pack | Estrelas observadas | Consulta UTC | Diferença desde o snapshot anterior |\n| --- | --- | ---: | --- | --- |\n'
for rank,m in enumerate(ranked,1):
 o=old.get(m['repository']);delta=m['stars']-o['stars']if o else None
 diff=(('+'if delta>=0 else '')+str(delta)+' desde '+o['observedUTC'])if o else 'Não há snapshot anterior comparável.'
 text+='| '+str(rank)+' | ['+m['repository']+']('+m['url']+') | '+str(m['stars'])+' | `'+m['observed_utc']+'` | '+diff+' |\n'
text+='\nAs diferenças acima pertencem ao intervalo real entre as duas consultas de 14 e 15 de outubro. Elas **não são crescimento de trinta dias**, não foram anualizadas e não substituem uma série histórica.\n\n'
text+='Na [página mensal GitHub Trending]('+trending['source_url']+'), a resposta HTTP 200 salva em `'+trending['observed_utc']+'` continha **22 cards de repositório**. `addyosmani/agent-skills` ocupava a **posição 15** e a página informava **12.981 estrelas neste mês**. Ele foi o único dos nove packs desta seleção que apareceu nesses 22 cards. Esse é o sinal mensal disponível para o universo observado; não significa que ele foi a skill mais adequada ou mais crescente de cada padrão de arquitetura. A ausência de um pack nesses cards não significa crescimento zero.\n\n'
text+='Cada entrada da matriz liga uma skill pertinente ao assunto. O pack Addy Osmani fornece apoio adicional em API, interface, segurança, automação, observabilidade ou documentação conforme a família. Esse apoio aparece no JSON como `trend_support`, com o papel adjacente explicitado; ele não foi usado para declarar uma skill específica de PAC, 3PC ou outro mecanismo raro.\n\n'
text+='## Como ler as versões e licenças\n\nOs links de código foram resolvidos para SHAs imutáveis antes da leitura. A licença aparece ligada ao arquivo lido na mesma revisão, quando a fonte é um arquivo. As versões históricas permanecem históricas: Medusa 1.20.10, Vault 1.14 e MediatR 12.4.1 não representam automaticamente as versões atuais ou suas condições atuais. Um identificador SPDX ausente ou indefinido continua visível; uma classificação da API não substitui o texto da licença. Esta matriz não é uma decisão de adoção ou de compatibilidade jurídica.\n\n'
text+='A descoberta anterior incluía NCATS Blackboard sem licença comprovada. A referência atual compara BehaviorTree.CPP com Navigation2 e mantém o limite do controle por árvore de comportamento. O arquivo de descoberta preserva o candidato anterior para que a reconciliação seja auditável.\n\n'
text+='## Artefatos para reproduzir a leitura\n\nA matriz completa é publicada em `tasks/FBI-4991-arquitetura-nextra/execution/curation/matrix.json.gz`, junto com o manifesto de hashes e o helper `unpack_matrix.py`. A cópia integral `matrix.json` é um artefato local restaurável. `sources.json` conserva URL, HTTP, horário, SHA, caminho, hash e trechos. `revision-licenses.json` conserva a prova de licença por revisão. `github-metadata.json` e `trending-monthly.json` conservam as medições de popularidade e seu universo. Os scripts `harvest.py`, `license_revisions.py` e `build_matrix.py` ficam no mesmo diretório. Reexecutar a coleta produz uma nova medição; não transforma o snapshot antigo em estado atual.\n\n'
text+='Para estudar o problema e repetir uma condição conhecida, siga as [jornadas aplicadas](/jornadas/). A [tabela dos quarenta prioritários](/referencia/prioritarios/) conserva a ordem do pedido e liga os padrões ao estudo.\n'
(DEST/'index.mdx').write_text(text)
(DEST/'_meta.js').write_text('export default '+json.dumps({'index':'Matriz e método',**{slugs[g]:info['title']for g,info in group_info.items()}},ensure_ascii=False,indent=2)+'\n')
(BASE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False))
