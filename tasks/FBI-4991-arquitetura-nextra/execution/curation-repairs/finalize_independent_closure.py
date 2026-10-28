"""Import actual review judgments and apply only the two authorized license classifications."""
import collections
import copy
import datetime
import gzip
import hashlib
import json
import sys
from pathlib import Path

BASE=Path(__file__).resolve().parent
CUR=BASE.parent/'curation'
ROOT=BASE.parents[3]
sys.path.insert(0,str(CUR))
from adjudication_gate import selection_fingerprint, source_lookup
from license_classification import scoped_license
from semantic_fingerprints import semantic_fingerprint, mechanism_fingerprint

load=lambda path:json.loads(path.read_text())
digest=lambda raw:hashlib.sha256(raw).hexdigest()
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
reviewed_sha='fa8e01dcc2bd0126ac085eed97452dff6d193448f588c9a078201fab259ddde0'
raw=(CUR/'matrix.json').read_bytes();assert digest(raw)==reviewed_sha
(BASE/'rechecked-matrix-fa8e01.json.gz').write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
old=load(CUR/'matrix.json');old_rows={r['concept_id']:r for r in old['concepts']}
sources=load(CUR/'sources.json');licenses=load(CUR/'revision-licenses.json')
lookup=source_lookup(sources)
source_hashes={k:(s.get('revision'),s.get('sha256'),s.get('artifact'))for k,s in sources.items()}
changes=[];expected=copy.deepcopy(old_rows)
for key,row in expected.items():
 for role in ['base','application']:
  for item in row[role]:
   if item['repo']!='python/cpython' and not (key=='database-decomposition' and item['repo']=='gitlabhq/gitlabhq' and item['path']=='doc/development/database/multiple_databases.md'):
    continue
   current=lookup[item['url']]
   proof=current.get('source_license') or licenses[current['repo']+'@'+current['revision']]
   corrected=scoped_license(current,proof,ROOT)
   before=item['license'];after=copy.deepcopy(before)
   after['license_spdx']=corrected.get('license_spdx')
   if before!=after:
    assert ((item['repo']=='python/cpython' and before['license_spdx']=='PostgreSQL' and after['license_spdx']=='Python-2.0')
      or (key=='database-decomposition' and item['repo']=='gitlabhq/gitlabhq'
          and item['path']=='doc/development/database/multiple_databases.md'
          and before['license_spdx']=='MIT' and after['license_spdx']=='CC-BY-SA-4.0'))
    changes.append(dict(concept_id=key,role=role,source_url=item['url'],path=item['path'],
       source_revision=item['revision'],source_sha256=item['sha256'],before=before,after=after,
       license_artifact=corrected['artifact'],license_artifact_sha256=corrected['sha256'],
       basis=corrected['classification_basis']))
    item['license']=after
for url,record in sources.items():
 if record.get('repo')=='python/cpython' or (record.get('repo')=='gitlabhq/gitlabhq'and record.get('path')=='doc/development/database/multiple_databases.md'):
  proof=record.get('source_license') or licenses.get(record['repo']+'@'+record.get('revision',''))
  if proof:
   corrected=scoped_license(record,proof,ROOT)
   if record.get('source_license') or record.get('repo')=='gitlabhq/gitlabhq':record['source_license']=corrected
for key,proof in licenses.items():
 if proof.get('repo')=='python/cpython':licenses[key]=scoped_license(dict(repo='python/cpython',path='Lib/'),proof,ROOT)
assert source_hashes=={k:(s.get('revision'),s.get('sha256'),s.get('artifact'))for k,s in sources.items()}
assert len(changes)==12 and collections.Counter(c['after']['license_spdx']for c in changes)=={'Python-2.0':11,'CC-BY-SA-4.0':1}
assert all(mechanism_fingerprint(old_rows[k])==mechanism_fingerprint(expected[k])for k in old_rows)
metadata=dict(schema_version=1,observed_utc=now,reviewed_matrix_sha256=reviewed_sha,
 scope='Two authorized license classifications; no source bytes, code revisions, mechanisms, limits or skills changed.',
 concepts_with_license_delta=len(changes),source_content_changes=0,mechanism_fingerprints_preserved=310,
 primary_identifier_references=['https://spdx.org/licenses/Python-2.0.html','https://spdx.org/licenses/PSF-2.0.html'],
 changes=changes)
metadata_path=BASE/'license-metadata-corrections.json';metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
metadata_sha=digest(metadata_path.read_bytes())

baseline=load(CUR/'review-baseline.json');decisions={}
for row in baseline['concepts']:
 if not row['carry_eligible']:continue
 key=row['concept_id'];prior=row['first_pass'];assert row['semantic_fingerprint']==semantic_fingerprint(old_rows[key])
 assert digest((ROOT/prior['review_path']).read_bytes())==prior['review_sha256']
 decisions[key]=dict(concept_id=key,state=prior['state'],origin='FIRST_PASS',review_path=prior['review_path'],
   review_sha256=prior['review_sha256'],reviewed_utc=prior.get('reviewed_utc'),
   reviewed_matrix_sha256=baseline['matrix_sha256'],reviewed_semantic_fingerprint=row['semantic_fingerprint'],
   notes=prior.get('notes',''))
reports=[]
for name,count in [('curation-independent.recheck.json',20),('curation-second.recheck.json',31)]:
 path=BASE.parent/'reviews'/name;report=load(path);report_sha=digest(path.read_bytes())
 assert report['matrix_sha256']==reviewed_sha and report['model']=='gpt-6.1-sol' and len(report['concepts'])==count
 assert report.get('residual_high_count',0)==0 and report.get('residual_high',[])==[]
 reports.append(dict(path=str(path.relative_to(ROOT)),sha256=report_sha,concepts=count,states=dict(collections.Counter(r['state']for r in report['concepts']))))
 for row in report['concepts']:
  key=row['concept_id'];assert key not in decisions and row['state']=='APPROVED_BOUNDED'
  assert row['semantic_fingerprint']==semantic_fingerprint(old_rows[key])
  decisions[key]=dict(concept_id=key,state=row['state'],origin='WARM_RECHECK',review_path=str(path.relative_to(ROOT)),
    review_sha256=report_sha,reviewed_utc=row.get('reviewed_utc',report.get('observed_utc')),
    reviewed_matrix_sha256=reviewed_sha,reviewed_semantic_fingerprint=row['semantic_fingerprint'],
    notes=row.get('notes',row.get('closure','')))
assert set(decisions)==set(old_rows) and len(decisions)==310
for key,decision in decisions.items():
 decision['mechanism_fingerprint']=mechanism_fingerprint(old_rows[key])
 decision['expected_final_semantic_fingerprint']=semantic_fingerprint(expected[key])
 affected=[c for c in changes if c['concept_id']==key]
 if affected:decision['license_metadata_correction']=dict(path=str(metadata_path.relative_to(ROOT)),sha256=metadata_sha)
closure=dict(schema_version=1,observed_utc=now,reviewed_matrix_sha256=reviewed_sha,unresolved_high=0,
 reviewed_concepts=310,rechecked_highs=51,preserved_first_pass=259,
 first_pass_accepted_without_medium=245,first_pass_nonblocking_medium=14,
 states=dict(collections.Counter(d['state']for d in decisions.values())),reports=reports,
 metadata_corrections=dict(path=str(metadata_path.relative_to(ROOT)),sha256=metadata_sha,affected_concepts=12),
 mechanism_fingerprints_preserved=310,source_content_changes=0,concepts=sorted(decisions.values(),key=lambda r:r['concept_id']),
 scope='Import of actual first-pass and warm-recheck judgments. It is not an author-issued independent verdict.')
(BASE/'independent-closure.json').write_text(json.dumps(closure,ensure_ascii=False,indent=2)+'\n')
(CUR/'sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
(CUR/'revision-licenses.json').write_text(json.dumps(licenses,ensure_ascii=False,indent=2)+'\n')
judgments=load(CUR/'author-adjudications.json');selections=load(CUR/'source-selections.json')
for key in ['thread-pool','database-decomposition']:
 judgment=judgments[key];judgment['prior_selection_fingerprint']=judgment['selection_fingerprint']
 judgment['selection_fingerprint']=selection_fingerprint(key,selections[key],sources)
 judgment['license_metadata_correction']=dict(path=str(metadata_path.relative_to(ROOT)),sha256=metadata_sha)
 judgment['metadata_checked_at_utc']=now
(CUR/'author-adjudications.json').write_text(json.dumps(judgments,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(closure_concepts=310,rechecked=51,unresolved_high=0,metadata_concepts=12,
 states=closure['states'],mechanism_fingerprints_preserved=310,source_content_changes=0,
 closure_sha256=digest((BASE/'independent-closure.json').read_bytes()))))
