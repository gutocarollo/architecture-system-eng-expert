"""Execute the historical retry function with explicit local integration doubles."""
import argparse
import ast
import builtins
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from subprocess import TimeoutExpired
from urllib.parse import quote

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
MANIFEST=json.loads((HERE/'manifest.json').read_text())
FUNCTION='task_run_60_days_rule_hs'
CONTRACTS={
    'transient_lock': {'before':dict(attempts=1,waits=[],outcome='RuntimeError'), 'after':dict(attempts=2,waits=[30],outcome='success')},
    'permanent_error': {'before':dict(attempts=1,waits=[],outcome='RuntimeError'), 'after':dict(attempts=1,waits=[],outcome='RuntimeError')},
    'lock_budget': {'before':dict(attempts=1,waits=[],outcome='RuntimeError'), 'after':dict(attempts=3,waits=[30,30],outcome='RuntimeError')},
    'process_timeout': {'before':dict(attempts=1,waits=[],outcome='TimeoutExpired'), 'after':dict(attempts=1,waits=[],outcome='TimeoutExpired')},
    'clean_success': {'before':dict(attempts=1,waits=[],outcome='success'), 'after':dict(attempts=1,waits=[],outcome='success')},
}


def measure(source, scenario):
    events={'transient_lock':['55P03','success'],'permanent_error':['23505','success'],
            'lock_budget':['55P03']*4,'process_timeout':['timeout'],'clean_success':['success']}[scenario].copy()
    calls=[];waits=[]

    def run_process(arguments, **options):
        if arguments!=['/synthetic/sixty_days_rule_hs/bin/sixty-days-rule','--mode','prod','--json']:
            raise ValueError('The candidate changed the source-bound process contract')
        if options['timeout']!=300 or 'learning.invalid' not in options['env']['PG_CONN_STRING']:
            raise ValueError('The candidate changed the synthetic connection or timeout contract')
        event=events.pop(0);calls.append(event)
        if event=='timeout': raise TimeoutExpired(arguments,300)
        return SimpleNamespace(returncode=0 if event=='success' else 1,
                               stderr='' if event=='success' else f'{event}: synthetic subprocess error',
                               stdout='{"fixture":"synthetic-success"}' if event=='success' else '')

    noop=lambda *args,**kwargs:None
    fake_connection=SimpleNamespace(login='learning_operator',password=None,host='learning.invalid',port=5432,schema='learning_only')
    modules={
        'json':json,
        'subprocess':SimpleNamespace(run=run_process,TimeoutExpired=TimeoutExpired),
        'time':SimpleNamespace(sleep=waits.append),
        'resource':SimpleNamespace(RUSAGE_CHILDREN=0,getrusage=lambda _:SimpleNamespace(ru_maxrss=2048)),
        'urllib.parse':SimpleNamespace(quote=quote),
    }

    def controlled_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name not in modules:
            raise ImportError('The isolated kernel does not allow this module: '+name)
        return modules[name]

    namespace={'__builtins__':{**vars(builtins),'__import__':controlled_import},
               'os':SimpleNamespace(path=SimpleNamespace(join=os.path.join,exists=lambda _:True),environ={}),
               'toolkit_path':'/synthetic',
               'get_postgres_hook':lambda:SimpleNamespace(get_connection=lambda _:fake_connection),
               'logger':SimpleNamespace(info=noop,warning=noop,error=noop)}
    tree=ast.parse(source)
    functions=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name==FUNCTION]
    if len(functions)!=1 or len(tree.body)!=1:
        raise ValueError('The candidate must contain only the selected function')
    exec(compile(tree,'<historical-airflow-kernel>','exec'),namespace)
    try:
        result=namespace[FUNCTION]()
        if result!={'fixture':'synthetic-success','peak_rss_mb':2.0}:
            raise ValueError('The synthetic success result changed')
        outcome='success'
    except RuntimeError:
        outcome='RuntimeError'
    except TimeoutExpired:
        outcome='TimeoutExpired'
    return dict(attempts=len(calls),waits=waits,outcome=outcome)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=Path)
    parser.add_argument('--out',default='tasks/FBI-4991-arquitetura-nextra/execution/airflow-learning/receipt.json')
    args=parser.parse_args(); observations={}
    for label in ['before','after']:
        path=HERE/(label+'.py');source=path.read_text()
        if hashlib.sha256(source.encode()).hexdigest()!=MANIFEST['snapshots'][label]['sha256']:
            raise ValueError('The historical snapshot changed: '+str(path))
        if label=='after' and args.candidate: source=args.candidate.read_text()
        for scenario,conditions in CONTRACTS.items():
            measured=measure(source,scenario)
            if measured!=conditions[label]:
                raise AssertionError(f'{scenario}: {label} violates retry contract: {measured!r}')
            observations.setdefault(scenario,{})[label]=measured
    report=dict(observed_at=datetime.now(timezone.utc).isoformat(),scope='HISTORICAL_KERNEL_WITH_SYNTHETIC_DOUBLES',
                real_subprocesses_executed=0,real_database_connections=0,real_sleep_seconds=0,
                source_manifest=MANIFEST,observations=observations,verdict='PASS')
    output=ROOT/args.out;output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print('transient_lock: before_attempts=1 failure=True after_attempts=2 success=True waits=[30]')
    print('permanent_error: before_attempts=1 after_attempts=1 failure_preserved=True')
    print('lock_budget: before_attempts=1 after_attempts=3 waits=[30, 30] failure_preserved=True')
    print('process_timeout: before_attempts=1 after_attempts=1 timeout_preserved=True')
    print('comparison=PASS real_subprocesses=0 real_database_connections=0 real_sleep_seconds=0')


if __name__=='__main__': main()
