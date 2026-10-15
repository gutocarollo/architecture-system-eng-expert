"""Assemble the current evidence packet without inventing review approvals."""
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = Path(__file__).resolve().parent
old = json.loads((ROOT / 'tasks/architecture-course-2026-10-14/prepared-council/packet.json').read_text())
now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
source_roots = {'project': ROOT, 'makershub': Path('/Users/augustocarollo/Developer/makershub'),
                'workflow-evidence': ROOT / 'tasks/architecture-course-2026-10-14/evidence'}
packet = dict(packet_version=2, project_root=str(ROOT), created_at=now, status='PARTIAL',
              scope=json.loads((BASE/'profile.json').read_text())['context']['bounded_anchor'],
              inventory=old['inventory'], sources=old['sources'], evidence=old['evidence'],
              coverage=old['coverage'], relations=old['relations'], documents=[], adrs=[], diagrams=[], reviews=[], gaps=[])
for source in packet['sources']:
    if source['id']=='project':
        source['revision']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() + '+working-tree-hashes'
        source['observed_at']=now
        source['reason']='The documents and evidence below bind the working-tree bytes; the base SHA is not a claim that changes are committed.'
for item in packet['evidence']:
    path=Path(item['path'])
    if path.is_absolute() and item['source_id']=='project':
        item['path']=str(path.relative_to(old['project_root']))
    actual=source_roots[item['source_id']] / item['path']
    if hashlib.sha256(actual.read_bytes()).hexdigest()!=item['sha256']:
        raise SystemExit('Changed inherited evidence needs adjudication: '+str(actual))


def add_evidence(identifier, relative, kind):
    path=ROOT/relative
    lines=path.read_text().splitlines(keepends=True)
    packet['evidence'].append(dict(id=identifier,source_id='project',path=relative,
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),line_start=1,line_end=min(20,len(lines)),
        quote=''.join(lines[:20]),observed_at=now,kind=kind))

for identifier,relative,kind in [
    ('learning-contracts','labs/architecture/financial_contracts.json','contract'),
    ('learning-matrix','tasks/FBI-4991-arquitetura-nextra/execution/learning/concept-matrix.json','contract'),
    ('pg-source','labs/postgres-lineage/manifest.json','code'),
    ('airflow-source','labs/airflow-lock-retry/manifest.json','code'),
    ('airflow-runtime','tasks/FBI-4991-arquitetura-nextra/execution/airflow-learning/full-run.json','runtime'),
    ('airflow-challenge','tasks/FBI-4991-arquitetura-nextra/execution/airflow-learning/challenges.json','runtime'),
    ('pg-runtime','tasks/FBI-4991-arquitetura-nextra/execution/postgres-learning/full-run.json','runtime'),
    ('pg-challenges','tasks/FBI-4991-arquitetura-nextra/execution/postgres-learning/challenges.json','runtime'),
    ('nextra-layout','app/layout.jsx','code'),
    ('course-validation','tasks/architecture-course-2026-10-14/artifacts/fbi4991-execution-validation.json','runtime'),
    ('catalog-barrier','tasks/FBI-4991-arquitetura-nextra/execution/catalog/registration-proposal.json','scope'),
    ('history-adjudication','tasks/FBI-4991-arquitetura-nextra/execution/history/history-causal-completion-summary.json','contract'),
    ('current-data','tasks/FBI-4991-arquitetura-nextra/execution/live-data-0301.json','runtime')]:
    if (ROOT/relative).exists(): add_evidence(identifier,relative,kind)

old_documents={item['path']:item for item in old['documents']}
concepts=json.loads((BASE/'learning/concept-matrix.json').read_text())['concepts']
by_case={}
for concept in concepts: by_case.setdefault(concept['case_id'],[]).append(concept['concept_id'])
for path in sorted((ROOT/'content').rglob('*.mdx')):
    relative=str(path.relative_to(ROOT)); source=old_documents.get(relative)
    if source: item={**source,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    else:
        case_id=next((part for part in path.parts if part in by_case),None)
        ids=by_case.get(case_id,[])
        if path.name.endswith('.mdx') and '/curadoria/' in relative:
            group=int(path.stem[:2]) if path.stem[:2].isdigit() else None
            ids=[c['concept_id'] for c in concepts if group in c['groups']] if group else []
        author='/root/curation_complete' if relative.startswith('content/referencia/') else '/root/applied_learning_build'
        if 'airflow-lock-retry' in relative: author='/root';ids=['retry','timeout','pessimistic-locking']
        if 'query-grain-postgres' in relative: author='/root';ids=['materialized-view','indexing','precomputation','cqrs']
        if 'revision-cas-postgres' in relative: author='/root';ids=['optimistic-concurrency-control','compare-and-swap-cas']
        item=dict(id=relative.removeprefix('content/').removesuffix('.mdx'),path=relative,
                  sha256=hashlib.sha256(path.read_bytes()).hexdigest(),author_id=author,
                  inventory_ids=[value for value in ids if value in packet['inventory']],relation_ids=[])
    packet['documents'].append(item)

render_file=BASE/'mermaid-current.json'
if render_file.exists():
    rendered=json.loads(render_file.read_text())
    doc_by_path={str(ROOT/d['path']):d for d in packet['documents']}
    for index,block in enumerate(rendered['blocks'],1):
        doc=doc_by_path[block['path']]
        if doc['sha256']!=block['document_sha256']: raise SystemExit('Diagram document changed: '+doc['path'])
        packet['diagrams'].append(dict(id=f'diagram-{index}',document_id=doc['id'],fence_index=block['fence_index'],
            relation_ids=doc['relation_ids'],syntax=block['syntax'],render=block['render'],semantic_review='NOT_RUN'))

catalog=json.loads((BASE/'catalog/registration-proposal.json').read_text())
if catalog['asset_state']!='registered': packet['gaps'].append(dict(id='catalog-registration',kind='authorization',critical=True,source_id='project',description='The exact repository and asset remain outside the approved catalog contract; the concrete proposal is preserved without bypassing validation.'))
curation=json.loads((BASE/'curation/matrix.json').read_text())
if curation['summary']['pending_concepts']:
    packet['gaps'].append(dict(id='curation-gaps',kind='source',critical=True,source_id='project',description=f"{curation['summary']['pending_concepts']} concepts still have author-declared curatorship gaps."))
repair_status=BASE/'curation-repairs/independent-closure.json'
if repair_status.exists():
    closure=json.loads(repair_status.read_text())
    unresolved=closure.get('unresolved_high',51)
else:
    unresolved=51
if unresolved:
    packet['gaps'].append(dict(id='curation-independent-highs',kind='review',critical=True,source_id='project',description=f'{unresolved} material source-correspondence findings still need repaired sources and independent acceptance. Author source-match counts are not independent approval.'))
history_summary=BASE/'history/history-causal-completion-summary.json'
if history_summary.exists():
    history=json.loads(history_summary.read_text())
    if not history['all_causes_confirmed']:
        packet['gaps'].append(dict(id='history-causal-proof',kind='source',critical=True,source_id='project',description=f"Individual classification is complete for {history['fbi_issues']} FBI issues, with {history['classification_counts']['MISSING_CAUSE_EVIDENCE']} explicitly missing causal evidence and {history['reported_only_count']} reported-only classifications. Full causal confirmation is not established by patch indexing or source triage."))
packet['gaps'].append(dict(id='independent-final-review',kind='review',critical=True,source_id='project',description='The current packet and diagrams require actual independent receipts; earlier-cycle receipts were not transplanted.'))
packet['gaps'].append(dict(id='production-boundary',kind='scope',critical=False,source_id='project',description='Local experiments and read-only source inspection do not establish deployment or end-to-end production execution.'))
for receipt_path in sorted((BASE/'reviews/terminal-receipts').glob('*.json')):
    receipt=json.loads(receipt_path.read_text())
    doc=next(d for d in packet['documents'] if d['id']==receipt['document_id'])
    if receipt['document_sha256']!=doc['sha256']: raise SystemExit('Stale independent receipt: '+str(receipt_path))
    packet['reviews'].append(dict(reviewer_id=receipt['reviewer_id'],document_id=doc['id'],document_sha256=doc['sha256'],
        verdict=receipt['verdict'],open_high_findings=receipt['open_high_findings'],receipt_path=str(receipt_path.relative_to(ROOT)),receipt_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest()))
output=BASE/'prepared/packet.json'
output.write_text(json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status=packet['status'],documents=len(packet['documents']),evidence=len(packet['evidence']),diagrams=len(packet['diagrams']),reviews=len(packet['reviews']),gaps=packet['gaps']),ensure_ascii=False))
