"""Publish committed website/ to the dedicated Pages branch, preserving its history.

Run only as an authorized maintainer after checks. Requires authenticated git.
Does not merge the development branch or publish a release.
"""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = 'https://github.com/GPT-FS/GPT-FS.git'


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


def publish():
    assert not git('status', '--porcelain'), 'Commit source changes before publication'
    sha = git('rev-parse', 'HEAD')
    # Use an explicitly owned temporary checkout under the workspace work directory.
    with tempfile.TemporaryDirectory(prefix='gptfs-pages-', dir=ROOT.parent) as temp:
        target = Path(temp).resolve()
        assert target.is_relative_to(ROOT.parent.resolve())
        git('init', '-b', 'gh-pages', cwd=target)
        git('remote', 'add', 'origin', REMOTE, cwd=target)
        if git('ls-remote', 'origin', 'refs/heads/gh-pages', cwd=target):
            git('fetch', 'origin', 'gh-pages', cwd=target)
            git('reset', '--hard', 'FETCH_HEAD', cwd=target)
        # Only remove previously tracked generated site files within this checkout.
        for name in git('ls-files', cwd=target).splitlines():
            p = (target / name).resolve()
            assert p.is_relative_to(target) and '.git' not in p.relative_to(target).parts
            if p.is_file(): p.unlink()
        for source in (ROOT / 'website').rglob('*'):
            if source.is_file() and source.name != 'package.json':
                dest = target / source.relative_to(ROOT / 'website')
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, dest)
        (target / '.nojekyll').write_text('')
        (target / 'deployment.json').write_text(json.dumps({'source_commit': sha, 'source_repository': REMOTE, 'source_path': 'website', 'status': 'launch-preview'}, indent=2) + '\n')
        git('add', '--all', cwd=target)
        git('commit', '-m', f'Publish launch preview from {sha}', cwd=target)
        git('push', 'origin', 'gh-pages', cwd=target)
        print(f'Published Pages branch from {sha}; check GitHub Pages build before reporting live.')


if __name__ == '__main__':
    publish()
