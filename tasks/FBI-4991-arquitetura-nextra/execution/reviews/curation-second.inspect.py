"""Produce disjoint bounded review packets and persist explicit reviewer judgments."""
import argparse,datetime,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[4]
BASE=ROOT/'tasks/FBI-4991-arquitetura-nextra/execution'
MATRIX=BASE/'curation/matrix.json'
OUT=BASE/'reviews/curation-second.concepts.json'
assignment=json.loads((BASE/'reviews/curation-assignment-two.json').read_text())['concept_ids']
matrix=json.loads(MATRIX.read_text()); rows={r['concept_id']:r for r in matrix['concepts']}
parser=argparse.ArgumentParser();parser.add_argument('offset',type=int,nargs='?',default=0);parser.add_argument('--count',type=int,default=5);parser.add_argument('--record');args=parser.parse_args()
if OUT.exists(): result=json.loads(OUT.read_text())
else: result={'schema_version':1,'reviewer':'/root/curation_second','native_type':'default','contract':'read-only REVIEW; only review control writes','model':'gpt-6.1-sol','reasoning_effort':'xhigh','matrix_sha256':hashlib.sha256(MATRIX.read_bytes()).hexdigest(),'global_integrity_reused':'tasks/FBI-4991-arquitetura-nextra/execution/reviews/curation-independent.integrity.json','concepts':[{'concept_id':c,'state':'UNREVIEWED','evidence':[],'notes':''} for c in assignment]}
indexed={r['concept_id']:r for r in result['concepts']}
if args.record:
 for cid,item in json.loads(args.record).items():
  assert cid in assignment
  indexed[cid].update(item);indexed[cid]['reviewed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
other={r['concept_id']:r for r in json.loads((BASE/'reviews/curation-independent.concepts.json').read_text())['concepts']}
for cid in assignment[args.offset:args.offset+args.count]:
 if other[cid]['state']!='UNREVIEWED': indexed[cid].update(other[cid]);indexed[cid]['covered_by_lane1']=True;print('REUSED',cid,other[cid]['state']);continue
 r=rows[cid];print('\nCONCEPT',cid,'KIND',r['application_kind']);print('MECHANISM',r['mechanism']);print('LIMITS',r['limits']);print('CLASSIFICATION',r.get('classification_basis'))
 evidence=[]
 for role,maximum in [('base',2),('application',4)]:
  for s in r[role][:maximum]:
   if not s.get('artifact'):print('MISSING_ARTIFACT',s);continue
   p=ROOT/s['artifact'];data=p.read_bytes();ok=hashlib.sha256(data).hexdigest()==s['sha256'];print('SOURCE',role,s['repo'],s.get('path'), 'HASH',ok)
   lines=data.decode().splitlines();hit=next((v for v in r['source_evidence'] if v['source_url']==s['url'] and v['role']==role),None)
   shown=[]
   for h in (hit or {}).get('hits',[])[:1]:
    lo=max(1,h['start_line']-2);hi=min(len(lines),h['end_line']+3);shown.append([lo,hi])
    print('\n'.join(f'{i}: {lines[i-1]}' for i in range(lo,hi+1)))
   evidence.append({'role':role,'repo':s['repo'],'path':s.get('path'),'revision':s['revision'],'url':s['url'],'artifact':s['artifact'],'sha256':s['sha256'],'hash_valid':ok,'inspected_ranges':shown})
 s=r['skill'];p=ROOT/s['artifact'];evidence.append({'role':'skill','repo':s['repo'],'path':s['path'],'artifact':s['artifact'],'sha256':s['sha256'],'hash_valid':hashlib.sha256(p.read_bytes()).hexdigest()==s['sha256'],'scope':s.get('scope')})
 if not indexed[cid]['evidence']:indexed[cid]['evidence']=evidence
result['observed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();result['summary']={s:sum(x['state']==s for x in result['concepts']) for s in ['APPROVED','REPAIR_HIGH','MEDIUM_BACKLOG','UNREVIEWED']};OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
