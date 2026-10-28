#!/usr/bin/env python3
"""Recompute one reviewed historical MDX without running the final matrix builder."""
import ast
import datetime
import gzip
import hashlib
import json
import platform
import re
import tempfile
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[3]
CUR=BASE.parent/'curation'
digest=lambda raw:hashlib.sha256(raw).hexdigest()
document_path='content/referencia/curadoria/09-apis-e-integracao.mdx'
review_path=BASE.parent/'reviews/curation-independent.recheck.json'
review=json.loads(review_path.read_text())
expected=review['bound_file_sha256'][document_path]
archive=BASE/'rechecked-matrix-fa8e01.json.gz'
input_bytes=gzip.decompress(archive.read_bytes())
input_sha=digest(input_bytes)
assert input_sha==review['matrix_sha256']=='fa8e01dcc2bd0126ac085eed97452dff6d193448f588c9a078201fab259ddde0'
matrix=json.loads(input_bytes)
coverage_path=ROOT/'tasks/architecture-course-2026-10-14/evidence/coverage.json'
coverage_bytes=coverage_path.read_bytes()
assert digest(coverage_bytes)==matrix['scope']['coverage_sha256']
coverage=json.loads(coverage_bytes)
heading_path=CUR/'heading-slugs.json'
headings=json.loads(heading_path.read_text())
protected_paths=sorted((ROOT/'content/referencia').rglob('*.mdx'))+[CUR/name for name in [
    'matrix.json','matrix.json.gz','sources.json','sources.json.gz','freeze-receipt.json',
    'matrix.publication.json','sources.publication.json','publication-index.json']]
before={str(p.relative_to(ROOT)):digest(p.read_bytes())for p in protected_paths}

builder_path=CUR/'build_matrix.py'
builder=builder_path.read_text()
start=builder.index('# Render searchable pages with one canonical heading per concept.')
end=builder.index('\npacks=',start)
family_block=ast.parse(builder[start:end])
nodes=[node for node in family_block.body if isinstance(node,ast.FunctionDef) and node.name in ['safe_mdx_text','link_item']]
nodes += [node for node in family_block.body if isinstance(node,ast.For) and isinstance(node.target,ast.Tuple)
          and [item.id for item in node.target.elts]==['group','info']]
assert len(nodes)==3
replacements={
 'Uma correspondência autoral registra a seleção do mecanismo e de suas fontes. A situação independente vem do parecer real vinculado a cada item e vale para o recorte e os limites declarados. Uma pendência continua sendo requisito aberto; nenhum conceito recebeu dispensa por não se aplicar.\n\n':
 'Uma correspondência autoral significa que o autor selecionou o mecanismo e suas fontes. A revisão independente desta nova matriz ainda é um gate separado. Uma pendência continua sendo requisito aberto; nenhum conceito recebeu dispensa por não se aplicar.\n\n',
 '**A revisão independente aceitou este recorte delimitado.** O mecanismo e os limites abaixo foram conferidos; as observações da revisão continuam nos recibos vinculados ao item.\n\n':
 '**A primeira revisão independente aceitou este recorte.** O fingerprint semântico foi preservado; as observações dessa revisão continuam no registro do item.\n\n',
}
class RestoreHistoricalStatus(ast.NodeTransformer):
    def __init__(self):
        self.count=0
    def visit_Constant(self,node):
        if isinstance(node.value,str) and node.value in replacements:
            self.count+=1
            return ast.copy_location(ast.Constant(replacements[node.value]),node)
        return node
transform=RestoreHistoricalStatus()
module=ast.Module(body=nodes,type_ignores=[])
module=ast.fix_missing_locations(transform.visit(module))
assert transform.count==2
renderer_path=BASE/'historical-fa8e01-family-renderer.py'
renderer_source=(
    '# Historical family renderer reconstructed for the fa8e01 matrix.\n'
    '# Globals are supplied by reconstruct_historical_mdx.py inside a temporary directory.\n'
    +ast.unparse(module)+'\n')
renderer_path.write_text(renderer_source)
group=next(item for item in coverage['groups']if Path(item['reference_path']).stem=='09-apis-e-integracao')
with tempfile.TemporaryDirectory(prefix='historical-mdx-',dir=BASE) as temporary:
    destination=Path(temporary)
    namespace=dict(json=json,re=re,Path=Path,entries=matrix['concepts'],group_info={group['group']:group},
                   heading_slugs=headings,slugs={group['group']:'09-apis-e-integracao'},DEST=destination)
    exec(compile(renderer_source,str(renderer_path),'exec'),namespace)
    rendered=(destination/'09-apis-e-integracao.mdx').read_bytes()
    actual=digest(rendered)
    output=BASE/'historical-mdx/09-apis-e-integracao-fa8e01.mdx'
    output.parent.mkdir(exist_ok=True)
    output.write_bytes(rendered)
assert len(rendered)<1_000_000
assert actual==expected,(actual,expected)
after={str(p.relative_to(ROOT)):digest(p.read_bytes())for p in protected_paths}
assert before==after,'A protected final file changed during the isolated reconstruction.'
receipt=dict(
    observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    document_path=document_path,
    historical_document_path=str(output.relative_to(ROOT)),
    recomputed_sha256=actual,
    expected_review_sha256=expected,
    match=actual==expected,
    bytes=len(rendered),
    renderer=dict(path=str(renderer_path.relative_to(ROOT)),sha256=digest(renderer_path.read_bytes()),
                  basis='Pure family renderer, with the two final review-status strings restored to the fa8e01 wording.',
                  historical_status_substitutions=transform.count,
                  extracted_from=str(builder_path.relative_to(ROOT)),
                  extracted_from_sha256=digest(builder_path.read_bytes()),python=platform.python_version()),
    reproducer=dict(path=str(Path(__file__).resolve().relative_to(ROOT)),sha256=digest(Path(__file__).read_bytes())),
    input=dict(path=str(archive.relative_to(ROOT)),archive_sha256=digest(archive.read_bytes()),
               contents_sha256=input_sha,coverage_sha256=digest(coverage_bytes),heading_slugs_sha256=digest(heading_path.read_bytes())),
    review=dict(path=str(review_path.relative_to(ROOT)),sha256=digest(review_path.read_bytes()),
                value_location='bound_file_sha256[document_path]'),
    final_matrix_sha256=before['tasks/FBI-4991-arquitetura-nextra/execution/curation/matrix.json'],
    protected_final_files_checked=len(before),protected_final_files_unchanged=before==after,
    proof_scope='Recomputed historical document bytes only; no new semantic approval or change to final sources.',
    limit='The renderer is a compatible reconstruction of the historical family block, not a claim that the original entire generator file was recovered byte for byte.'
)
(BASE/'historical-mdx-hash-proof.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:receipt[k]for k in ['document_path','historical_document_path','recomputed_sha256','match','bytes','protected_final_files_unchanged','final_matrix_sha256']}))
