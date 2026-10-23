import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from browser_snapshot import browser_snapshot
from portable import export_directory


class BrowserSnapshotTests(unittest.TestCase):
    def test_export_retains_records_and_checkpoint(self):
        source = ROOT/'website/data/demo.gpt'
        cp = json.loads((source.parent/'demo.checkpoint.json').read_text())
        data = browser_snapshot(source,cp)
        self.assertEqual(data, json.loads((source.parent/'demo.snapshot.json').read_text()))

    def test_both_storage_bindings_export_identical_browser_data(self):
        source = ROOT/'website/data/demo.gpt'
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)/'snapshot'
            export_directory(source,directory)
            self.assertEqual(browser_snapshot(source),browser_snapshot(directory))

    def test_foreign_checkpoint_rejected(self):
        cp = json.loads((ROOT/'website/data/demo.checkpoint.json').read_text())
        cp['project_id'] = 'foreign'
        with self.assertRaises(ValueError):
            browser_snapshot(ROOT/'website/data/demo.gpt',cp)


if __name__ == '__main__':
    unittest.main()
