import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'prototype/v0.1'))
import portable as p
from gptfs import Store, canonical, digest


class PortableTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db = self.root / 'a.gpt'
        self.s = Store.create(self.db, 'Interoperability fixture')
        self.o = self.s.put(b'one two\r\n\x00', origin='fixture:source')
        self.s.put(bytes(range(256)), 'bundle', 'fixture:binary', parents=[self.o])
        self.i = self.s.intent('Count', [self.o])
        self.a = self.s.admit(self.i, self.o, 'fixture')['receipt']
        self.s.run(self.i, self.o, self.a)
        self.cp = self.s.checkpoint()
        self.folder = self.root / 'directory'

    def tearDown(self):
        self.s.close()
        self.temp.cleanup()

    def roundtrip(self):
        original = p.snapshot(self.db)
        p.export_directory(self.db, self.folder)
        restored = self.root / 'b.gpt'
        p.import_directory(self.folder, restored)
        self.assertEqual(original, p.snapshot(restored))
        return restored

    def test_roundtrip_bytes_ids_lineage_receipts_and_checkpoint(self):
        restored = self.roundtrip()
        self.assertEqual(p.replay(p.snapshot(restored), self.cp)['head'], self.cp['head'])

    def test_second_roundtrip_identical_directory(self):
        restored = self.roundtrip()
        second = self.root / 'second'
        p.export_directory(restored, second)
        for path in self.folder.rglob('*'):
            if path.is_file():
                self.assertEqual(path.read_bytes(), (second / path.relative_to(self.folder)).read_bytes())

    def test_policy_denial_survives_conversion(self):
        restored = self.roundtrip()
        s = Store(restored)
        try:
            self.assertEqual(s.run(self.i, self.o, self.a, 'shell.exec')['status'], 'denied')
        finally:
            s.close()

    def test_unknown_extension_bytes_preserved_without_policy_approval(self):
        # Add opaque manifest data and correctly rehash the whole chain in this fixture.
        m = self.s.manifest()
        m['extensions'] = {'example.future': {'opaque': ['α', 42]}}
        m['required_extensions'] = ['example.future']
        self.s.db.execute('DROP TRIGGER manifest_update')
        self.s.db.execute('UPDATE manifest SET body=?', (canonical(m),))
        self.s.db.execute('DROP TRIGGER events_update')
        previous = None
        # Use a fresh genesis-only fixture to avoid rewriting event references.
        for table in ('events', 'objects', 'blobs'):
            self.s.db.execute(f'DROP TRIGGER {table}_delete')
            self.s.db.execute(f'DELETE FROM {table}')
        self.s._event('genesis', {'manifest': digest(canonical(m))}, 'Drew')
        self.s.db.commit()
        restored = self.roundtrip()
        with self.assertRaisesRegex(ValueError, 'required extension'):
            p.replay(p.snapshot(restored))

    def test_tampered_payload_rejected(self):
        p.export_directory(self.db, self.folder)
        (self.folder / 'blobs/00000000.bin').write_bytes(b'changed')
        with self.assertRaises(ValueError): p.read_directory(self.folder)

    def test_missing_relationship_rejected_independently(self):
        rows = p.snapshot(self.db)
        oid, raw = rows['objects'][0]
        o = json.loads(raw); o['parents'] = ['missing']
        raw = canonical(o)
        rows['objects'][0] = (digest(b'GPTFS:object:1\0' + raw), raw)
        with self.assertRaisesRegex(ValueError, 'relationship'): p.validate(rows)

    def test_external_checkpoint_detects_valid_tail_removal(self):
        rows = p.snapshot(self.db)
        rows['events'].pop()
        self.assertEqual(p.validate(rows)['integrity'], 'valid')
        with self.assertRaisesRegex(ValueError, 'history'): p.validate(rows, self.cp)

    def test_forged_policy_passes_hashes_but_fails_semantic_replay(self):
        rows = p.snapshot(self.db)
        seq, eid, raw = rows['events'][-1]
        e = json.loads(raw); e['data']['capability'] = 'shell.exec'
        raw = canonical(e)
        rows['events'][-1] = (seq, digest(b'GPTFS:event:1\0' + raw), raw)
        self.assertEqual(p.validate(rows)['policy'], 'not-evaluated')
        with self.assertRaisesRegex(ValueError, 'execution'): p.replay(rows)

    def test_path_traversal_rejected(self):
        p.export_directory(self.db, self.folder)
        index = json.loads((self.folder / 'index.json').read_text())
        index['tables']['manifest'][0]['file'] = '../a.gpt'
        (self.folder / 'index.json').write_text(json.dumps(index))
        with self.assertRaisesRegex(ValueError, 'path'): p.read_directory(self.folder)

    def test_extra_files_rejected_instead_of_lost(self):
        p.export_directory(self.db, self.folder)
        (self.folder / 'unknown').write_bytes(b'preserve me')
        with self.assertRaisesRegex(ValueError, 'unindexed'): p.read_directory(self.folder)

    def test_unknown_tables_rejected_instead_of_lost(self):
        self.s.db.execute('CREATE TABLE future(data BLOB)'); self.s.db.commit()
        with self.assertRaisesRegex(ValueError, 'unsupported tables'): p.snapshot(self.db)

    def test_existing_destinations_not_overwritten(self):
        p.export_directory(self.db, self.folder)
        with self.assertRaises(ValueError): p.export_directory(self.db, self.folder)
        before = self.db.read_bytes()
        with self.assertRaises(ValueError): p.import_directory(self.folder, self.db)
        self.assertEqual(before, self.db.read_bytes())

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'): p.parse('{"x":1,"x":2}')

    def test_real_sample_roundtrip_and_replay(self):
        source = ROOT / 'prototype/v0.1/sample/research.gpt'
        p.export_directory(source, self.folder)
        p.import_directory(self.folder, self.root / 'real.gpt')
        self.assertEqual(p.snapshot(source), p.snapshot(self.root / 'real.gpt'))
        cp = json.loads((source.parent / 'checkpoint.json').read_text())
        self.assertTrue(p.replay(p.read_directory(self.folder), cp)['ok'])


if __name__ == '__main__':
    unittest.main()
