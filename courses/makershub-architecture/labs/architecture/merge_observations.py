"""Merge authored executable properties into the explicit per-concept adjudication."""
import json
from pathlib import Path
from additional_observations import all_observations

ROOT=Path(__file__).resolve().parents[2]
path=ROOT/'labs/architecture/mapping_decisions.json'
decisions=json.loads(path.read_text())
rows=list(all_observations())
extra_names={name for row in rows for name in row['names']}
assert len(extra_names)==sum(len(row['names']) for row in rows),'multiple new observations own the same concept'
existing=[]
for decision in decisions['observations']:
    names=[name for name in decision['names'].split('|') if name not in extra_names]
    if names:existing.append({**decision,'names':'|'.join(names)})
for row in rows:
    existing.append({'case':row['case'],'probe':row['probe'],'names':'|'.join(row['names']),'basis':row['guarantee'],
                     'action':row['action'],'source_file':row['source_file'],'scope_limit':row['limit']})
for decision in existing:
    if decision['probe']=='provider-contract':
        if 'Anti-Corruption Layer' not in decision['names'].split('|'):decision['names']+='|Anti-Corruption Layer'
    if decision['probe']=='value-object':
        if 'Immutable Data' not in decision['names'].split('|'):decision['names']+='|Immutable Data'
decisions['observations']=existing
path.write_text(json.dumps(decisions,ensure_ascii=False,indent=2)+'\n')
(ROOT/'tasks/FBI-4991-arquitetura-nextra/execution/learning/additional-observations.json').write_text(json.dumps({'observations':rows},ensure_ascii=False,indent=2)+'\n')
print(f'additional_properties={len(rows)} specifically_named_concepts={len(extra_names)}')
