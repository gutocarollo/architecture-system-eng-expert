"""Close only this reviewer's 31 HIGH repairs and immutable first-pass carry receipts."""
import collections,copy,datetime,hashlib,html,json,pathlib,re,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[4];B=ROOT/'tasks/FBI-4991-arquitetura-nextra/execution';C=B/'curation';sys.path.insert(0,str(C))
from adjudication_gate import adjudication_issues
from semantic_fingerprints import semantic_fingerprint
load=lambda p:json.loads(p.read_text());digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
oldp=B/'reviews/curation-second.concepts.json';old=load(oldp);out=B/'reviews/curation-second.recheck.json';review=load(out);matrix=load(C/'matrix.json');rows={r['concept_id']:r for r in matrix['concepts']};baseline={r['concept_id']:r for r in load(C/'review-baseline.json')['concepts']};ids={r['concept_id']for r in old['concepts']if r['state']=='REPAIR_HIGH'}
assert len(ids)==31 and ids=={r['concept_id']for r in review['concepts']};assert digest(C/'matrix.json')=='fa8e01dcc2bd0126ac085eed97452dff6d193448f588c9a078201fab259ddde0';assert digest(oldp)=='1b767d48cfa0d4e6b0e664480fbd596ae0c4e07045a3b6c0608b1ae3579ac074'
selections=load(C/'source-selections.json');sources=load(C/'sources.json');judgments=load(C/'author-adjudications.json');now=datetime.datetime.now(datetime.timezone.utc).isoformat();sections={};refs=[];errors=[];captures={};licenses={};guard=[]
for page in (ROOT/'content/referencia/curadoria').glob('*.mdx'):
 for section in re.split(r'\n(?=## )',page.read_text()):
  match=re.search(r'O identificador canônico é `([^`]+)`',section)
  if match and match.group(1) in ids:sections[match.group(1)]=(page,section)
for item in review['concepts']:
 cid=item['concept_id'];row=rows[cid];assert item['state'] in ['APPROVED_BOUNDED','RESIDUAL_HIGH']
 current_issues=adjudication_issues(cid,selections[cid],sources,judgments[cid],ROOT);assert not current_issues;(guard.append({'concept_id':cid,'issues':current_issues}))
 for source in item['evidence']:
  p=ROOT/source['artifact'];actual=digest(p);assert actual==source['sha256'];captures[source['artifact']]={'sha256':actual,'valid':True}
  l=source['license'];lp=ROOT/l['artifact'];assert digest(lp)==l['sha256'];licenses[l['artifact']]={'sha256':l['sha256'],'url':l['url'],'spdx':l['spdx'],'valid':True}
 page,text=sections[cid];decoded=html.unescape(text);err=[]
 for key in ['mechanism','limits']:
  if row[key] not in decoded:err.append(key+' text differs')
 for role in ['base','application']:
  for source in row[role]:
   if source['url'] not in text:err.append(role+' URL missing: '+source['url'])
 if err:errors.append({'concept_id':cid,'errors':err})
 refs.append({'concept_id':cid,'path':str(page.relative_to(ROOT)),'sha256':digest(page),'errors':err});item['reference_check']={'path':str(page.relative_to(ROOT)),'sha256':digest(page),'exact_mechanism_and_limits':not err}
 item['semantic_fingerprint']=semantic_fingerprint(row);item['author_selection_fingerprint']=judgments[cid]['selection_fingerprint']
carry=[]
for item in old['concepts']:
 if item['state']=='REPAIR_HIGH':continue
 cid=item['concept_id'];same=semantic_fingerprint(rows[cid])==baseline[cid]['semantic_fingerprint'];assert same;carry.append({'concept_id':cid,'state':item['state'],'semantic_fingerprint_unchanged':True})
assert len(carry)==96
key='domain-policy';sel=selections[key];j=judgments[key];mutations=[]
for name,changed in [('missing-positive',{}),('pending-decision',dict(j,decision='PENDING')),('unresolved-author-gate',dict(j,remaining_gates=['unresolved']))]:
 issue=adjudication_issues(key,sel,sources,changed,ROOT);assert issue;mutations.append({'case':name,'rejected':True,'issue_kinds':list({i['kind']for i in issue})})
assert not errors
observation={'id':'M1','severity':'MEDIUM_BACKLOG','concept_id':'database-decomposition','scope':'license metadata only; mechanism APPROVED_BOUNDED','source_path':'doc/development/database/multiple_databases.md','observed_label':'MIT','primary_license_declaration':'All content residing under the "doc/" directory of this repository is licensed under "Creative Commons: CC BY-SA 4.0 license".','expected_label':'CC-BY-SA-4.0','evidence_artifact':'tasks/FBI-4991-arquitetura-nextra/execution/curation/raw/license-a90b276ac6fcc001d0d5a914e1ced947fd2a2c877b94eb303b109c9cfac3ac83.txt','line':5,'fix':'Apply the path-specific doc/ license classification in the source record and MDX; keep MIT for the GitLab application code sources. No semantic source-review round is required for this deterministic metadata correction.'}
# Bind the observation to the actual license artifact, without assuming its cache filename.
entry=next(e for i in review['concepts']if i['concept_id']=='database-decomposition'for e in i['evidence']if e['path'].startswith('doc/'));observation['evidence_artifact']=entry['license']['artifact'];observation['evidence_sha256']=entry['license']['sha256'];observation['url']=entry['license']['url']
review.update({'observed_utc':now,'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),'summary':dict(collections.Counter(x['state']for x in review['concepts'])),'residual_high':[],'nonblocking_metadata_observations':[observation],'own_non_high_fingerprints_preserved':96,'positive_guard_checks':31,'positive_guard_mutations':mutations,'reference_errors':errors,'integrity_receipt':'tasks/FBI-4991-arquitetura-nextra/execution/reviews/curation-second.recheck.integrity.json','scope_note':'Warm recheck of original 31 HIGHs only. Prior 92 accepted and 4 medium remain unchanged. Approval is bounded semantic source proof, not runtime/deployment or universal license compatibility approval.'})
out.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
receipt={'observed_utc':now,'workspace':str(ROOT),'head':review['head'],'branch':review['branch'],'matrix_sha256':digest(C/'matrix.json'),'baseline_review_sha256':digest(oldp),'recheck_sha256':digest(out),'source_captures':len(captures),'source_hash_errors':[],'license_captures':len(licenses),'license_hash_errors':[],'license_scope_observations':[observation],'positive_guard':guard,'positive_guard_negative_probes':mutations,'reference_sections':len(refs),'reference_errors':errors,'own_non_high_preserved':len(carry),'carry':carry,'references':refs,'source_artifacts':captures,'license_artifacts':licenses,'control_files':{p.name:digest(p)for p in [C/'freeze-receipt.json',C/'repair-selections.json',C/'author-adjudications.json',C/'review-baseline.json',C/'adjudication_gate.py',C/'semantic_fingerprints.py',B/'curation-repairs/consolidated-recommendations.json']}}
(B/'reviews/curation-second.recheck.integrity.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'observed_utc':now,'head':review['head'],'matrix_sha256':receipt['matrix_sha256'],'summary':review['summary'],'source_captures':len(captures),'source_hash_errors':[],'license_captures':len(licenses),'license_hash_errors':[],'license_scope_observations':1,'positive_guard_checks':len(guard),'negative_probes_rejected':len(mutations),'reference_sections':len(refs),'reference_errors':errors,'own_non_high_preserved':len(carry),'recheck_sha256':receipt['recheck_sha256']},ensure_ascii=False))
