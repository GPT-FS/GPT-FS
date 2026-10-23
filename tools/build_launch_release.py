"""Build a reproducible synthetic runtime/demo kit, without recovered third-party samples."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.1.1-rc.1'


def build(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    paths = [ROOT / name for name in ('LICENSE', 'CHARTER.md', 'SPEC.md', 'SECURITY.md', 'COMPATIBILITY.md', 'LICENSING.md', 'NAMING.md', 'ARCHITECTURE.md')]
    paths += [ROOT / 'prototype/v0.1' / name for name in ('gptfs.py', 'gptfs.pyz', 'gptfs.cmd', 'LICENSE')]
    paths += [ROOT / 'tools' / name for name in ('portable.py', 'browser_snapshot.py')]
    paths += [p for p in (ROOT / 'website').rglob('*') if p.is_file() and p.name != 'package.json']
    files = {p.relative_to(ROOT).as_posix(): p.read_bytes() for p in paths}
    # Normalize new text sources across Windows/Linux checkouts; preserve all
    # historical prototype files and binary payloads exactly.
    for name, raw in files.items():
        if not name.startswith('prototype/') and (Path(name).suffix in {'.md','.py','.js','.css','.html','.svg','.vtt','.txt','.json'} or name == 'LICENSE'):
            files[name] = raw.replace(b'\r\n', b'\n')
    files['START-HERE.md'] = b'''# GPTFS public demo runtime kit 0.1.1-rc.1

This candidate packages the unchanged GPTFS 0.1 engine, experimental transport,
browser inspector, and wholly synthetic public fixtures. It does not change the
GPTFS 0.1 on-disk profile. No recovered Idea Lab sample is included.

Python 3.10+, standard library only. From this extracted directory:

    python prototype/v0.1/gptfs.pyz verify website/data/demo.gpt --checkpoint website/data/demo.checkpoint.json
    python tools/portable.py export website/data/demo.gpt notebook
    python tools/portable.py verify notebook --policy
    python tools/portable.py import notebook restored.gpt
    python tools/browser_snapshot.py restored.gpt mine.snapshot.json

For the browser inspector, serve website/ over localhost with correct JavaScript
MIME types or use https://gpt-fs.github.io/GPT-FS/ and open mine.snapshot.json.
The hosted page loads no local file onto a server. See docs in the source repository
for the complete test suite, original artifact audit, and recorded walkthrough.

Integrity checks do not evaluate authority. Revocation, authenticated grants,
independent full policy replay and a writable directory runtime remain open work.
Names are provisional. Review NAMING.md and LICENSING.md before a branded release.
'''
    inventory = [{'path': name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()} for name, raw in sorted(files.items())]
    files['MANIFEST.json'] = (json.dumps({'version': VERSION, 'profile': 'GPTFS 0.1.0 / schema 1', 'files': inventory}, indent=2) + '\n').encode()
    archive = output / f'GPTFS-public-demo-{VERSION}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(f'GPTFS-public-demo-{VERSION}/{name}', date_time=(2026,10,23,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, raw)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'SHA256SUMS.txt').write_text(f'{checksum}  {archive.name}\n', encoding='ascii')
    print(f'Built {archive.name}: {len(inventory)} files, SHA256 {checksum}')
    return archive


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', default='build/release')
    build(p.parse_args().output)
