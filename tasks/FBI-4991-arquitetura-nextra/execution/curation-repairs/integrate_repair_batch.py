"""Apply the one authorized batch after all 51 proposals pass receipt validation."""
import copy
import datetime
import gzip
import hashlib
import json
from pathlib import Path
from proposed_adjudication_gate import selection_fingerprint

BASE=Path(__file__).resolve().parent
DEST=BASE.parent/'curation'
ROOT=BASE.parents[3]
load=lambda path:json.loads(path.read_text())
digest=lambda data:hashlib.sha256(data).hexdigest()
receipt=load(BASE/'consolidation-receipt.json')
assert receipt['concepts']==51 and receipt['high_coverage']==51 and receipt['errors_count']==0
packet=load(BASE/'consolidated-recommendations.json')
assert digest((BASE/'consolidated-recommendations.json').read_bytes())==receipt['consolidated_sha256']
frozen=(DEST/'matrix.json').read_bytes()
assert digest(frozen)==receipt['matrix_frozen_sha256']
(BASE/'first-pass-matrix.json.gz').write_bytes(gzip.compress(frozen,compresslevel=9,mtime=0))
source_index=load(DEST/'sources.json')
license_index=load(DEST/'revision-licenses.json')
metadata=load(DEST/'github-metadata.json')
repo_receipts=load(BASE/'repository-receipts.json')
selections=load(DEST/'source-selections.json')
repairs={}
for row in packet['rows']:
 key=row['concept_id']
 for role in ['base','application']:
  for item in row[role]:
   record=copy.deepcopy(item)
   record['kind']='FILE'
   record['source_license']=record.pop('license')
   record['repair_provenance']=row['repair_packet']
   record.pop('evidence',None)
   source_index[record['url']]=record
   license_key=record['repo']+'@'+record['revision']
   if license_key not in license_index or license_index[license_key].get('status')!='READ':
    license_index[license_key]=copy.deepcopy(record['source_license'])
   if record['repo'] not in metadata:
    repo_meta=item.get('repository_metadata') or repo_receipts.get(record['repo']) or {}
    if repo_meta:metadata[record['repo']]=copy.deepcopy(repo_meta)
 old=selections[key]
 repairs[key]=dict(base_urls=[s['url']for s in row['base']],application_urls=[s['url']for s in row['application']],
                   mechanism=row['mechanism'],limits=row['limits'],application_kind=row['application_kind'],
                   verification_terms=[],decision_evidence=[],
                   research_packet=row['repair_packet'],
                   classification_basis=row.get('classification_basis',row.get('pairing_relationship','')),
                   supersedes_first_pass_matrix_sha256=receipt['matrix_frozen_sha256'])
 if row.get('official_context'):
  repairs[key]['decision_evidence']=[dict(url=x['url'],claim=x.get('proves',x.get('claim','Contexto primário de suporte.')))for x in row['official_context'] if x.get('url')]
 elif row.get('primary_documentation'):
  repairs[key]['decision_evidence']=[dict(url=x['url'],claim=x.get('claim','Contexto primário de suporte.'))for x in row['primary_documentation'] if x.get('url')]

adjudications={}
for row in packet['rows']:
 key=row['concept_id'];evidence=[]
 for role in ['base','application']:
  for item in row[role]:
   for span in item['evidence']:
    evidence.append(dict(role=role,source_url=item['url'],source_sha256=item['sha256'],start_line=span['start_line'],
                         end_line=span['end_line'],excerpt_sha256=span['excerpt_sha256'],claim=span['claim'],url=span['url']))
 adjudications[key]=dict(concept_id=key,decision='AUTHOR_SOURCE_MATCH',remaining_gates=[],
    checked_by=row['checked_by'],checked_at_utc=row['checked_at_utc'],basis=row['mechanism'],
    selection_fingerprint=selection_fingerprint(key,repairs[key],source_index),primary_evidence=evidence,
    repair_packet=row['repair_packet'],repair_packet_sha256=row['repair_packet_sha256'],independent_review='PENDING')
baseline=load(BASE/'first-pass-semantic-baseline.json')
for row in baseline['concepts']:row['first_pass'].pop('evidence',None)
for name,data in [('sources.json',source_index),('revision-licenses.json',license_index),('github-metadata.json',metadata),
                  ('repair-selections.json',repairs),('author-adjudications.json',adjudications),('review-baseline.json',baseline)]:
 (DEST/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(repair_selections=len(repairs),author_adjudications=len(adjudications),
    preserved_baseline=sum(x['carry_eligible']for x in baseline['concepts']),
    original_matrix_sha256=digest(frozen),source_index_records=len(source_index))))
