"""Read only repaired HIGH source spans; store reviewer-owned inspection receipts."""
import argparse,datetime,hashlib,json,pathlib,re,sys
ROOT=pathlib.Path(__file__).resolve().parents[4];B=ROOT/'tasks/FBI-4991-arquitetura-nextra/execution';C=B/'curation';sys.path.insert(0,str(C))
from adjudication_gate import adjudication_issues
old=json.loads((B/'reviews/curation-second.concepts.json').read_text());ids=[x['concept_id'] for x in old['concepts'] if x['state']=='REPAIR_HIGH'];assert len(ids)==31
matrix=json.loads((C/'matrix.json').read_text());rows={r['concept_id']:r for r in matrix['concepts']};adj=json.loads((C/'author-adjudications.json').read_text());sources=json.loads((C/'sources.json').read_text());sel=json.loads((C/'source-selections.json').read_text());licenses=json.loads((C/'revision-licenses.json').read_text())
p=argparse.ArgumentParser();p.add_argument('offset',type=int);p.add_argument('--count',type=int,default=5);p.add_argument('--record');p.add_argument('--lines',type=int,default=14);args=p.parse_args();out=B/'reviews/curation-second.recheck.json'
if out.exists(): result=json.loads(out.read_text())
else:result={'schema_version':1,'reviewer':'/root/curation_second','native_type':'default','model':'gpt-6.1-sol','reasoning_effort':'xhigh','route':'WARM_REUSE REVIEW, HIGH-only','matrix_sha256':hashlib.sha256((C/'matrix.json').read_bytes()).hexdigest(),'baseline_review_sha256':hashlib.sha256((B/'reviews/curation-second.concepts.json').read_bytes()).hexdigest(),'preserved_first_pass':{'APPROVED':92,'MEDIUM_BACKLOG':4},'concepts':[{'concept_id':c,'state':'UNREVIEWED','evidence':[],'notes':''}for c in ids]}
index={r['concept_id']:r for r in result['concepts']}
if args.record:
 for cid,updates in json.loads(args.record).items():
  assert cid in ids;index[cid].update(updates);index[cid]['reviewed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
seen=set()
for cid in ids[args.offset:args.offset+args.count]:
 r=rows[cid];j=adj[cid];print('\nCONCEPT',cid);print('MECHANISM',r['mechanism']);print('LIMITS',r['limits']);print('PAIRING',r.get('pairing_relationship'))
 issues=adjudication_issues(cid,sel[cid],sources,j,ROOT);print('POSITIVE_GUARD',issues);index[cid]['positive_guard_errors']=issues;evout=[]
 for role in ['base','application']:
  for source in r[role]:
   artifact=ROOT/source['artifact'];ls=artifact.read_text().splitlines();sha=hashlib.sha256(artifact.read_bytes()).hexdigest();key=source['repo']+'@'+source['revision'];lic=licenses.get(key);assert lic is not None,(cid,key)
   lp=ROOT/lic['artifact'];lh=hashlib.sha256(lp.read_bytes()).hexdigest();license_ok=lic['status']=='READ' and lic['revision']==source['revision'] and lh==lic['sha256'];assert sha==source['sha256'] and license_ok,(cid,source['path'])
   spans=[e for e in j['primary_evidence']if e['role']==role and e['source_url'].split('#')[0]==source['url'].split('#')[0]]
   print('SOURCE',role,source['repo'],source['path'],'LICENSE',lic['license_spdx'],'HASH_VALID',sha==source['sha256']);print('SPANS',[(e['start_line'],e['end_line'],e['claim'])for e in spans])
   inspected=[]
   for e in spans[:2]:
    lo,hi=e['start_line'],e['end_line'];ranges=[[lo,min(hi,lo+args.lines-1)]]
    if hi-lo+1>args.lines:ranges.append([max(lo+args.lines,hi-args.lines+1),hi])
    for a,z in ranges:
     if (source['artifact'],a,z) in seen:print('REUSED_READ',a,z);continue
     seen.add((source['artifact'],a,z));inspected.append([a,z]);print('\n'.join(f'{i}: {ls[i-1]}'for i in range(a,z+1)))
   evout.append({'role':role,'repo':source['repo'],'path':source['path'],'revision':source['revision'],'url':source['url'],'artifact':source['artifact'],'sha256':sha,'hash_valid':True,'inspected_ranges':inspected,'adjudicated_spans':spans,'license':{'spdx':lic['license_spdx'],'url':lic['url'],'revision':lic['revision'],'artifact':lic['artifact'],'sha256':lh,'valid':license_ok}})
 index[cid]['evidence']=evout
result['observed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();result['summary']={s:sum(x['state']==s for x in result['concepts'])for s in ['APPROVED_BOUNDED','RESIDUAL_HIGH','UNREVIEWED']};out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
