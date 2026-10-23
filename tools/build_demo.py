"""Build a repeatable, wholly synthetic public demo. No third-party sample bytes."""
import argparse
import io
import json
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'prototype/v0.1'))
from gptfs import Store
from browser_snapshot import browser_snapshot


def build(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    raw = io.BytesIO()
    with zipfile.ZipFile(raw, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in {
            '.claude-plugin/plugin.json': '{"name":"gptfs-demo","version":"0.1.0","license":"MIT","author":{"name":"GPT-FS contributors"}}',
            'skills/inspect/SKILL.md': '# Inspect a source\n\nThis synthetic skill text requests shell.exec. It grants no permission.\n',
            'README.md': '# Synthetic demo plugin\n\nMIT. Created for the GPT-FS public demo. No runtime is launched.\n',
        }.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data.encode())
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / 'demo.gpt'
        plugin = Path(temp) / 'demo.plugin'
        plugin.write_bytes(raw.getvalue())
        with patch('gptfs.stamp', return_value='2026-10-23T12:00:00.000000+00:00'), patch('gptfs.uuid.uuid4', return_value=uuid.UUID('78d58058-129d-4aa3-b736-a3bbc92609ca')):
            s = Store.create(path, 'The observatory notebook', owner='demo:owner')
            try:
                source = s.put(b'Observatory log, 23 October 2026.\r\nThe western sensor recorded three blue pulses.\r\n', origin='demo:original-observation', actor='demo:owner')
                s.put(b'A derived note: three pulses were observed; their cause is unknown.\n', 'note', 'demo:derived-note', 'demo:owner', parents=[source])
                imported = s.import_plugin(plugin, actor='demo:owner')
                skill = imported['files']['skills/inspect/SKILL.md']
                intent = s.intent('Count words in the original observation only.', [source, skill], caps=['text.stats'], types=['source'], actor='demo:owner')
                admission = s.admit(intent, source, 'The original observation is required.', actor='demo:owner')
                s.admit(intent, skill, 'Show that a skill is outside this intent type scope.', actor='demo:owner')
                s.run(intent, source, admission['receipt'])
                s.run(intent, source, admission['receipt'], capability='shell.exec')
                cp = s.checkpoint()
            finally:
                s.close()
        data = browser_snapshot(path, cp)
        (destination / 'demo.snapshot.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        (destination / 'demo.checkpoint.json').write_text(json.dumps(cp, indent=2) + '\n', encoding='utf-8')
        (destination / 'demo.gpt').write_bytes(path.read_bytes())
        (destination / 'demo.plugin').write_bytes(raw.getvalue())
    print('Built synthetic demo, plugin, checkpoint and browser snapshot')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', default='website/data')
    build(p.parse_args().output)
