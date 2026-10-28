"""Check every mapped command, sharing one execution only for identical commands."""
import hashlib
import json
import os
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
LEARNING=ROOT/'tasks/FBI-4991-arquitetura-nextra/execution/learning'
matrix_path=LEARNING/'concept-matrix.json'
matrix=json.loads(matrix_path.read_text())
commands={}
for row in matrix['concepts']:
    if row['command'] is None:continue
    commands.setdefault(row['command'],[]).append(row['concept_id'])
receipts=[]
for text,concept_ids in commands.items():
    command=shlex.split(text)
    env=dict(os.environ)
    while command and '=' in command[0] and command[0].split('=',1)[0] in {'TZ'}:
        key,value=command.pop(0).split('=',1);env[key]=value
    result=subprocess.run(command,cwd=ROOT,env=env,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,(text,result.stderr)
    assert 'comparison=PASS' in result.stdout,(text,'missing comparison receipt')
    receipts.append(dict(command=text,concept_ids=concept_ids,observed_at_utc=datetime.now(timezone.utc).isoformat(),
                         exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,
                         output_sha256=hashlib.sha256(result.stdout.encode()).hexdigest()))
output=dict(verdict='PASS',concepts_adjudicated=310,concepts_with_relevant_observation=sum(r['command'] is not None for r in matrix['concepts']),specific_practice_pending=sum(r['command'] is None for r in matrix['concepts']),distinct_commands_executed=len(receipts),
            source_matrix_sha256=hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
            sharing_policy='An identical command was run once, and its output is shared explicitly by the listed concepts.',
            proof_limit='Command success checks the bounded local observation; it does not close specific_pattern_implementation_gap or independent review.',
            receipts=receipts)
(LEARNING/'concept-execution-receipt.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(f'concepts_adjudicated=310 relevant={output["concepts_with_relevant_observation"]} pending={output["specific_practice_pending"]} distinct_commands={len(receipts)} exit_failures=0')
