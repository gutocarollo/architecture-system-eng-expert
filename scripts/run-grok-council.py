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

packet = json.loads((BASE / 'prepared-council/packet.json').read_text())
evidence_ids = ['original-request', 's5', 'l5a', 'l5b', 'l5c', 'bootstrap',
                'cache-code', 'singleflight-code', 'nextbilling-code',
                'task-worker-code', 'airflow-client-code',
                'report-api', 'report-service', 'report-repository',
                'insurance-api', 'insurance-service', 'insurance-repository']
documents = [item for item in packet['documents']
             if item['author_id'] == '/root/s5_operational_patterns']
assert len(documents) == 10
review_inputs = []
for document in documents:
    content = (ROOT / document['path']).read_text()
    assert hashlib.sha256(content.encode()).hexdigest() == document['sha256']
    digest, projection = review_context_digest(packet, document['id'], evidence_ids)
    review_inputs.append({'document': document, 'content': content,
                         'context_sha256': digest,
                         'relation_ids': document['relation_ids'],
                         'diagrams': [d for d in packet['diagrams']
                                      if d['document_id'] == document['id']]})

input_data = {
    'scope': packet['scope'], 'sources': packet['sources'],
    'documents': review_inputs,
    'evidence': [e for e in packet['evidence'] if e['id'] in evidence_ids],
    'relations': packet['relations'],
    'method': 'Diataxis: explanations, tutorials, how-to guides and reference are distinct purposes.',
    'reviewer_id': 'openrouter/x-ai/grok-4.7',
}
system_prompt = '''You are an independent documentation council reviewer. Review the actual supplied MDX and exact code/evidence against the original user request. You did not author it. Your lane is cache, concurrency, resilience/capacity, APIs/integration and observability, including their five catalogs. Use complete readable Portuguese for findings. Examine all ten documents and every Mermaid fence, failure boundaries, guarantees, scoped local/runtime facts, examples, references and teaching. A name mention is not explanation. A URL alone is not proof of its code. Do not invent production implementation or promote an educational REF sample to PROD. The request requires a concrete base/framework and real OSS implementation per concept; flag actual missing coverage, while a code product that implements the mechanism can be an actual OSS application. Distinguish unsupported global claims from explicitly scoped snapshots and hypothetical financial examples. Select APPROVED only if no high finding remains for that document. Never fabricate approval for a mechanical gate. Report medium/low editorial issues separately without treating every style preference as a blocker.
Return one JSON object, without markdown fences: {"reviewer_id":"openrouter/x-ai/grok-4.7","summary":"...","document_reviews":[{"document_id":"exact supplied id","document_sha256":"exact supplied sha","context_sha256":"exact supplied context sha","verdict":"APPROVED or CHANGES_REQUESTED","open_high_findings":["finding IDs"],"relation_ids":["supplied relevant relation IDs"],"evidence_ids":["actually examined supplied evidence IDs"],"diagram_reviews":[{"fence_index":1,"status":"PASS or FAIL","reason":"..."}]}],"findings":[{"id":"G1","severity":"HIGH or MEDIUM or LOW","document_id":"...","anchor":"...","claim":"...","evidence":"...","repair":"..."}],"limits":["..."]}. Include all ten documents exactly once and each diagram of that document. You may not edit files or operate any live system.'''
payload = {'model': 'x-ai/grok-4.7', 'reasoning': {'effort': 'xhigh'},
           'max_tokens': 32768,
           'messages': [{'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': json.dumps(input_data, ensure_ascii=False)}]}
input_bytes = json.dumps(payload, ensure_ascii=False).encode()
key = subprocess.run(['security', 'find-generic-password', '-s',
                      'com.fazcapital.openrouter', '-w'], check=True,
                     capture_output=True, text=True).stdout.strip()
request = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
                                 data=input_bytes,
                                 headers={'Authorization': 'Bearer ' + key,
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
output_path = BASE / 'reviews/grok-response.json'
output_path.parent.mkdir(exist_ok=True)
output_path.write_text(content + '\n')
receipt = {'http_status': status, 'started_at': started_at,
           'finished_at': datetime.now(timezone.utc).isoformat(),
           'model_requested': payload['model'], 'model_returned': result.get('model'),
           'dispatch_id': result.get('id'), 'reasoning_effort_requested': 'xhigh',
           'usage': result.get('usage'), 'finish_reason': result['choices'][0].get('finish_reason'),
           'input_sha256': hashlib.sha256(input_bytes).hexdigest(),
           'output_sha256': hashlib.sha256((content + '\n').encode()).hexdigest(),
           'document_versions': [{k: item[k] for k in ('document_id', 'document_sha256', 'context_sha256')}
                                 for item in [{'document_id': d['document']['id'],
                                               'document_sha256': d['document']['sha256'],
                                               'context_sha256': d['context_sha256']}
                                              for d in review_inputs]],
           'evidence_ids': evidence_ids}
(BASE / 'reviews/grok-dispatch.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k: receipt[k] for k in ('http_status', 'model_returned', 'dispatch_id', 'finish_reason')}))
