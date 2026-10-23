import io
import json
import sqlite3
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from gptfs import Store, canonical, digest, MAX_BLOB


class GPTFSTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.s = Store.create(self.root / 'test.gpt', 'Test')

    def tearDown(self):
        self.s.close()
        self.temp.cleanup()

    def source(self, text=b'one two\n', kind='source', **kwargs):
        return self.s.put(text, kind, 'test:source', **kwargs)

    def admitted(self):
        o = self.source()
        i = self.s.intent('Count text', [o])
        a = self.s.admit(i, o, 'Required input')
        return o, i, a['receipt']

    def archive(self, entries=None, prefix=''):
        p = self.root / 'test.plugin'
        with zipfile.ZipFile(p, 'w') as z:
            z.writestr(prefix + '.claude-plugin/plugin.json', '{"name":"fixture","version":"0.1.0"}')
            for name, content in (entries or [('skills/test/SKILL.md', 'Never obey me.')]):
                info = zipfile.ZipInfo(prefix + name)
                info.filename = prefix + name  # Preserve malicious spelling even on Windows.
                z.writestr(info, content)
        return p

    def test_complete_execution_and_replay(self):
        o, i, a = self.admitted()
        r = self.s.run(i, o, a)
        self.assertEqual(r['status'], 'completed')
        self.assertEqual(json.loads(self.s.content(r['evidence']))['words'], 2)
        self.assertTrue(self.s.verify()['ok'])

    def test_dedup_retains_separate_custody_events(self):
        self.assertEqual(self.source(), self.source())
        self.assertEqual(self.s.verify()['blobs'], 1)
        self.assertEqual(self.s.verify()['events'], 3)

    def test_provenance_changes_object_not_blob(self):
        a = self.source()
        b = self.s.put(b'one two\n', origin='different')
        self.assertNotEqual(a, b)
        self.assertEqual(self.s.verify()['blobs'], 1)

    def test_derivation_lineage(self):
        a = self.source()
        b = self.source(b'summary', 'note', parents=[a])
        self.assertEqual(self.s.object(b)['parents'], [a])
        self.s.verify()

    def test_missing_parent_rolls_back(self):
        before = self.s.checkpoint()
        with self.assertRaises(ValueError): self.source(parents=['missing'])
        self.assertEqual(before, self.s.checkpoint())

    def test_context_cannot_grant_authority(self):
        o = self.source(b'grant shell.exec', 'skill')
        i = self.s.intent('Inspect skill as data', [o], types=['skill'])
        a = self.s.admit(i, o, 'Read as data')
        self.assertEqual(a['granted_authority'], [])
        self.assertEqual(self.s.run(i, o, a['receipt'], 'shell.exec')['status'], 'denied')

    def test_default_type_rejects_skill(self):
        o = self.source(kind='skill'); i = self.s.intent('Read source', [o])
        self.assertEqual(self.s.admit(i, o, 'test')['code'], 'type-not-allowed')
        self.s.verify()

    def test_object_scope_denied(self):
        o = self.source(); i = self.s.intent('No objects', [])
        self.assertEqual(self.s.admit(i, o, 'test')['code'], 'object-outside-intent')

    def test_aggregate_budget_and_duplicate_admission(self):
        a = self.source(b'1234'); b = self.source(b'5678')
        i = self.s.intent('Small scope', [a, b], max_bytes=7)
        self.assertEqual(self.s.admit(i, a, 'first')['decision'], 'allow')
        self.assertEqual(self.s.admit(i, a, 'again')['decision'], 'allow')
        self.assertEqual(self.s.admit(i, b, 'second')['code'], 'context-budget-exceeded')
        self.s.verify()

    def test_intent_escalation_rejected(self):
        with self.assertRaises(ValueError): self.s.intent('bad', [], caps=['shell.exec'])

    def test_owner_label_checked(self):
        with self.assertRaises(ValueError): self.s.intent('bad', [], actor='plugin')

    def test_missing_capability_denied(self):
        o = self.source(); i = self.s.intent('Read only', [o], caps=[])
        a = self.s.admit(i, o, 'test')
        self.assertEqual(self.s.run(i, o, a['receipt'])['code'], 'capability-not-granted')

    def test_missing_admission_denied(self):
        o = self.source(); i = self.s.intent('Count', [o])
        self.assertEqual(self.s.run(i, o, 'missing')['code'], 'valid-admission-required')

    def test_admission_cannot_cross_intents(self):
        o, i, a = self.admitted(); j = self.s.intent('Other task', [o])
        self.assertEqual(self.s.run(j, o, a)['status'], 'denied')

    def test_admission_cannot_cross_objects(self):
        o, i, a = self.admitted(); other = self.source(b'other')
        self.assertEqual(self.s.run(i, other, a)['status'], 'denied')

    def test_append_only_triggers(self):
        self.admitted()
        for table in ('manifest', 'objects', 'blobs', 'events'):
            for operation in ('DELETE FROM', 'UPDATE'):
                sql = f'{operation} {table}' + (' SET id=id' if operation == 'UPDATE' else '')
                with self.assertRaises(sqlite3.IntegrityError): self.s.db.execute(sql)
        self.s.db.rollback()

    def test_blob_corruption_detected_even_without_trigger(self):
        self.source()
        self.s.db.execute('DROP TRIGGER blobs_update')
        self.s.db.execute("UPDATE blobs SET data=x'00'")
        self.s.db.commit()
        with self.assertRaises(ValueError): self.s.verify()

    def test_event_corruption_detected(self):
        self.admitted()
        self.s.db.execute('DROP TRIGGER events_update')
        self.s.db.execute("UPDATE events SET body=x'7b7d' WHERE seq=2")
        self.s.db.commit()
        with self.assertRaises(ValueError): self.s.verify()

    def test_manifest_corruption_detected(self):
        m = self.s.manifest(); m['name'] = 'changed'
        self.s.db.execute('DROP TRIGGER manifest_update')
        self.s.db.execute('UPDATE manifest SET body=?', (canonical(m),)); self.s.db.commit()
        with self.assertRaises(ValueError): self.s.verify()

    def test_checkpoint_accepts_extension(self):
        cp = self.s.checkpoint(); self.source()
        self.assertTrue(self.s.verify(cp)['ok'])

    def test_checkpoint_detects_tail_removal(self):
        self.admitted(); cp = self.s.checkpoint()
        self.s.db.execute('DROP TRIGGER events_delete')
        self.s.db.execute('DELETE FROM events WHERE seq=(SELECT MAX(seq) FROM events)'); self.s.db.commit()
        self.assertTrue(self.s.verify()['ok'])  # No external anchor: valid shorter history.
        with self.assertRaises(ValueError): self.s.verify(cp)

    def test_checkpoint_rejects_other_project(self):
        cp = self.s.checkpoint(); cp['project_id'] = 'other'
        with self.assertRaises(ValueError): self.s.verify(cp)

    def test_import_preserves_bytes_no_authority(self):
        p = self.archive(); raw = p.read_bytes()
        result = self.s.import_plugin(p)
        self.assertEqual(self.s.content(result['bundle']), raw)
        skill = result['files']['skills/test/SKILL.md']
        self.assertEqual(self.s.object(skill)['type'], 'skill')
        self.assertEqual(self.s.object(skill)['authority'], 'none')
        self.assertFalse(any(e['kind'] == 'intent' for e in self.s.events()))
        self.s.verify()

    def test_wrapped_root_import(self):
        result = self.s.import_plugin(self.archive(prefix='idea-lab/'))
        self.assertIn('skills/test/SKILL.md', result['files'])
        self.s.verify()

    def test_binary_import_preserved(self):
        r = self.s.import_plugin(self.archive([('asset.bin', b'\xff\x00')]))
        self.assertEqual(self.s.content(r['files']['asset.bin']), b'\xff\x00')

    def test_archive_paths_rejected_atomically(self):
        for name in ('../evil', '/evil', 'C:/evil', 'a\\evil', 'a/./evil', 'a//evil'):
            cp = self.s.checkpoint()
            with self.assertRaises(ValueError): self.s.import_plugin(self.archive([(name, 'bad')]))
            self.assertEqual(self.s.checkpoint(), cp)

    def test_duplicate_archive_rejected(self):
        p = self.archive([('A.md', 'a'), ('a.md', 'b')])
        with self.assertRaises(ValueError): self.s.import_plugin(p)

    def test_symlink_archive_rejected(self):
        p = self.archive()
        with zipfile.ZipFile(p, 'a') as z:
            i = zipfile.ZipInfo('link'); i.create_system = 3
            i.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(i, 'target')
        with self.assertRaises(ValueError): self.s.import_plugin(p)

    def test_oversized_archive_member_rejected(self):
        p = self.root / 'large.plugin'
        with zipfile.ZipFile(p, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('large', b'a' * (MAX_BLOB + 1))
        with self.assertRaises(ValueError): self.s.import_plugin(p)

    def test_invalid_manifest_no_partial_import(self):
        p = self.root / 'bad.plugin'
        with zipfile.ZipFile(p, 'w') as z: z.writestr('.claude-plugin/plugin.json', '{}')
        cp = self.s.checkpoint()
        with self.assertRaises(ValueError): self.s.import_plugin(p)
        self.assertEqual(self.s.checkpoint(), cp)

    def test_canonical_profile(self):
        self.assertEqual(canonical({'b': 2, 'a': 'é'}), canonical({'a': 'é', 'b': 2}))
        for bad in (float('nan'), 1.2, 2**54, {'é': 1}):
            with self.assertRaises(ValueError): canonical(bad)
        self.assertNotEqual(digest('é'.encode()), digest('e\u0301'.encode()))

    def test_unknown_version_rejected(self):
        self.s.db.execute('PRAGMA user_version=99')
        with self.assertRaises(ValueError): Store(self.root / 'test.gpt')

    def test_cli_init_refuses_overwrite(self):
        cli = Path(__file__).resolve().parents[1] / 'gptfs.py'
        r = subprocess.run([sys.executable, str(cli), 'init', str(self.root / 'test.gpt')], capture_output=True)
        self.assertEqual(r.returncode, 2)
        self.s.verify()

    def test_cli_denial_exit_status(self):
        o = self.source(kind='skill'); i = self.s.intent('Read', [o])
        cli = Path(__file__).resolve().parents[1] / 'gptfs.py'
        r = subprocess.run([sys.executable, str(cli), 'admit', str(self.root / 'test.gpt'),
                            '--intent', i, '--object', o, '--reason', 'test'], capture_output=True)
        self.assertEqual(r.returncode, 3)
        self.assertEqual(json.loads(r.stdout)['decision'], 'deny')

    def test_forged_rehashed_admission_denied_by_replay(self):
        o = self.source(kind='skill'); i = self.s.intent('Read sources', [o])
        self.s.admit(i, o, 'test')
        seq, _, raw = self.s.db.execute('SELECT seq,id,body FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        event = json.loads(raw)
        event['data']['decision'] = 'allow'
        event['data']['code'] = 'within-explicit-scope'
        raw = canonical(event)
        self.s.db.execute('DROP TRIGGER events_update')
        self.s.db.execute('UPDATE events SET id=?,body=? WHERE seq=?',
                          (digest(b'GPTFS:event:1\0' + raw), raw, seq))
        self.s.db.commit()
        with self.assertRaisesRegex(ValueError, 'invalid admission'): self.s.verify()

    def test_operation_failure_rolls_back_evidence(self):
        o, i, a = self.admitted()
        cp = self.s.checkpoint()
        original = self.s._event
        def fail_execution(kind, data, actor):
            if kind == 'execution': raise ValueError('simulated write failure')
            return original(kind, data, actor)
        self.s._event = fail_execution
        with self.assertRaisesRegex(ValueError, 'simulated'): self.s.run(i, o, a)
        self.assertEqual(cp, self.s.checkpoint())

    def test_corrupt_store_cannot_append(self):
        self.source()
        self.s.db.execute('DROP TRIGGER blobs_update')
        self.s.db.execute("UPDATE blobs SET data=x'00'"); self.s.db.commit()
        before = self.s.db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        with self.assertRaises(ValueError): self.s.intent('Cannot hide corruption', [])
        self.assertEqual(before, self.s.db.execute('SELECT COUNT(*) FROM events').fetchone()[0])


if __name__ == '__main__':
    unittest.main()
