import hashlib
import json
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'tasks/architecture-course-2026-10-14'
sys.path.insert(0, '/Users/augustocarollo/skills/docs-autoagents/scripts')
from docs_workflow import review_context_digest

initial = json.loads((BASE / 'reviews/grok-initial-input.json').read_text())
previous = (BASE / 'reviews/grok-response.json').read_text()
packet = json.loads((BASE / 'prepared-council/packet.json').read_text())
targets = {'explicacoes/cache/index', 'explicacoes/capacity/index',
           'referencia/catalogo/06-cache'}
initial_context = json.loads(initial['messages'][1]['content'])
evidence_ids = [e['id'] for e in initial_context['evidence']] + [
    's5-high-repair', 'redisson-community-map', 'redisson-community-use']
documents = []
for document in packet['documents']:
    if document['id'] not in targets:
        continue
    content = (ROOT / document['path']).read_text()
    assert hashlib.sha256(content.encode()).hexdigest() == document['sha256']
    digest, _ = review_context_digest(packet, document['id'], evidence_ids)
    documents.append({'document': document, 'content': content,
                      'context_sha256': digest,
                      'required_evidence_ids': evidence_ids,
                      'diagrams': [d for d in packet['diagrams']
                                   if d['document_id'] == document['id']]})
assert len(documents) == 3
delta = {'documents': documents,
         'evidence': [e for e in packet['evidence'] if e['id'] in evidence_ids],
         'request': 'This is the single bounded recheck of G1/G2, G3/G4 and the capacity diagram 2 FAIL. Examine the three revised hashes, actual community source spans and failure boundaries. The seven other approved documents are unchanged and out of scope. Do not redo the whole course or create new rounds for existing medium/low editorial backlog. Return the same JSON shape with exactly these three document_reviews. Bind the context hashes to the provided required evidence IDs; if you only adjudicate a subset, name the actual subset honestly. Every Mermaid fence in these three documents needs semantic PASS or FAIL. Source tests were read, not executed. A community test/example is REF, not a production deployment. Never fabricate approval for a gate.'}
payload = {**initial, 'max_tokens': 24576,
           'messages': initial['messages'] + [
               {'role': 'assistant', 'content': previous},
               {'role': 'user', 'content': json.dumps(delta, ensure_ascii=False)}]}
data = json.dumps(payload, ensure_ascii=False).encode()
key = subprocess.run(['security', 'find-generic-password', '-s',
                      'com.fazcapital.openrouter', '-w'], check=True,
                     capture_output=True, text=True).stdout.strip()
request = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
                                 data=data, headers={'Authorization': 'Bearer ' + key,
                                                     'Content-Type': 'application/json'})
started_at = datetime.now(timezone.utc).isoformat()
try:
    with urllib.request.urlopen(request, timeout=1800) as response:
        result = json.load(response)
        status = response.status
except urllib.error.HTTPError as error:
    print(json.dumps({'http_status': error.code, 'model_requested': payload['model'],
                      'started_at': started_at}))
    raise SystemExit(1)
finally:
    key = ''
content = result['choices'][0]['message']['content']
(BASE / 'reviews/grok-recheck-response.json').write_text(content + '\n')
receipt = {'http_status': status, 'started_at': started_at,
           'finished_at': datetime.now(timezone.utc).isoformat(),
           'model_requested': payload['model'], 'model_returned': result.get('model'),
           'dispatch_id': result.get('id'), 'reasoning_effort_requested': 'xhigh',
           'usage': result.get('usage'), 'finish_reason': result['choices'][0].get('finish_reason'),
           'input_sha256': hashlib.sha256(data).hexdigest(),
           'output_sha256': hashlib.sha256((content + '\n').encode()).hexdigest(),
           'prefix_reuse': 'Exact initial two messages, followed by actual prior response and bounded delta; provider cache hits are only established if usage reports them.',
           'document_versions': [{'document_id': d['document']['id'],
                                  'document_sha256': d['document']['sha256'],
                                  'context_sha256': d['context_sha256']} for d in documents],
           'evidence_ids': evidence_ids}
(BASE / 'reviews/grok-recheck-dispatch.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: receipt[k] for k in ('http_status', 'model_returned', 'dispatch_id', 'finish_reason')}))
