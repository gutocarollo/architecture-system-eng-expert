"""Package the versioned case files without keeping another editable source."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / 'public/downloads/early-refresh.zip'
FILES = ('run.py', 'before.py', 'after.py', 'source.diff', 'manifest.json')

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(OUTPUT, 'w', compression=ZIP_DEFLATED) as archive:
    for filename in FILES:
        source = ROOT / 'labs/architecture/early-refresh' / filename
        entry = ZipInfo(f'early-refresh-lab/labs/architecture/early-refresh/{filename}', (2026, 10, 24, 0, 0, 0))
        entry.compress_type = ZIP_DEFLATED
        entry.external_attr = 0o644 << 16
        archive.writestr(entry, source.read_bytes())
print(f'Packaged {len(FILES)} versioned files: {OUTPUT.relative_to(ROOT)}')
