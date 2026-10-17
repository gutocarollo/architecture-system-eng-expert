#!/usr/bin/env python3
"""Create a complete, evidence-bound author matrix without laundering partial matches."""
import collections,datetime,gzip,hashlib,json,re
from pathlib import Path
from adjudication_gate import adjudication_issues, carry_forward_issues, independent_decision_issues
from semantic_fingerprints import semantic_fingerprint
from license_classification import scoped_license
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
load=lambda name:json.loads((BASE/name).read_text())
coverage=json.loads((ROOT/'tasks/architecture-course-2026-10-14/evidence/coverage.json').read_text())
selections=load('source-selections.json');sources=load('sources.json');metadata=load('github-metadata.json');licenses=load('licenses.json');revision_licenses=load('revision-licenses.json');skills=load('skill-candidates.json');trending=load('trending-monthly.json')
learning=json.loads((ROOT/'tasks/FBI-4991-arquitetura-nextra/execution/learning/concept-matrix.json').read_text())
learning_by_id={x['concept_id']:x for x in learning['concepts']}
heading_slugs=load('heading-slugs.json')
assert {x['concept_id'] for x in coverage['concepts']}==set(selections)

# Current author judgments and fingerprint-bound first-pass reviews are the only positive gates.
adjudications=load('author-adjudications.json')
review_baseline=load('review-baseline.json')
baseline_by_id={row['concept_id']:row for row in review_baseline['concepts']}
closure_path=BASE.parent/'curation-repairs/independent-closure.json'
closure=json.loads(closure_path.read_text()) if closure_path.exists() else {}
closure_by_id={row['concept_id']:row for row in closure.get('concepts',[])}

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
  value['license']=value.get('source_license') or revision_licenses.get(repo+'@'+value['revision'],{})
 else:value['license']=licenses.get(repo,{})
 value['license']=scoped_license(value,value['license'],ROOT)
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
 if sel.get('application_kind') not in ['PRODUCT_OSS','INFRASTRUCTURE_OSS']:issues.append({'kind':'REAL_APPLICATION_MISSING','reason':'O localizador é '+sel.get('application_kind','UNKNOWN')+'. Ele não satisfaz a aplicação OSS real exigida.'})
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
 entry={'concept_id':key,'canonical_name':concept['canonical_name'],'groups':concept['groups'],'primary_group':group,'priority_entries':concept['priority_entries'],'status':status,'independent_review':'PENDING','base':bases,'application':apps,'application_kind':sel.get('application_kind'),'mechanism':sel['mechanism'],'limits':sel['limits'],'decision_evidence':sel.get('decision_evidence',[]),'research_packet':sel.get('research_packet'),'classification_basis':sel.get('classification_basis'),'source_evidence':body_evidence,'source_locator_terms_not_found':missing,'skill':primary_skill,'skill_candidates':candidates,'skill_candidate_universe':'Only the explicitly selected public SKILL.md candidates in this row; stars compare their parent repositories, not individual skill quality.','trend_support':trend,'issues':issues,'learning':learning_by_id.get(key),'original_reference_paths':concept['reference_paths'],'not_applicable':False}
 adjudication=adjudications.get(key)
 if adjudication:
  issues.extend(adjudication_issues(key,sel,sources,adjudication,ROOT))
  explicit=[]
  for proof in adjudication['primary_evidence']:
   item=source_item(proof['source_url'])
   lines=(ROOT/item['artifact']).read_text().splitlines()
   hit={'term':proof['claim'],'claim':proof['claim'],'start_line':proof['start_line'],'end_line':proof['end_line'],
        'excerpt':'\n'.join(lines[proof['start_line']-1:proof['end_line']]),'excerpt_sha256':proof['excerpt_sha256'],'url':proof['url']}
   matching=next((record for record in explicit if record['role']==proof['role'] and record['source_url']==proof['source_url']),None)
   if matching:matching['hits'].append(hit)
   else:explicit.append({'role':proof['role'],'source_url':proof['source_url'],'hits':[hit]})
  entry['source_evidence']=explicit
  entry['author_adjudication']={field:adjudication[field]for field in ['decision','checked_by','checked_at_utc','selection_fingerprint','remaining_gates','repair_packet','repair_packet_sha256']}
 else:
  prior=baseline_by_id.get(key)
  carry_issues=(independent_decision_issues(entry,closure_by_id[key],ROOT) if key in closure_by_id else carry_forward_issues(entry,prior,ROOT))
  if not prior or prior.get('carry_eligible') is not True:
   carry_issues.append({'kind':'AUTHOR_ADJUDICATION_MISSING','reason':'A repaired concept still requires its explicit current author judgment.'})
  issues.extend(carry_issues)
  if not carry_issues:
   entry['independent_review']=prior['first_pass']['state']
   entry['independent_review_detail']=prior['first_pass']
   entry['author_adjudication']={'decision':'AUTHOR_SOURCE_MATCH','origin':'UNCHANGED_INDEPENDENT_FIRST_PASS','semantic_fingerprint':prior['semantic_fingerprint'],'remaining_gates':[]}
 if key in closure_by_id:
  decision=closure_by_id[key]
  closure_issues=independent_decision_issues(entry,decision,ROOT)
  issues.extend(closure_issues)
  if not closure_issues:
   entry['independent_review']=decision['state']
   entry['independent_review_detail']={field:decision[field] for field in ['state','origin','review_path','review_sha256','reviewed_utc','reviewed_matrix_sha256']}
 entry['status']='PENDING' if issues else 'AUTHOR_SOURCE_MATCH'
 entry['semantic_fingerprint']=semantic_fingerprint(entry)
 entries.append(entry)
summary={'canonical_concepts':len(entries),'author_source_matches':sum(e['status']=='AUTHOR_SOURCE_MATCH'for e in entries),'pending_concepts':sum(e['status']=='PENDING'for e in entries),'independently_reviewed_concepts':sum(e['independent_review']!='PENDING'for e in entries),'independent_recheck_pending':sum(e['independent_review']=='PENDING'for e in entries),'independent_states':dict(collections.Counter(e['independent_review']for e in entries)),'not_applicable_exemptions':0,'issues_by_kind':dict(collections.Counter(i['kind']for e in entries for i in e['issues']))}
result={'schema_version':'1.0','purpose':'Reconcile the complete 310-concept catalog with exact public sources, dated skill popularity, source licenses and explicit semantic gaps. AUTHOR_SOURCE_MATCH alone is an author claim. Independent decisions are imported from actual review receipts and remain bounded to each documented mechanism.','scope':{'workspace':str(ROOT),'branch':'docs/FBI-4991-arquitetura-aplicada','base_sha':'23d5d158d3a964dceba296296368ec14bcd8970b','generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'source_inventory_sha256':hashlib.sha256((BASE/'existing-sections.json').read_bytes()).hexdigest(),'coverage_sha256':hashlib.sha256((ROOT/'tasks/architecture-course-2026-10-14/evidence/coverage.json').read_bytes()).hexdigest()},'summary':summary,'trend_snapshot':trending,'concepts':entries}
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
(BASE/'matrix.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
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
 text+='Uma correspondência autoral registra a seleção do mecanismo e de suas fontes. A situação independente vem do parecer real vinculado a cada item e vale para o recorte e os limites declarados. Uma pendência continua sendo requisito aberto; nenhum conceito recebeu dispensa por não se aplicar.\n\n'
 for row in rows:
  if heading_slugs[row['concept_id']]!=row['concept_id']:text+='<span id=\"'+row['concept_id']+'\" />\n\n'
  text+='## '+row['canonical_name']+'\n\n'
  text+='O identificador canônico é `'+row['concept_id']+'`. '
  if row['status']=='PENDING':text+='**A curadoria deste item permanece pendente.** '+ ' '.join(i.get('reason','A fonte ou a licença precisa ser verificada.')for i in row['issues'])+'\n\n'
  elif row['independent_review']!='PENDING':text+='**A revisão independente aceitou este recorte delimitado.** O mecanismo e os limites abaixo foram conferidos; as observações da revisão continuam nos recibos vinculados ao item.\n\n'
  else:text+='**Há uma correspondência autoral reparada com fontes primárias.** A rechecagem independente desta versão continua pendente.\n\n'
  text+=safe_mdx_text(row['mechanism'])+'\n\n'
  text+='A base de estudo é '+ '; '.join(link_item(i)for i in row['base'])+'. A aplicação ou candidato de aplicação é '+ '; '.join(link_item(i)for i in row['application'])+'.\n\n'
  skill=row['skill'];stars=skill['repository_metadata'].get('stars');observed=skill['repository_metadata'].get('observed_utc','')
  text+='A orientação pública selecionada é '+link_item(skill)+'. Seu pack tinha **'+str(stars)+' estrelas** na consulta `'+observed+'`. Ele ocupa a primeira posição por estrelas entre as '+str(len(row['skill_candidates']))+' candidatas de assunto selecionadas para este item; esse recorte não é um ranking de todas as skills existentes.\n\n'
  app_hits=[h for f in row['source_evidence']if f['role']=='application'for h in f['hits']]
  if app_hits:
   h=app_hits[0]
   text+='Para conferir o mecanismo no produto, comece por [este trecho do código]('+h['url']+'). '+safe_mdx_text(h.get('claim','O localizador textual ajuda a encontrar o fluxo; ele não substitui a leitura do mecanismo e de seus limites.'))+'\n\n'
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
text+='Esta curadoria reúne **310 conceitos de arquitetura** para consulta. Cada conceito tem uma entrada com referências para estudar o mecanismo, comparar bibliotecas ou frameworks e observar seu uso em produtos de código aberto. Abra a família do assunto que você procura ou use a busca pelo nome do conceito.\n\nA página [Arquitetura na prática: Makershub](/referencia/prioritarios/) oferece uma seleção de 40 temas para começar. Alguns temas reúnem vários conceitos, como Retry, Exponential Backoff e Jitter. Já a [matriz de conceitos e casos](/jornadas/matriz/) distribui os 310 conceitos entre 15 casos principais de estudo. As 17 famílias abaixo organizam os conceitos por assunto; os 15 casos os organizam pelo problema que você pode investigar.\n\nUma fonte de código mostra um recorte do mecanismo em uma biblioteca ou em um produto. Um exercício permite observar uma condição e comparar seus efeitos. Consulte os limites de cada entrada antes de aplicar a ideia: uma comparação local pode ensinar um requisito do padrão sem implementar o protocolo completo ou comprovar seu uso em produção.\n\n'

text+='## Consulte por família\n\n| Família de assuntos | Conceitos distintos nesta família |\n| --- | ---: |\n'
for g,info in group_info.items():
 rows=[e for e in entries if e['primary_group']==g];n=sum(e['status']=='AUTHOR_SOURCE_MATCH'for e in rows)
 text+='| ['+info['title']+'](/referencia/curadoria/'+slugs[g]+'/) | '+str(len(rows))+' |\n'
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
text+='Para estudar o problema e repetir uma condição conhecida, siga as [jornadas aplicadas](/jornadas/). A [seleção Arquitetura na prática: Makershub](/referencia/prioritarios/) conserva a ordem do pedido e liga os padrões ao estudo.\n'
(DEST/'index.mdx').write_text(text)
(DEST/'_meta.js').write_text('export default '+json.dumps({'index':'Matriz e método',**{slugs[g]:info['title']for g,info in group_info.items()}},ensure_ascii=False,indent=2)+'\n')
(BASE/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False))
