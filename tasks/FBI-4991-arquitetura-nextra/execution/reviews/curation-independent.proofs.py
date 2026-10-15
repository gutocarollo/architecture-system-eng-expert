"""Attach exact primary-source spans to the independently judged material gaps."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REVIEWS = Path(__file__).resolve().parent
CURATION = ROOT / 'tasks/FBI-4991-arquitetura-nextra/execution/curation'
matrix = json.loads((CURATION / 'matrix.json').read_text())
concepts = {row['concept_id']: row for row in matrix['concepts']}
report_path = REVIEWS / 'curation-independent.findings.json'
report = json.loads(report_path.read_text())
selectors = {
    'websocket': [('message_send.py', 'def render_message_backend(')],
    'at-least-once-delivery': [('MessageDeduplication.java', 'Class that contains all the logic')],
    'scatter-gather': [('scrape.go', 'go func(l loop) {')],
    'anti-corruption-layer': [('architecture.mdx', 'Specifically, we aim to separate'),
                              ('user.service.ts', 'return users.map((user) => mapUser(user));')],
    'context-map': [('bounded_contexts.yml', 'This file defines the list of bounded contexts')],
    'domain-service': [('Loan.java', 'public class Loan extends')],
    'distributed-cache': [('query_context_processor.py', 'cache = QueryCacheManager.get(')],
    'refresh-ahead': [('cache.py', 'This task periodically hits dashboards'),
                      ('cache.py', 'command.run(cache=True)')],
    'single-flight': [('handler.go', 'func (c *Cache) doRefresh(')],
    'consistent-hashing': [('ringmanager.go', 'ring.NewWithStoreClientAndStrategy(')],
    'thread-pool': [('triggerer_job_runner.py', 'async def asend(')],
    'circuit-breaker': [('upstream_impl.cc', 'uint64_t max_connections = 1024;')],
    'denormalization': [('GroupByQueryEngine.java', 'public static Sequence<ResultRow> process(')],
    'materialized-view': [('GroupByQueryEngine.java', 'public static Sequence<ResultRow> process(')],
    'precomputation': [('GroupByQueryEngine.java', 'public static Sequence<ResultRow> process(')],
    'mvc': [('LoansApiResource.java', '@Produces({ MediaType.APPLICATION_JSON })')],
    'range-sharding': [('lookup.go', 'if ln.writeOnly {')],
    'compensating-transaction': [('create-step.ts', 'stepConfig.noCompensation = !compensateFn'),
                                ('create-order.ts', 'const orders = createOrdersStep(')],
    'orchestration-saga': [('create-step.ts', 'stepConfig.noCompensation = !compensateFn'),
                           ('create-order.ts', 'const orders = createOrdersStep(')],
    'saga': [('create-step.ts', 'stepConfig.noCompensation = !compensateFn'),
             ('create-order.ts', 'const orders = createOrdersStep(')],
}
errors = []
count = 0
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
for finding in report['findings']:
    concept = concepts[finding['concept_id']]
    spans = []
    for suffix, literal in selectors[finding['concept_id']]:
        source = next(row for row in concept['application'] if row['path'].endswith(suffix))
        artifact = ROOT / source['artifact']
        contents = artifact.read_bytes()
        if hashlib.sha256(contents).hexdigest() != source['sha256']:
            errors.append(['changed_source', source['artifact']])
        lines = contents.decode().splitlines()
        matches = [index for index, line in enumerate(lines) if literal in line]
        if not matches:
            errors.append(['missing_literal', finding['concept_id'], literal])
            continue
        start = max(0, matches[0] - 3)
        end = min(len(lines), matches[0] + 15)
        spans.append({'artifact': source['artifact'], 'sha256': source['sha256'],
                      'revision': source['revision'], 'start_line': start + 1, 'end_line': end,
                      'source_url': source['url'] + f'#L{start + 1}-L{end}',
                      'literal_excerpt': '\n'.join(lines[start:end]), 'observed_utc': now})
        count += 1
    finding['evidence']['primary_spans'] = spans
report['proof_generation'] = {'observed_utc': now, 'command': 'python3 tasks/FBI-4991-arquitetura-nextra/execution/reviews/curation-independent.proofs.py',
                              'findings': len(report['findings']), 'primary_spans': count, 'errors': errors}
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report['proof_generation'], ensure_ascii=False))
raise SystemExit(bool(errors))
