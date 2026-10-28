"""Extract immutable SQL kernels; running the labs needs no MakersHub access."""
import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--source-repo', required=True)
args = parser.parse_args()
output = Path(__file__).resolve().parent
cases = [
    ('grain', 'backend/app/repositories/account.py', 'get_family_revenue_by_period',
     'b1df42295ce42d593ae14f0a8a9092c28d1b410d', '05b2cacdddd59b968641b12d8d124bad1888392f'),
    ('revision', 'backend/app/repositories/employee_repository.py', 'update_employee_scd2_without_commit',
     '3ad846049c32fedee09d458c8d685fb39b675b82', 'c5e8efc5913355a8545b8a27b8b72e0828f77660'),
]
manifest = {}
for case, source_path, symbol, before, after in cases:
    entry = dict(path=source_path, function=symbol, before=before, after=after, sources={})
    for condition, revision in [('before', before), ('after', after)]:
        raw = subprocess.check_output(['git', '-C', args.source_repo, 'show', revision + ':' + source_path])
        source = raw.decode()
        tree = ast.parse(source)
        function = next(node for node in ast.walk(tree)
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol)
        candidates = []
        for node in ast.walk(function):
            if case == 'grain' and isinstance(node, ast.Constant) and isinstance(node.value, str) and 'months AS' in node.value:
                candidates.append(node.value)
            if case == 'revision' and isinstance(node, ast.JoinedStr):
                value = ''.join(part.value if isinstance(part, ast.Constant)
                                else '{' + ast.unparse(part.value) + '}' for part in node.values)
                if 'UPDATE {EMPLOYEE_TABLE}' in value:
                    candidates.append(value)
        if len(candidates) != 1:
            raise RuntimeError(f'Expected one SQL kernel: {case}/{condition}, got {len(candidates)}')
        template = candidates[0]
        template_name = f'{case}-{condition}.sql.template'
        (output / template_name).write_text(template)
        (output / f'{case}-{condition}.function.txt').write_text(
            '\n'.join(source.splitlines()[function.lineno - 1:function.end_lineno]) + '\n')
        entry['sources'][condition] = dict(
            sha=revision, file_sha256=hashlib.sha256(raw).hexdigest(),
            function_lines=[function.lineno, function.end_lineno],
            template_sha256=hashlib.sha256(template.encode()).hexdigest(), template=template_name)
    manifest[case] = entry
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Extracted four SQL kernels from the recorded source revisions.')
