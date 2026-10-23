"""Verify every recovered archive member and embedded executable source."""
import hashlib
import json
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
base = root / 'prototype/v0.1'
inventory = json.loads((root / 'audit/archive-inventory.json').read_text())
for entry in inventory:
    raw = (base / entry['path']).read_bytes()
    assert len(raw) == entry['bytes'], entry['path']
    assert hashlib.sha256(raw).hexdigest() == entry['sha256'], entry['path']
with zipfile.ZipFile(base / 'gptfs.pyz') as z:
    assert z.read('gptfs.py') == (base / 'gptfs.py').read_bytes()
print(f'PASS: {len(inventory)} original members unchanged; pyz source matches')
