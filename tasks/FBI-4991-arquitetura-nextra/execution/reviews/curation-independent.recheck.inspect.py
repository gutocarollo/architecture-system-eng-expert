"""Read bound primary spans for the original HIGH-only warm recheck."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CURATION = ROOT / 'tasks/FBI-4991-arquitetura-nextra/execution/curation'
parser = argparse.ArgumentParser()
parser.add_argument('ids', nargs='+')
parser.add_argument('--role', default='all')
parser.add_argument('--source', default='')
args = parser.parse_args()
rows = {row['concept_id']: row for row in json.loads((CURATION / 'matrix.json').read_text())['concepts']}
judgments = json.loads((CURATION / 'author-adjudications.json').read_text())
seen = set()
for concept_id in args.ids:
    print('\nCONCEPT', concept_id)
    row = rows[concept_id]
    sources = {source['url'].split('#')[0]: source for source in row['base'] + row['application']}
    for evidence in judgments[concept_id]['primary_evidence']:
        if args.role != 'all' and evidence['role'] != args.role:
            continue
        source = sources[evidence['source_url'].split('#')[0]]
        if args.source and args.source not in source['path']:
            continue
        key = (source['artifact'], evidence['start_line'], evidence['end_line'])
        if key in seen:
            continue
        seen.add(key)
        lines = (ROOT / source['artifact']).read_text().splitlines()
        print('SOURCE', evidence['role'], source['repo'], source['path'], source['revision'])
        print('ARTIFACT', source['artifact'])
        print('AUTHOR_CLAIM', evidence['claim'])
        for index in range(evidence['start_line'] - 1, evidence['end_line']):
            print(f'{index + 1}: {lines[index]}')
