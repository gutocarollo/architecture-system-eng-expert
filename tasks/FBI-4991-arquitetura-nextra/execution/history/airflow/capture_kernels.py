#!/usr/bin/env python3
"""Read selected immutable Airflow objects and disk markers over SSH; never import DAGs."""
import json
import pathlib
import subprocess

REMOTE_SCRIPT = r'''
import ast, datetime, hashlib, json, pathlib, subprocess
root = pathlib.Path('/home/fazcapital/airflow/airflow-dags')
specs = [
 ('retry', '55dfe8acb362e6854d1af4e7dd7d17e6497af9bd', [
  ('dags/inflow__xp__stg_to_fct.py', ['@task_run_60_days_rule_hs'])]),
 ('capacity', '751009ba9c744e8e6d2be71b100251a59fa339e4', [
  ('config/airflow.cfg', ['parallelism =', 'max_active_tasks_per_dag =']),
  ('config/dw_capacity.json', ['role_connection_limit', 'max_connections_per_task', 'connection_headroom', 'max_parallel_tasks', '"status"'])]),
 ('identity', 'bff72e872644bc256f6a704b49309a263a6ddf93', [
  ('toolkit/lemitvox_dialer/dedupe.py', ['@drop_identical_rows', '@call_key', '@drop_repeated_calls', '@stored_call_keys', '@drop_stored_calls'])]),
 ('publication', 'f53d1e8d1e689d90380e7a9a29ab8a0d24a55082', [
  ('toolkit/lead_dashboard/publication.py', ['@object_path', '@publish_html', '@fetch_html']),
  ('dags/reports__lead_conversion__build__hourly.py', ['output_dir =', 'html_file =', 'published_path ='])]),
 ('run_gate', 'ce08e7025606280ac926442b4d89fe88283ae88d', [
  ('dags/captable__xp__stg_to_fct.py', ['@forex_freshness_gate', "WHERE procedure_name", "AND run_at >="])])
]
def git(*args):
 return subprocess.run(['git','-C',str(root),*args],capture_output=True,check=True).stdout
def excerpts(source, selectors):
 lines = source.splitlines()
 nodes = list(ast.walk(ast.parse(source))) if any(s.startswith('@') for s in selectors) else []
 ranges = set()
 for selector in selectors:
  if selector.startswith('@'):
   for node in nodes:
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name == selector[1:]:
     # Preserve exact function text with original line locators; do not execute it.
     start,end=node.lineno,node.end_lineno
     ranges.add((start,end))
  else:
   for i,line in enumerate(lines):
    if selector in line and not line.lstrip().startswith('#') and (selector not in ['parallelism =', 'max_active_tasks_per_dag ='] or line.strip().startswith(selector)):
     span=12 if selector in ['html_file =','published_path ='] else 3
     ranges.add((max(1,i+1-1),min(len(lines),i+1+span)))
 return [{'start_line':a,'end_line':b,'text':'\n'.join(lines[a-1:b])} for a,b in sorted(ranges)]
out=[]
for case,sha,files in specs:
 parent=git('rev-parse',sha+'^').decode().strip()
 item={'case_id':case,'sha':sha,'parent':parent,'committer_date':git('show','-s','--format=%cI',sha).decode().strip(),'files':[]}
 for path,selectors in files:
  f={'path':path}
  for label,revision in [('before',parent),('after',sha)]:
   read=subprocess.run(['git','-C',str(root),'show',revision+':'+path],capture_output=True)
   if read.returncode:
    f[label]={'available':False,'reason':'path_absent_in_revision'}
   else:
    source=read.stdout.decode()
    f[label]={'available':True,'blob':git('rev-parse',revision+':'+path).decode().strip(),'sha256':hashlib.sha256(read.stdout).hexdigest(),'excerpts':excerpts(source,selectors)}
  patch=git('diff','--no-ext-diff',parent,sha,'--',path)
  f['diff_sha256']=hashlib.sha256(patch).hexdigest()
  item['files'].append(f)
 out.append(item)
disk=[]
for path,selectors in [
 ('dags/inflow__xp__stg_to_fct.py',['lock_retries,','AND run_at >=']),
 ('config/airflow.cfg',['parallelism =','max_active_tasks_per_dag =']),
 ('config/dw_capacity.json',['role_connection_limit','"status"']),
 ('toolkit/lemitvox_dialer/dedupe.py',['@call_key']),
 ('toolkit/lead_dashboard/publication.py',['@publish_html']),
 ('dags/reports__lead_conversion__build__hourly.py',['output_dir =','published_path ='])]:
 p=root/path
 item={'path':path,'exists':p.is_file()}
 if p.is_file():
  data=p.read_bytes()
  item.update(mtime_utc=datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(data).hexdigest(),excerpts=excerpts(data.decode(),selectors))
 disk.append(item)
print(json.dumps({'measured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':'airflow-70','source_path':str(root),'historical_cases':out,'disk_receipts':disk,'scope':'Historical immutable objects and selected disk text only; no scheduler, cluster, database, DAG run or current-production verification.'},ensure_ascii=False))
'''

if __name__ == '__main__':
    result = subprocess.run(
        ['ssh', '-o', 'ConnectTimeout=10', 'airflow-70', 'python3 - #stale-ok'],
        input=REMOTE_SCRIPT, capture_output=True, text=True, check=True,
    )
    payload = json.loads(result.stdout)
    output_path = pathlib.Path(__file__).with_name('source-kernels.json')
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'output': str(output_path), 'cases': len(payload['historical_cases']), 'measured_at': payload['measured_at']}))
