"""Render bounded primary-source review packets without changing author files."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
CURATION = ROOT / 'tasks/FBI-4991-arquitetura-nextra/execution/curation'
parser = argparse.ArgumentParser()
parser.add_argument('concepts', nargs='+')
parser.add_argument('--context', type=int, default=7)
parser.add_argument('--max-hits', type=int, default=2)
parser.add_argument('--role', default='application')
parser.add_argument('--max-sources', type=int, default=999)
args = parser.parse_args()
matrix = json.loads((CURATION / 'matrix.json').read_text())
for row in matrix['concepts']:
    if row['concept_id'] not in args.concepts and str(matrix['concepts'].index(row)) not in args.concepts:
        continue
    print('\nCONCEPT', row['concept_id'], 'GROUPS', row['groups'])
    print('MECHANISM', row['mechanism'])
    print('LIMITS', row['limits'])
    if row.get('classification_basis'):
        print('CLASSIFICATION', row['classification_basis'])
    sources = {s['url']: s for role in ['base', 'application'] for s in row[role]}
    source_count = 0
    for evidence in row['source_evidence']:
        if args.role != 'all' and evidence['role'] != args.role:
            continue
        source = sources.get(evidence['source_url'])
        if not source or not source.get('artifact'):
            continue
        if source_count >= args.max_sources:
            continue
        source_count += 1
        lines = (ROOT / source['artifact']).read_text().splitlines()
        print('SOURCE', evidence['role'], source['repo'], source['path'], source['revision'])
        print('ARTIFACT', source['artifact'])
        printed = set()
        for hit in evidence['hits'][:args.max_hits]:
            start = max(1, hit['start_line'] - args.context)
            end = min(len(lines), hit['end_line'] + args.context)
            for index in range(start, end + 1):
                if index not in printed:
                    print(f'{index}: {lines[index - 1]}')
                    printed.add(index)
