"""Normalize and bind all 51 author repair proposals before the single integration."""
import copy
import datetime
import hashlib
import json
import re
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
FROZEN=BASE.parent/'curation'
FILES=[
 'two-highs-source-recommendations.json','additional-four-highs-source-recommendations.json',
 'cache-and-concurrency-recommendations.json','product-flow-recommendations.json',
 'base-five/recommendations.json','base-five/wave-two/recommendations.json','base-five/wave-three/recommendations.json',
 'rare-runtime/rare-runtime-recommendations.json','rare-security/rare-security-recommendations.json',
 'rare-service-mesh/rare-service-mesh-recommendation.json']
digest=lambda b:hashlib.sha256(b).hexdigest()
rows=[]
errors=[]
artifacts={}
frozen_licenses=json.loads((FROZEN/'revision-licenses.json').read_text())
omitted_context=[]
license_pool={}
def collect_licenses(value):
 if isinstance(value,dict):
  if value.get('artifact') and value.get('revision') and value.get('repo') and ('LICENSE' in value.get('path','').upper() or value.get('path')=='doc/COPYING'):
   license_pool[(value['repo'],value['revision'])]=value
  for child in value.values():collect_licenses(child)
 elif isinstance(value,list):
  for child in value:collect_licenses(child)
for file in FILES:collect_licenses(json.loads((BASE/file).read_text()))

def check_bytes(record,kind):
 path=ROOT/record.get('artifact','__missing__')
 if not path.is_file():errors.append([kind,'MISSING',str(path)]);return []
 raw=path.read_bytes();actual=digest(raw)
 if actual!=record.get('sha256'):errors.append([kind,'HASH',record.get('url'),record.get('sha256'),actual])
 artifacts[str(path.relative_to(ROOT))]=actual
 return raw.decode().splitlines()

def normalize_source(record,license_record=None):
 out=copy.deepcopy(record)
 out['kind']='FILE'
 out['url']=out['url'].split('#')[0]
 if not re.fullmatch('[0-9a-f]{40}',out.get('revision','')):errors.append(['UNPINNED',out['url']])
 if out.get('http_status')!=200:errors.append(['HTTP',out['url']])
 lines=check_bytes(out,'SOURCE')
 license_record=copy.deepcopy(license_record or out.get('license') or {})
 if not license_record.get('artifact') or license_record.get('revision')!=out['revision']:
  replacement=license_pool.get((out['repo'],out['revision']))
  if replacement:
   old_reference={k:license_record.get(k) for k in ['url','revision','path']}
   license_record=copy.deepcopy(replacement)
   license_record['replaced_compact_reference']=old_reference
 if not license_record.get('artifact'):
  saved=frozen_licenses.get(out['repo']+'@'+out['revision'],{})
  if saved.get('url')==license_record.get('url'):
   license_record={**copy.deepcopy(saved),**license_record}
 license_record.setdefault('status','READ')
 license_lines=check_bytes(license_record,'LICENSE')
 license_text='\n'.join(license_lines)
 if license_record.get('license_spdx') in [None,'NOASSERTION']:
  if 'Permission is hereby granted, free of charge' in license_text and 'THE SOFTWARE IS PROVIDED "AS IS"' in license_text:
   license_record['license_spdx']='MIT'
   license_record['classification_basis']='The full captured text contains the MIT grant and disclaimer.'
  elif 'Redistribution and use in source and binary forms' in license_text and ('contributors may be used to endorse' in license_text or 'contributors may not be used to endorse' in license_text):
   license_record['license_spdx']='BSD-3-Clause'
   license_record['classification_basis']='The full captured text contains redistribution conditions and the non-endorsement clause.'
 if license_record.get('license_spdx') in [None,'NOASSERTION','NONE']:errors.append(['LICENSE_IDENTIFIER',out['url'],license_record.get('license_spdx')])
 if license_record.get('status')!='READ':errors.append(['LICENSE_STATE',out['url']])
 if license_record.get('revision')!=out['revision']:errors.append(['LICENSE_REVISION',out['url'],license_record.get('revision')])
 out['license']=license_record
 return out,lines

def hits_from_source(record,lines):
 evidence=record.get('evidence')
 if evidence is None:
  evidence=[dict(start_line=a,end_line=b,claim=record.get('proves')) for a,b in record.get('inspected_ranges',[])]
 result=[]
 for e in evidence:
  start,end=e['start_line'],e['end_line']
  if not 1<=start<=end<=len(lines):errors.append(['SPAN',record['url'],start,end]);continue
  excerpt='\n'.join(lines[start-1:end])
  if 'excerpt' in e and e['excerpt']!=excerpt:
   numbered='\n'.join(re.sub(r'^\d+: ', '', line) for line in e['excerpt'].splitlines())
   if numbered!=excerpt:errors.append(['EXCERPT',record['url'],start,end])
  if e.get('excerpt_sha256') and e['excerpt_sha256']!=digest(excerpt.encode()):errors.append(['EXCERPT_HASH',record['url'],start,end])
  claim=e.get('claim') or e.get('term') or record.get('claim') or record.get('proves')
  if not claim:errors.append(['CLAIM_MISSING',record['url'],start,end]);continue
  result.append(dict(start_line=start,end_line=end,excerpt=excerpt,excerpt_sha256=digest(excerpt.encode()),
                     claim=claim,url=record['url']+f'#L{start}-L{end}'))
 return result

def rare_role(concept,record):
 repo=record['repo'];role=record['role']
 if role=='base':return 'base'
 if concept=='graphql-federation' and repo=='wundergraph/graphql-go-tools':return 'base'
 if concept=='distributed-tracing' and repo=='airlift/airlift':return 'base'
 if concept=='zero-trust' and repo=='golang/crypto':return 'base'
 if concept=='service-to-service-identity' and repo=='spiffe/go-spiffe':return 'base'
 if concept=='token-exchange' and repo=='spring-projects/spring-security':return 'base'
 if concept=='service-mesh' and repo=='envoyproxy/envoy':return 'base'
 return 'application'

for file in FILES:
 path=BASE/file;packet=json.loads(path.read_text())
 candidates=packet.get('rows') or packet.get('concepts') or []
 for candidate in candidates:
  row=copy.deepcopy(candidate)
  key=row['concept_id']
  decision=row.get('decision',row.get('recommendation'))
  if decision not in ['AUTHOR_SOURCE_MATCH_REPAIR','RECOMMEND_AUTHOR_SOURCE_MATCH'] and not str(decision).startswith('RECOMMEND_AUTHOR_SOURCE_MATCH'):
   errors.append(['DECISION',file,key,decision])
  if 'base' not in row:
   row['base']=[];row['application']=[]
   for record in row['evidence']:
    role=rare_role(key,record)
    license_record=packet['licenses'][record['repo']+'@'+record['revision']]
    normalized,lines=normalize_source(record,license_record)
    normalized['evidence']=hits_from_source(record,lines)
    row[role].append(normalized)
   row['application_kind']='INFRASTRUCTURE_OSS'
   if isinstance(row.get('limits'),list):row['limits']=' '.join(row['limits'])
   row['classification_basis']=row.get('base_role','')+' '+row.get('application_role','')
  else:
   helper_evidence={(e['role'],e['source_url'].split('#')[0]):e for e in row.get('source_evidence',[])}
   for role in ['base','application']:
    normalized=[]
    for record in row[role]:
     helper=helper_evidence.get((role,record['url'].split('#')[0]))
     if not helper and not record.get('evidence'):
      omitted_context.append(dict(concept_id=key,role=role,url=record['url'],reason='The proposal supplied no adjudicated span for this supplementary context source; it cannot contribute to a positive mechanism judgment.'))
      continue
     out,lines=normalize_source(record)
     if helper:
      out['evidence']=hits_from_source(dict(out,evidence=helper['hits']),lines)
     else:out['evidence']=hits_from_source(record,lines)
     if not out['evidence']:
      # Sources such as exact dependency manifests remain selected only with an explicit span.
      errors.append(['EVIDENCE_MISSING',key,role,out['url']])
     normalized.append(out)
    row[role]=normalized
  row['decision']='AUTHOR_SOURCE_MATCH_REPAIR'
  row['independent_review']='PENDING'
  row['remaining_gates']=[]
  row['repair_packet']=str(path.relative_to(ROOT))
  row['repair_packet_sha256']=digest(path.read_bytes())
  row['checked_by']='curation_complete author integration, gpt-6.1-sol/xhigh'
  row['checked_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  rows.append(row)

baseline=json.loads((BASE/'first-pass-semantic-baseline.json').read_text())
review_highs={r['concept_id']for r in json.loads((BASE/'repair-inventory.json').read_text())['highs']}
ids=[r['concept_id']for r in rows]
if len(ids)!=len(set(ids)):errors.append(['DUPLICATE_CONCEPT'])
if set(ids)!=review_highs:errors.append(['HIGH_COVERAGE',sorted(set(ids)-review_highs),sorted(review_highs-set(ids))])
sha=digest((FROZEN/'matrix.json').read_bytes())
if sha!='a4b12f6c6aa8b1883d8f6c1ac7ed1c7f81d829859422f5a0212f7fd1cca6689e':errors.append(['FREEZE_MUTATED',sha])
output=dict(schema_version=1,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            frozen_matrix_sha256=sha,scope='51 author repairs; 259 other semantic fingerprints are preserved.',
            independent_review='PENDING',context_only_sources_omitted=omitted_context,rows=sorted(rows,key=lambda r:r['concept_id']))
path=BASE/'consolidated-recommendations.json';path.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
receipt=dict(recorded_utc=output['recorded_utc'],concepts=len(rows),unique_concepts=len(set(ids)),high_coverage=len(set(ids)&review_highs),
             source_role_counts={role:sum(len(r[role])for r in rows)for role in ['base','application']},
             unique_artifacts=len(artifacts),artifact_hash_errors=sum(e[0] in ['SOURCE','LICENSE'] and len(e)>1 and e[1]=='HASH' for e in errors),errors_count=len(errors),errors=errors,
             context_only_sources_omitted=len(omitted_context),
             matrix_frozen_sha256=sha,consolidated_sha256=digest(path.read_bytes()),independent_review='PENDING')
(BASE/'consolidation-receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(receipt,ensure_ascii=False))
raise SystemExit(bool(errors))
