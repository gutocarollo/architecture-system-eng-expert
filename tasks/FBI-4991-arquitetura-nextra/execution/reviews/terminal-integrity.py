"""Reconcile frozen source, inherited review boundaries and delivery metadata."""
import contextlib
import hashlib
import io
import json
import re
import runpy
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

root = Path.cwd()
base = root / 'tasks/FBI-4991-arquitetura-nextra/execution'
out = base / 'reviews'
sha = lambda data: hashlib.sha256(data).hexdigest()
load = lambda path: json.loads(path.read_text())
report = {'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'scope': 'Current bytes and actual independent judgment lineage, not a renewed semantic approval of 310 concepts or all 94 diagrams.'}

def git(*args, cwd=root):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()

report['checkouts'] = [{ 'path': str(cwd), 'branch': git('branch', '--show-current', cwd=cwd), 'head': git('rev-parse', 'HEAD', cwd=cwd),
                         'tracked_changes': git('status', '--porcelain', '--untracked-files=no', cwd=cwd).splitlines() }
                        for cwd in [root, root / 'sites/architecture-course']]
assert report['checkouts'][0]['head'] == '623ae1d3d34143df53c571327a508de47ab58951'
assert report['checkouts'][1]['head'] == '1677c81236d3588736e88597e9589d942b655a25'
assert all(not item['tracked_changes'] for item in report['checkouts'])
report['scanner_applicability'] = {'codegraph_present': (root / '.codegraph').is_dir(), 'harness_scanner_present': (root / '.harness/lib/scan_project.py').exists(), 'request_anchor_present': (root / '.harness/requests/CURRENT-TASK.md').exists(), 'anchor_used': 'Inline terminal task and execution/profile.json bounded_anchor; standalone original request archive absent.'}

freeze = load(base / 'curation/freeze-receipt.json')
freeze_errors = []
for relative, binding in freeze['files'].items():
    path = base / 'curation' / relative
    if not path.is_file() or sha(path.read_bytes()) != binding['sha256']:
        freeze_errors.append(relative)
assert not freeze_errors, freeze_errors
closure = load(base / 'curation-repairs/independent-closure.json')
matrix = load(base / 'curation/matrix.json')
assert sha((base / 'curation/matrix.json').read_bytes()) == 'ee53aae70c2edf9256dc0b56660993b05283b0b1db028b6f738343764aa3313b'
assert len(closure['concepts']) == len(matrix['concepts']) == 310
assert len({r['concept_id'] for r in closure['concepts']}) == 310
assert closure['unresolved_high'] == 0
report['curation'] = {'freeze_files_checked': len(freeze['files']), 'freeze_errors': freeze_errors, 'matrix_sha256': closure['final_matrix_sha256'],
                      'reviewed_matrix_sha256': closure['reviewed_matrix_sha256'], 'concepts': 310, 'states': closure['states'],
                      'warm_rechecked_highs': closure['rechecked_highs'], 'mechanism_fingerprints_preserved': closure['mechanism_fingerprints_preserved'],
                      'metadata_corrections': closure['metadata_corrections'], 'unresolved_high': 0}

def run_redirected(script, original_output, terminal_output, arguments=()):
    original_write = Path.write_text
    def redirect(path, data, *args, **kwargs):
        assert path.resolve() == original_output.resolve(), str(path)
        return original_write(terminal_output, data, *args, **kwargs)
    saved_args = sys.argv[:]
    sys.path.insert(0, str(script.parent))
    captured = io.StringIO()
    try:
        sys.argv = [str(script), *arguments]
        with patch.object(Path, 'write_text', redirect), contextlib.redirect_stdout(captured):
            try:
                runpy.run_path(str(script), run_name='__main__')
            except SystemExit as stop:
                assert stop.code in (None, 0), stop.code
    finally:
        sys.argv = saved_args
        sys.path.pop(0)
    return {'script': str(script.relative_to(root)), 'source_sha256': sha(script.read_bytes()), 'arguments': list(arguments),
            'write_redirection_only': str(terminal_output.relative_to(root)), 'output': captured.getvalue()}

report['deterministic_gates'] = [
    run_redirected(base / 'curation/check_adjudication_gate.py', base / 'curation/adjudication-gate-receipt.json', out / 'terminal-curation-guard.json'),
    run_redirected(base / 'curation/verify_curation.py', base / 'curation/curation-validation.json', out / 'terminal-curation-validation.json', ['--require-complete', '--require-independent']),
    run_redirected(base / 'history/audit_public_history.py', base / 'history/public-export-manifest.json', out / 'terminal-history.json')
]
guard = load(out / 'terminal-curation-guard.json')
assert guard['checks'] == 375 and guard['failures'] == guard['independent_pending_count'] == 0
history = load(out / 'terminal-history.json')
assert history['semantic_commits'] == 12697 and history['classified_fbi_issues'] == 595
assert history['classification_counts'] == {'CAUSE_REPORTED_AND_CODE_SUPPORTED': 7, 'MISSING_CAUSE_EVIDENCE': 35, 'REPORTED_ONLY': 290, 'NOT_APPLICABLE_CHANGE': 263}

inherited = []
for relative, key, permitted in [('reviews/teaching-recheck.json', 'read_source_sha256', {'labs/architecture/run_all.py'}), ('reviews/root-cases.json', 'source_sha256', set())]:
    receipt = load(base / relative)
    changes = [name for name, expected in receipt[key].items() if not (root / name).exists() or sha((root / name).read_bytes()) != expected]
    assert set(changes) == permitted, (relative, changes)
    inherited.append({'receipt': relative, 'receipt_sha256': sha((base / relative).read_bytes()), 'bindings': len(receipt[key]), 'changed': changes,
                      'preserved_verdict': receipt['verdict'], 'scope': receipt['scope']})
old_runner = subprocess.check_output(['git', 'show', '32b80d5fc8eda42e2aa9b496d82c30b574120e68:labs/architecture/run_all.py'], cwd=root)
assert sha(old_runner) == load(base / 'reviews/teaching-recheck.json')['read_source_sha256']['labs/architecture/run_all.py']
report['inherited_reviews'] = inherited
report['runner_delta'] = {'before_sha256': sha(old_runner), 'current_sha256': sha((root / 'labs/architecture/run_all.py').read_bytes()),
                          'diff': git('diff', '32b80d5fc8eda42e2aa9b496d82c30b574120e68', 'HEAD', '--', 'labs/architecture/run_all.py'),
                          'judgment': 'Only optional Git metadata and source_revision_kind changed; sixteen runners independently rerun from the downloadable unversioned archive.'}

packet = load(base / 'prepared/packet.json')
docs = {d['id']: d for d in packet['documents']}
assert len(docs) == 181 and len(packet['evidence']) == 63 and len(packet['diagrams']) == 94
for document in docs.values(): assert sha((root / document['path']).read_bytes()) == document['sha256'], document['path']
for diagram in packet['diagrams']:
    document = docs[diagram['document_id']]
    fences = re.findall(r'^```mermaid[^\n]*\n(.*?)^```\s*$', (root / document['path']).read_text(), re.M | re.S)
    body = fences[diagram['fence_index'] - 1]
    assert sha(body.encode()) == diagram['syntax']['source_sha256'], diagram['id']
    assert diagram['syntax']['source_sha256'] == diagram['render']['source_sha256']
    artifact = Path(diagram['render']['artifact_path'])
    assert sha(artifact.read_bytes()) == diagram['render']['artifact_sha256']
report['packet'] = {'sha256': sha((base / 'prepared/packet.json').read_bytes()), 'status': packet['status'], 'documents_verified': 181,
                    'evidence': 63, 'diagram_source_and_render_bindings_verified': 94, 'per_document_reviews_in_packet': len(packet['reviews']),
                    'gaps': packet['gaps'], 'diagram_semantic_review_is_separate': True}
assert packet['status'] == 'PARTIAL'

projection_errors = []
content_files = [p for p in (root / 'content').rglob('*') if p.is_file()]
for source in content_files:
    relative = source.relative_to(root)
    target = root / 'sites/architecture-course' / relative
    if not target.is_file() or sha(source.read_bytes()) != sha(target.read_bytes()): projection_errors.append(str(relative))
assert not projection_errors, projection_errors
report['site_source_projection'] = {'files_checked': len(content_files), 'errors': projection_errors}
prerequisite = 'Para o caso de data, você também precisa de Node 20.9 ou posterior. Execute `npm ci --prefix labs/architecture` para instalar a versão do TypeScript fixada no lock dos laboratórios.'
old_prerequisite = 'Para o caso de data, você também precisa de Node 20.9 ou posterior e das dependências do curso instaladas com `npm ci`.'
changed_tutorials = git('diff', '--name-only', '32b80d5fc8eda42e2aa9b496d82c30b574120e68', 'HEAD', '--', 'content/tutoriais/casos').splitlines()
assert len(changed_tutorials) == 15
for relative in changed_tutorials:
    current = (root / relative).read_text()
    before = subprocess.check_output(['git', 'show', '32b80d5fc8eda42e2aa9b496d82c30b574120e68:' + relative], cwd=root, text=True)
    assert current.replace(prerequisite, old_prerequisite) == before, relative
report['prerequisite_delta'] = {'tutorials': changed_tutorials, 'count': 15, 'only_exact_dependency_sentence_changed': True}
journeys = sorted(p.name for p in (root / 'content/jornadas').iterdir() if p.is_dir())
assert len(journeys) == 18
missing_links = []
for case in journeys:
    targets = ['/jornadas/' + case + '/', '/explicacoes/casos/' + case + '/', '/tutoriais/casos/' + case + '/', '/guias/casos/' + case + '/', '/referencia/casos/' + case + '/']
    for target in targets:
        page = root / 'content' / target.strip('/') / 'index.mdx'
        assert page.is_file(), str(page)
        text = page.read_text()
        for sibling in targets:
            if sibling != target and sibling not in text: missing_links.append({'page': str(page.relative_to(root)), 'sibling': sibling})
assert not missing_links, missing_links
report['journey_integration'] = {'journeys': journeys, 'destination_pages_checked': 90, 'missing_sibling_links': missing_links}
manifest = load(root / 'sites/architecture-course/.openai/hosting.json')
assert 'static' not in manifest and manifest['r2'] == 'COURSE_ASSETS'
dist = root / 'sites/architecture-course/dist'
assert sorted(p.name for p in dist.iterdir()) == ['.openai', 'server']
assert sorted(p.name for p in (dist / 'server').iterdir()) == ['index.js']
report['worker_artifact'] = {'manifest_sha256': sha((root / 'sites/architecture-course/.openai/hosting.json').read_bytes()),
                            'has_public_static_assets': False, 'server_bundle_sha256': sha((dist / 'server/index.js').read_bytes()),
                            'isolated_dependencies': load(root / 'sites/architecture-course/server-build/package.json')}
report['verdict'] = 'PASS_WITH_DECLARED_DELIVERY_GAPS'
report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
(out / 'terminal-integrity.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({'verdict': report['verdict'], 'curation_concepts': 310, 'guard_checks': 375, 'documents': 181, 'diagrams': 94, 'journeys': 18, 'history_commits': 12697, 'fbi_issues': 595, 'packet_status': packet['status']}))
