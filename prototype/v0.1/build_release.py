"""Build the Python executable and release ZIP from this directory."""
import hashlib
import zipfile
from pathlib import Path


def build():
    root = Path(__file__).resolve().parent
    executable = root / 'gptfs.pyz'
    with zipfile.ZipFile(executable, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('__main__.py', 'from gptfs import main\nraise SystemExit(main())\n')
        z.write(root / 'gptfs.py', 'gptfs.py')
    package = root.parent / 'GPTFS-v0.1.0.zip'
    with zipfile.ZipFile(package, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith(('.pyc', '-journal', '-wal', '-shm')):
                z.write(p, root.name + '/' + p.relative_to(root).as_posix())
    checksum = hashlib.sha256(package.read_bytes()).hexdigest()
    (root.parent / 'GPTFS-v0.1.0.sha256').write_text(checksum + '  ' + package.name + '\n', encoding='ascii')
    print(f'{package.name}: {package.stat().st_size} bytes; SHA256 {checksum}')


if __name__ == '__main__':
    build()
