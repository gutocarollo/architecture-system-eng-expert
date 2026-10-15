"""Run live observations and prove that bypasses and corrupt fields are rejected."""
import copy
import importlib.util
import json
import subprocess
import tempfile
import shutil
from datetime import datetime,timezone
from pathlib import Path
from invariants import validate,CONTRACTS,validate_object
from object_patterns import mechanisms
import financial

ROOT=Path(__file__).resolve().parents[2]
receipts=[]

def leaves(value,path=()):
    if isinstance(value,dict):
        for key,item in value.items():yield from leaves(item,path+(key,))
    elif isinstance(value,list):
        for index,item in enumerate(value):yield from leaves(item,path+(index,))
    else:yield path,value

def replace_at(value,path,replacement):
    if not path:return replacement
    cursor=value
    for key in path[:-1]:cursor=cursor[key]
    cursor[path[-1]]=replacement
    return value

def reject(probe,before,after):
    try:validate(probe,before,after)
    except AssertionError:return True
    return False

for case,fn in financial.CASES.items():
    for observed in fn():
        probe=observed['probe'];before=observed['before'];after=observed['after']
        validate(probe,before,after)
        bypass_rejected=reject(probe,before,copy.deepcopy(before))
        assert bypass_rejected,probe
        corruptions=[]
        for path,value in leaves(after):
            replacement=(not value) if isinstance(value,bool) else ((value+1) if isinstance(value,(float,int)) else ('MUTATED' if value!='MUTATED' else 'OTHER'))
            mutant=replace_at(copy.deepcopy(after),path,replacement)
            killed=reject(probe,before,mutant)
            assert killed,(probe,path)
            corruptions.append({'path':list(path),'original':value,'mutation':replacement,'rejected':killed})
        saved_record=financial.record
        def bypass_record(name,observed_before,observed_after,guarantee,limit):
            return saved_record(name,observed_before,copy.deepcopy(observed_before) if name==probe else observed_after,guarantee,limit)
        financial.record=bypass_record
        try:
            list(fn());execution_bypass_rejected=False
        except AssertionError as error:
            execution_bypass_rejected=str(error).startswith(probe+':')
        finally:
            financial.record=saved_record
        assert execution_bypass_rejected,probe
        receipts.append({'probe':probe,'case_id':case,'live_contract':'PASS','bypass_protected_result_rejected':bypass_rejected,'live_execution_without_protected_result_rejected':execution_bypass_rejected,'field_mutations':corruptions})

objects=[]
for concept,before,after,mechanism in mechanisms():
    validate_object(concept,before,after)
    try:validate_object(concept,before,copy.deepcopy(before));killed=False
    except AssertionError:killed=True
    assert killed,concept
    field_kills=0
    for path,value in leaves(after):
        replacement=(not value) if isinstance(value,bool) else ((value+1) if isinstance(value,(float,int)) else 'MUTATED')
        mutant=replace_at(copy.deepcopy(after),path,replacement)
        try:validate_object(concept,before,mutant);rejected=False
        except AssertionError:rejected=True
        assert rejected,(concept,path)
        field_kills+=1
    objects.append({'concept':concept,'live_contract':'PASS','bypass_rejected':killed,'field_mutations_killed':field_kills})

# Reproduce the reviewer's exact arithmetic corruption inside the executable function.
source=(ROOT/'labs/architecture/financial.py').read_text()
needle="{'debit':sum(inbox.values()),'effects':len(inbox)}"
replacement="{'debit':sum(value for _,value in messages),'effects':len(inbox)}"
assert needle in source
namespace={'__name__':'financial_mutant','__file__':str(ROOT/'labs/architecture/financial.py')}
exec(compile(source.replace(needle,replacement),'<in-memory removed deduplication>', 'exec'),namespace)
try:list(namespace['order_delivery']());arithmetic_rejected=False
except AssertionError:arithmetic_rejected=True
assert arithmetic_rejected
historical=[]
for case,source_name,needle,replacement in [
    ('single-flight-cancel','after.py','return await asyncio.shield(task)','return await task'),
    ('early-refresh','after.py','self._start_background_refresh(producer)','None'),
    ('opportunity-entry','after-integration.py','if source_opp_id:\n        try:','if False:\n        try:')]:
    with tempfile.TemporaryDirectory(prefix='historical-negative-control-') as directory:
        target=Path(directory)/case
        shutil.copytree(ROOT/'labs/architecture'/case,target,ignore=shutil.ignore_patterns('__pycache__'))
        changed=target/source_name
        original=changed.read_text()
        assert needle in original,(case,'missing mutation anchor')
        changed.write_text(original.replace(needle,replacement,1))
        result=subprocess.run(['python3',str(target/'run.py')],capture_output=True,text=True,timeout=20)
        killed=result.returncode!=0 and 'AssertionError' in result.stderr
        assert killed,(case,result.stdout,result.stderr)
        historical.append({'case_id':case,'source_file':source_name,'removed_guard':needle,'replacement':replacement,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr,'mutant_rejected_by_contract':killed})

output={'observed_at_utc':datetime.now(timezone.utc).isoformat(),'verdict':'PASS','probe_count':len(receipts),'field_mutations_killed':sum(len(r['field_mutations']) for r in receipts),'reviewer_debit_250_mutant_rejected':arithmetic_rejected,'receipts':receipts,'object_receipts':objects,'historical_source_mutations':historical,'date_source_mutation_receipt':'challenge-receipts.json','limit':'Each fixture output is checked in full. Field mutation and protected-result bypass are negative controls, not a complete mutation campaign over all source operators.'}
(ROOT/'tasks/FBI-4991-arquitetura-nextra/execution/learning/invariant-receipts.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(f'probes={len(receipts)} field_mutations_killed={output["field_mutations_killed"]} reviewer_arithmetic_mutant_rejected={arithmetic_rejected}')
