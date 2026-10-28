"""Extract immutable source bytes; never execute the original system adapters."""
import hashlib
import json
import subprocess
from pathlib import Path

SOURCE_ROOT = Path('/Users/augustocarollo/Developer/makershub')
LAB_ROOT = Path(__file__).resolve().parent
SPECS = {
    'single-flight-cancel': ('a304a4e5', [('backend/app/utils/single_flight.py', '')]),
    'early-refresh': ('a8bb7023', [('backend/app/utils/single_flight.py', '')]),
    'date-only': ('7101d3a4', [('frontend/app/_utils/isoDate.ts', ''),
        ('frontend/app/(pages)/insurance/InsuranceProposalsAnalysisCard.tsx', '-card')]),
    'opportunity-entry': ('8206752f', [('backend/app/services/super_r1_service.py', ''),
        ('backend/app/integrations/salesforce_integration.py', '-integration'),
        ('backend/app/services/qualify_service.py', '-qualify')]),
}

def git(*args):
    return subprocess.check_output(['git', '-C', str(SOURCE_ROOT), *args])

for case_id, (abbreviated, sources) in SPECS.items():
    destination = LAB_ROOT / case_id
    destination.mkdir(parents=True, exist_ok=True)
    corrected = git('rev-parse', abbreviated).decode().strip()
    previous = git('rev-parse', abbreviated + '^').decode().strip()
    snapshots = []
    for source_path, local_suffix in sources:
        for phase, sha in [('before', previous), ('after', corrected)]:
            raw = git('show', f'{sha}:{source_path}')
            local = destination / f'{phase}{local_suffix}{Path(source_path).suffix}'
            local.write_bytes(raw)
            snapshots.append(dict(phase=phase, sha=sha, source_path=source_path,
                                  local_path=str(local.relative_to(LAB_ROOT.parent.parent)),
                                  sha256=hashlib.sha256(raw).hexdigest()))
    diff_paths=[p for p,_ in sources] if case_id=='opportunity-entry' else [sources[0][0]]
    diff = git('diff', previous, corrected, '--', *diff_paths)
    (destination / 'source.diff').write_bytes(diff)
    manifest = dict(case_id=case_id, source_repository=str(SOURCE_ROOT), before_sha=previous,
                    after_sha=corrected, snapshots=snapshots,
                    diff_sha256=hashlib.sha256(diff).hexdigest(), inputs='SYNTHETIC',
                    historical_lineage_gate='PENDING_JIRA_PR', runtime_scope='LOCAL_LEARNING_ONLY')
    history_root=LAB_ROOT.parent.parent/'tasks/FBI-4991-arquitetura-nextra/execution/history'
    history_file=history_root/'cases-source.json'
    if history_file.is_file():
        cases=json.loads(history_file.read_text())['cases']
        matched=next((c for c in cases if c['sha']==corrected and c['parent_sha']==previous),None)
        if matched and all((history_root/name).is_file() for name in ['cases-remote.json','cases-visible-jira.json']):
            manifest['historical_lineage_gate']='SOURCE_PR_JIRA_PRESENT_MATCHED_TO_LOCAL_SNAPSHOTS'
            manifest['historical_source_receipt']=str(history_file.relative_to(LAB_ROOT.parent.parent))
            manifest['historical_pr_receipt']=str((history_root/'cases-remote.json').relative_to(LAB_ROOT.parent.parent))
            manifest['historical_jira_receipt']=str((history_root/'cases-visible-jira.json').relative_to(LAB_ROOT.parent.parent))
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('extracted=4 source_repository=read-only snapshots=14')
