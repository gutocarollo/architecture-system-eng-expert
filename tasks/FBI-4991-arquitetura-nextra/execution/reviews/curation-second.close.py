"""Verify this review's bounded captures, references and coverage without editing author content."""
import datetime,hashlib,json,pathlib,re,collections,html
ROOT=pathlib.Path(__file__).resolve().parents[4]
BASE=ROOT/'tasks/FBI-4991-arquitetura-nextra/execution'
matrix_path=BASE/'curation/matrix.json';matrix=json.loads(matrix_path.read_text());rows={r['concept_id']:r for r in matrix['concepts']}
review_path=BASE/'reviews/curation-second.concepts.json';review=json.loads(review_path.read_text());assigned=json.loads((BASE/'reviews/curation-assignment-two.json').read_text())['concept_ids']
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
checks=[];captures={};missing_capture=[];reference_errors=[];references=[]
sections={}
for p in (ROOT/'content/referencia/curadoria').glob('*.mdx'):
 for section in re.split(r'\n(?=## )',p.read_text()):
  match=re.search(r'O identificador canônico é `([^`]+)`',section)
  if match and match.group(1) in assigned:sections[match.group(1)]=(p,section)
for item in review['concepts']:
 cid=item['concept_id'];row=rows[cid]
 for role,ss in [('base',row['base']),('application',row['application']),('skill',[row['skill']]),('decision',row.get('decision_evidence',[]))]:
  for source in ss:
   artifact=source.get('artifact')
   if not artifact:
    if role in ['base','application']:missing_capture.append({'concept_id':cid,'role':role,'url':source['url']})
    continue
   actual=hashlib.sha256((ROOT/artifact).read_bytes()).hexdigest();captures[artifact]={'sha256':actual,'expected_sha256':source['sha256'],'valid':actual==source['sha256']}
   if role=='decision' or not any(e.get('artifact')==artifact for e in item['evidence']):
    item['evidence'].append({'role':role,'repo':source.get('repo'),'path':source.get('path'),'url':source['url'],'artifact':artifact,'sha256':actual,'hash_valid':actual==source['sha256'],'inspected_ranges':source.get('evidence',[]) if role=='decision' else [],'scope':'supplemental source capture checked'})
 page,section=sections.get(cid,(None,''));err=[]
 if page is None:err.append('missing concept section')
 else:
  for key in ['mechanism','limits']:
   if row[key] not in html.unescape(section):err.append(key+' diverges from matrix')
  for role in ['base','application']:
   for source in row[role]:
    if source['url'] not in section:err.append(role+' URL absent: '+source['url'])
  if row['skill']['url'] not in section:err.append('skill URL absent')
  for key in ['journey','concept']:
   if row['learning']['destinations'][key] not in section:err.append('learning destination absent: '+key)
  if 'revisão independente' not in section.lower():err.append('independent gate warning absent')
  references.append({'concept_id':cid,'path':str(page.relative_to(ROOT)),'sha256':hashlib.sha256(page.read_bytes()).hexdigest(),'exact_mechanism':row['mechanism'] in html.unescape(section),'exact_limits':row['limits'] in html.unescape(section),'errors':err})
 if err:reference_errors.append({'concept_id':cid,'errors':err})
 item['reference_check']={'observed_utc':now,'path':str(page.relative_to(ROOT)) if page else None,'errors':err}
assert len(review['concepts'])==len(assigned)==len(set(assigned))==127
assert set(assigned)=={x['concept_id'] for x in review['concepts']}
assert all(x['state'] in ['APPROVED','REPAIR_HIGH','MEDIUM_BACKLOG'] for x in review['concepts'])
review['summary']=dict(collections.Counter(x['state'] for x in review['concepts']));review['observed_utc']=now;review['coverage_complete']=True
review['integrity_receipt']='tasks/FBI-4991-arquitetura-nextra/execution/reviews/curation-second.integrity.json'
review['reference_receipt']='tasks/FBI-4991-arquitetura-nextra/execution/reviews/curation-second.references.json'
review_path.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
receipt={'observed_utc':now,'workspace':str(ROOT),'matrix_sha256':hashlib.sha256(matrix_path.read_bytes()).hexdigest(),'expected_matrix_sha256':'a4b12f6c6aa8b1883d8f6c1ac7ed1c7f81d829859422f5a0212f7fd1cca6689e','assigned':127,'finished_judgments':127,'unreviewed':0,'covered_by_lane1':sum(bool(x.get('covered_by_lane1')) for x in review['concepts']),'source_captures_checked':len(captures),'source_hash_errors':[p for p,v in captures.items() if not v['valid']],'missing_implementation_captures':missing_capture,'captures':captures,'global_integrity_reused':'tasks/FBI-4991-arquitetura-nextra/execution/reviews/curation-independent.integrity.json','global_reference_reconciliation_reused':'tasks/FBI-4991-arquitetura-nextra/execution/reviews/curation-independent.reference-reconciliation.json','scope':'Own assigned source captures only. Metadata, licenses and global locator/gzip gates reused. No production/runtime approval.'}
(BASE/'reviews/curation-second.integrity.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
(BASE/'reviews/curation-second.references.json').write_text(json.dumps({'observed_utc':now,'assigned_sections':len(references),'errors':reference_errors,'receipts':references},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'observed_utc':now,'summary':review['summary'],'source_captures_checked':len(captures),'source_hash_errors':receipt['source_hash_errors'],'reference_sections':len(references),'reference_errors':reference_errors,'missing_capture':missing_capture},ensure_ascii=False))
