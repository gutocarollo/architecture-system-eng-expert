"""Build a deterministic, source-only download of the course exercises."""
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
DESTINATION = ROOT / 'public/downloads/architecture-labs.zip'
selected = []
for path in sorted((ROOT / 'labs').rglob('*')):
    if not path.is_file() or path.is_symlink() or any(part in {'.venv', '__pycache__'} for part in path.parts):
        continue
    if path.suffix in {'.pyc', '.log'} or path.name == '.DS_Store':
        continue
    selected.append(path)
learning = ROOT / 'tasks/FBI-4991-arquitetura-nextra/execution/learning'
for name in ['concept-matrix.json', 'families.json']:
    selected.append(learning / name)
selected += sorted((learning / 'searches').glob('*.json'))
manifest = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in selected}
readme = '''# Laboratórios de arquitetura

Esta pasta reúne as cópias de aprendizado usadas nos tutoriais do curso. Os dados das práticas são fictícios. Os manifests identificam os commits históricos e os hashes das funções selecionadas; um resultado local não comprova implantação em produção.

## Comece por um caso

Abra o tutorial no site e execute seus comandos a partir desta pasta, que contém `labs/` e `tasks/`. Consulte o README da família escolhida. Python 3.11 ou mais recente e Node.js precisam estar no PATH. Alguns casos financeiros precisam de OpenSSL 3 e do SDK OpenTelemetry fixado em `labs/architecture/requirements-lock.txt`.

Antes de executar o caso de datas, execute `npm ci --prefix labs/architecture`. O lock fixa o compilador TypeScript usado para executar as funções históricas.

Para preparar o SDK local dos casos que precisam dele, execute `python3 labs/architecture/setup_labs.py`. O comando cria uma pasta `.venv` exclusiva dos laboratórios e baixa as versões fixadas. Ele não configura um exportador de telemetria externo.

Depois dessa preparação, `python3 labs/architecture/run_all.py` executa os quinze casos iniciais e os padrões de objetos. Em uma extração sem Git, o recibo marca a origem como `UNVERSIONED_SOURCE_SNAPSHOT`; os hashes dos arquivos continuam presentes. Use os comandos de cada tutorial para observar e editar o antes/depois.

Os dois casos em `labs/postgres-lineage` precisam das ferramentas PostgreSQL 16 ou mais recente no PATH. O runner inicia um servidor temporário, sem porta TCP, e verifica o próprio diretório antes de escrever. O caso em `labs/airflow-lock-retry` usa dependências locais controladas e não executa uma DAG nem um binário externo.

Os scripts que reextraem fontes de repositórios ou regeneram páginas são ferramentas de manutenção. Eles podem exigir os checkouts originais e não são necessários para executar os exercícios já entregues.

O arquivo `source-manifest.json` contém o SHA-256 de cada arquivo incluído. Preserve a cópia recebida e faça suas alterações em uma pasta separada quando o tutorial pedir.
'''
DESTINATION.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(DESTINATION, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    entries = [(str(path.relative_to(ROOT)), path.read_bytes()) for path in selected]
    entries += [('LEIA-ME.md', readme.encode()), ('source-manifest.json', (json.dumps(manifest, indent=2) + '\n').encode())]
    for relative, data in entries:
        info = zipfile.ZipInfo('architecture-labs/' + relative, date_time=(2026, 10, 15, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, data)
receipt = dict(observed_at=datetime.now(timezone.utc).isoformat(), source_files=len(selected),
               download=str(DESTINATION.relative_to(ROOT)), bytes=DESTINATION.stat().st_size,
               sha256=hashlib.sha256(DESTINATION.read_bytes()).hexdigest(), files=manifest,
               exclusions=['Virtual environments', 'Compiled Python', 'Log files', 'Symlinks'],
               note='The archive carries exercises and pinned setup instructions, not installed dependencies or a production database.')
(BASE / 'lab-bundle-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({key: receipt[key] for key in ['source_files', 'download', 'bytes', 'sha256']}))
