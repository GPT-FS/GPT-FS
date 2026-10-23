"""Check local site references and prohibited remote execution/network patterns."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

root = Path(__file__).resolve().parents[1] / 'website'


class References(HTMLParser):
    def handle_starttag(self, tag, attributes):
        for key, value in attributes:
            if key not in ('href', 'src', 'poster') or not value:
                continue
            url = urlsplit(value)
            if url.scheme or url.netloc or value.startswith('#'):
                continue
            assert (root / url.path).is_file(), f'Missing site asset: {value}'


References().feed((root / 'index.html').read_text(encoding='utf-8'))
for name in ('app.js', 'integrity.js'):
    code = (root / name).read_text(encoding='utf-8')
    for forbidden in ('innerHTML', 'outerHTML', 'eval(', 'sendBeacon', 'XMLHttpRequest', 'localStorage'):
        assert forbidden not in code, f'Unexpected pattern: {forbidden}'
print('PASS: referenced assets present; local-content rendering uses text nodes')
