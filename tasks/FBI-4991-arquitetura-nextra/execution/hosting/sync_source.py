"""Project the canonical Nextra source into the separate Sites checkout."""
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DESTINATION = ROOT / 'sites/architecture-course'
BASE = Path(__file__).resolve().parent
manifest = DESTINATION / '.openai/hosting.json'
hosting = json.loads(manifest.read_text())
if not hosting.get('project_id'):
    raise SystemExit('Register and persist the Sites project before synchronizing.')
files = []
for directory in ['app', 'content', 'patches', 'public/downloads']:
    for source in sorted((ROOT / directory).rglob('*')):
        if source.is_file() and not source.is_symlink():
            files.append(source)
for name in ['mdx-components.jsx', 'package.json', 'package-lock.json', 'jsconfig.json', 'next-env.d.ts']:
    if (ROOT / name).is_file():
        files.append(ROOT / name)
for source in files:
    destination = DESTINATION / source.relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
package = json.loads((DESTINATION / 'package.json').read_text())
package['scripts']['postbuild'] = 'pagefind --site out --output-path out/_pagefind'
package['scripts'].pop('check:course', None)
(DESTINATION / 'package.json').write_text(json.dumps(package, indent=2) + '\n')
(DESTINATION / 'next.config.mjs').write_text("""import nextra from 'nextra'

const withNextra = nextra({})

export default withNextra({
  poweredByHeader: false,
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true }
})
""")
(DESTINATION / '.gitignore').write_text('node_modules\n.next\nout\ndist\n.env*\n.sites-runtime\n.DS_Store\n')
if hosting.get('r2'):
    hosting.pop('static', None)
else:
    hosting['static'] = {'directory': 'out'}
manifest.write_text(json.dumps(hosting, indent=2) + '\n')
receipt = dict(observed_at=datetime.now(timezone.utc).isoformat(),
               source_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               project_id=hosting['project_id'],
               source_files={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
               projection_changes=['Static export with trailing slashes', 'Pagefind indexes the exported out directory'],
               access='Owner-private native Sites access; shared-password support is not established by this projection.')
(BASE / 'source-projection.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(dict(project_id=hosting['project_id'], projected_files=len(files), destination=str(DESTINATION))))
