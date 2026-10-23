"""GPT File System 0.1: local, content-addressed context and receipt container.

Standard library only. See SPEC.md and SECURITY.md before integrating a runner.
"""
import argparse
import hashlib
import io
import json
import sqlite3
import stat
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = '0.1.0'
APP_ID = 0x47505446
TYPES = {'source', 'reference', 'skill', 'note', 'evidence', 'plugin-manifest', 'bundle'}
TEXT_TYPES = TYPES - {'bundle'}
CAPS = {'text.stats'}
MAX_BLOB = 8 * 1024 * 1024
MAX_ARCHIVE = 32 * 1024 * 1024
MAX_FILES = 256


def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    """Restricted JSON profile: no floats; ASCII keys; exact Unicode strings."""
    def check(v):
        if v is None or type(v) in (bool, str):
            return
        if type(v) is int:
            require(abs(v) <= 2**53 - 1, 'integer outside canonical range')
        elif type(v) is list:
            for item in v:
                check(item)
        elif type(v) is dict:
            for key, item in v.items():
                require(type(key) is str and key.isascii(), 'keys must be ASCII strings')
                check(item)
        else:
            raise ValueError('unsupported canonical JSON value')
    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(data):
    return 'sha256:' + hashlib.sha256(data).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def stats(data):
    text = data.decode('utf-8')
    return {'bytes': len(data), 'characters': len(text),
            'words': len(text.split()), 'lines': len(text.splitlines()),
            'content_digest': digest(data)}


def plugin_members(raw):
    """Bound reads before decompression; never extract or execute archive paths."""
    require(len(raw) <= MAX_BLOB, 'compressed archive too large')
    entries = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        require(len(infos) <= MAX_FILES, 'too many archive entries')
        require(sum(i.file_size for i in infos) <= MAX_ARCHIVE, 'expanded archive too large')
        seen = set()
        for i in infos:
            name = i.filename
            require(i.orig_filename == name, 'normalized archive path rejected')
            parts = name.rstrip('/').split('/')
            require(name and not name.startswith('/') and '\\' not in name and ':' not in name
                    and all(s not in ('', '.', '..') for s in parts), 'unsafe archive path')
            require(name.casefold() not in seen, 'duplicate archive path')
            seen.add(name.casefold())
            mode = i.external_attr >> 16
            require(not stat.S_ISLNK(mode), 'symlink rejected')
            require(not (i.flag_bits & 1), 'encrypted member rejected')
            require(i.file_size <= MAX_BLOB, 'archive member too large')
            if not i.is_dir():
                entries[name] = z.read(i)
    manifests = [n for n in entries if n == '.claude-plugin/plugin.json' or n.endswith('/.claude-plugin/plugin.json')]
    require(len(manifests) == 1, 'exactly one Claude manifest required')
    mn = manifests[0]
    prefix = mn[:-len('.claude-plugin/plugin.json')]
    require(all(n.startswith(prefix) for n in entries), 'files outside plugin root')
    manifest = json.loads(entries[mn])
    require(type(manifest) is dict and type(manifest.get('name')) is str and manifest['name'], 'plugin name required')
    return entries, prefix, manifest


SCHEMA = '''
CREATE TABLE manifest (id INTEGER PRIMARY KEY CHECK(id=1), body BLOB NOT NULL);
CREATE TABLE blobs (id TEXT PRIMARY KEY, data BLOB NOT NULL);
CREATE TABLE objects (id TEXT PRIMARY KEY, body BLOB NOT NULL);
CREATE TABLE events (seq INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, body BLOB NOT NULL);
'''


class Store:
    def __init__(self, path):
        self.path = Path(path).resolve()
        require(self.path.is_file(), 'container does not exist')
        self.db = sqlite3.connect(self.path.as_uri() + '?mode=rw', uri=True)
        self.db.execute('PRAGMA busy_timeout=5000')
        self.db.execute('PRAGMA trusted_schema=OFF')
        self.db.execute('PRAGMA synchronous=FULL')
        try:
            require(self.db.execute('PRAGMA application_id').fetchone()[0] == APP_ID,
                    'not a GPTFS container')
            require(self.db.execute('PRAGMA user_version').fetchone()[0] == 1,
                    'unsupported schema version')
        except Exception:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    @classmethod
    def create(cls, path, name, owner='Drew'):
        p = Path(path)
        with p.open('xb'):
            pass
        db = sqlite3.connect(p)
        try:
            db.executescript(SCHEMA)
            for table in ('manifest', 'blobs', 'objects', 'events'):
                for action in ('UPDATE', 'DELETE'):
                    db.execute(f"CREATE TRIGGER {table}_{action.lower()} BEFORE {action} ON {table} "
                               "BEGIN SELECT RAISE(ABORT, 'append-only'); END")
            db.execute(f'PRAGMA application_id={APP_ID}')
            db.execute('PRAGMA user_version=1')
            body = {'format': 'GPTFS', 'format_version': VERSION, 'schema_version': 1,
                    'project_id': str(uuid.uuid4()), 'name': name, 'owner': owner,
                    'created_at': stamp(), 'canonicalization': 'gptfs-json-1',
                    'hash': 'sha256', 'capability_ceiling': sorted(CAPS)}
            db.execute('INSERT INTO manifest VALUES (1, ?)', (canonical(body),))
            db.commit()
        finally:
            db.close()
        s = cls(p)
        with s.db:
            s._event('genesis', {'manifest': digest(canonical(body))}, owner)
        return s

    def manifest(self):
        return json.loads(self.db.execute('SELECT body FROM manifest WHERE id=1').fetchone()[0])

    def events(self):
        return [dict(json.loads(body), id=eid) for eid, body in
                self.db.execute('SELECT id, body FROM events ORDER BY seq')]

    def _event(self, kind, data, actor):
        row = self.db.execute('SELECT seq,id FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        body = {'seq': row[0] + 1 if row else 1, 'previous': row[1] if row else None,
                'kind': kind, 'actor': actor, 'at': stamp(), 'data': data}
        eid = digest(b'GPTFS:event:1\0' + canonical(body))
        self.db.execute('INSERT INTO events VALUES (?,?,?)', (body['seq'], eid, canonical(body)))
        return eid

    def _begin(self):
        self.db.execute('BEGIN IMMEDIATE')
        self.verify()

    def object(self, oid):
        row = self.db.execute('SELECT body FROM objects WHERE id=?', (oid,)).fetchone()
        require(row is not None, 'unknown object')
        return json.loads(row[0])

    def content(self, oid):
        obj = self.object(oid)
        row = self.db.execute('SELECT data FROM blobs WHERE id=?', (obj['blob'],)).fetchone()
        require(row is not None, 'missing blob')
        return row[0]

    def _put(self, data, kind, origin, actor, parents=(), media='text/plain; charset=utf-8'):
        require(kind in TYPES and len(data) <= MAX_BLOB, 'invalid type or object too large')
        require(type(origin) is str and bool(origin), 'origin required')
        for parent in parents:
            self.object(parent)
        if kind in TEXT_TYPES:
            data.decode('utf-8')
        bid = digest(data)
        obj = {'schema': 1, 'type': kind, 'blob': bid, 'media_type': media,
               'size': len(data), 'origin': origin, 'parents': sorted(set(parents)),
               'authority': 'none', 'trust': 'untrusted'}
        raw = canonical(obj)
        oid = digest(b'GPTFS:object:1\0' + raw)
        self.db.execute('INSERT OR IGNORE INTO blobs VALUES (?,?)', (bid, data))
        self.db.execute('INSERT OR IGNORE INTO objects VALUES (?,?)', (oid, raw))
        self._event('custody', {'object': oid, 'action': 'ingest', 'origin': origin}, actor)
        return oid

    def put(self, data, kind='source', origin='local', actor='Drew', parents=()):
        with self.db:
            self._begin()
            return self._put(data, kind, origin, actor, parents)

    def intent(self, text, objects, caps=('text.stats',), types=('source', 'note', 'reference'),
               max_bytes=65536, actor='Drew'):
        with self.db:
            self._begin()
            require(actor == self.manifest()['owner'], 'only local owner may declare intent')
            require(type(text) is str and bool(text.strip()), 'intent text required')
            require(set(caps) <= set(self.manifest()['capability_ceiling']), 'capability escalation')
            require(set(types) <= TEXT_TYPES, 'unsupported context type')
            require(type(max_bytes) is int and 0 <= max_bytes <= MAX_BLOB, 'invalid context budget')
            for oid in objects:
                self.object(oid)
            return self._event('intent', {'text': text, 'objects': sorted(set(objects)),
                'capabilities': sorted(set(caps)), 'types': sorted(set(types)),
                'max_bytes': max_bytes}, actor)

    def _intent(self, iid):
        event = next((e for e in self.events() if e['id'] == iid and e['kind'] == 'intent'), None)
        require(event is not None, 'unknown intent')
        return event['data']

    def _admission_reason(self, iid, oid, previous):
        intent = self._intent(iid)
        obj = self.object(oid)
        if oid not in intent['objects']:
            return 'object-outside-intent'
        if obj['type'] not in intent['types']:
            return 'type-not-allowed'
        admitted = {e['data']['object'] for e in previous if e['kind'] == 'admission'
                    and e['data']['intent'] == iid and e['data']['decision'] == 'allow'}
        admitted.add(oid)
        if sum(self.object(x)['size'] for x in admitted) > intent['max_bytes']:
            return 'context-budget-exceeded'
        return 'within-explicit-scope'

    def admit(self, iid, oid, reason, actor='Drew'):
        with self.db:
            self._begin()
            require(bool(reason.strip()), 'admission rationale required')
            code = self._admission_reason(iid, oid, self.events())
            data = {'intent': iid, 'object': oid, 'rationale': reason, 'code': code,
                    'decision': 'allow' if code == 'within-explicit-scope' else 'deny',
                    'role': 'data', 'granted_authority': []}
            eid = self._event('admission', data, actor)
            return dict(data, receipt=eid)

    def _run_reason(self, iid, oid, admission, capability, previous):
        intent = self._intent(iid)
        if capability not in CAPS or capability not in intent['capabilities']:
            return 'capability-not-granted'
        match = next((e for e in previous if e['id'] == admission and e['kind'] == 'admission'), None)
        if not match or match['data']['intent'] != iid or match['data']['object'] != oid or match['data']['decision'] != 'allow':
            return 'valid-admission-required'
        return 'authorized'

    def run(self, iid, oid, admission, capability='text.stats', actor='runner:local'):
        with self.db:
            self._begin()
            code = self._run_reason(iid, oid, admission, capability, self.events())
            data = {'intent': iid, 'object': oid, 'admission': admission,
                    'capability': capability, 'code': code, 'evidence': None,
                    'status': 'completed' if code == 'authorized' else 'denied',
                    'runner': 'gptfs-text-stats/0.1.0'}
            if code == 'authorized':
                result = canonical(stats(self.content(oid)))
                data['evidence'] = self._put(result, 'evidence', 'runner:text.stats', actor, [oid], 'application/json')
            eid = self._event('execution', data, actor)
            return dict(data, receipt=eid)

    def import_plugin(self, path, actor='Drew'):
        p = Path(path)
        require(p.stat().st_size <= MAX_BLOB, 'compressed archive too large')
        raw = p.read_bytes()
        entries, prefix, manifest = plugin_members(raw)
        with self.db:
            self._begin()
            bundle = self._put(raw, 'bundle', 'claude-plugin:sha256:' + hashlib.sha256(raw).hexdigest(), actor, media='application/zip')
            mapping = {}
            for name, data in sorted(entries.items()):
                rel = name[len(prefix):]
                kind = ('plugin-manifest' if rel == '.claude-plugin/plugin.json' else
                        'skill' if rel.startswith('skills/') and rel.endswith('/SKILL.md') else 'reference')
                try:
                    data.decode('utf-8')
                except UnicodeDecodeError:
                    kind = 'bundle'
                mapping[rel] = self._put(data, kind, 'claude-plugin:/' + rel, actor, [bundle],
                                          'application/octet-stream' if kind == 'bundle' else 'text/plain; charset=utf-8')
            receipt = self._event('import', {'adapter': 'claude-plugin/0.1', 'bundle': bundle,
                'files': mapping, 'plugin_name': manifest['name'], 'authority_granted': []}, actor)
            return {'bundle': bundle, 'files': mapping, 'receipt': receipt}

    def verify(self, checkpoint=None):
        require(self.db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'SQLite integrity failure')
        m = self.manifest()
        require(m['format'] == 'GPTFS' and m['format_version'] == VERSION and m['schema_version'] == 1,
                'unsupported manifest version')
        require(m['capability_ceiling'] == sorted(CAPS), 'unsupported capability ceiling')
        require(m['hash'] == 'sha256' and m['canonicalization'] == 'gptfs-json-1', 'unsupported identity profile')
        require(self.db.execute('SELECT body FROM manifest').fetchone()[0] == canonical(m), 'noncanonical manifest')
        blobs = {}
        for bid, data in self.db.execute('SELECT id,data FROM blobs'):
            require(digest(data) == bid and len(data) <= MAX_BLOB, 'blob hash/size mismatch')
            blobs[bid] = data
        objects = {}
        for oid, raw in self.db.execute('SELECT id,body FROM objects'):
            o = json.loads(raw)
            require(raw == canonical(o) and oid == digest(b'GPTFS:object:1\0' + raw), 'object hash mismatch')
            require(o['schema'] == 1 and o['type'] in TYPES and o['authority'] == 'none' and o['trust'] == 'untrusted', 'invalid object semantics')
            require(o['blob'] in blobs and len(blobs[o['blob']]) == o['size'], 'missing/wrong blob')
            if o['type'] in TEXT_TYPES:
                blobs[o['blob']].decode('utf-8')
            objects[oid] = o
        previous = []
        seen_objects = set()
        for seq, eid, raw in self.db.execute('SELECT seq,id,body FROM events ORDER BY seq'):
            e = json.loads(raw)
            require(raw == canonical(e) and digest(b'GPTFS:event:1\0' + raw) == eid, 'event hash mismatch')
            require(seq == len(previous) + 1 == e['seq'] and e['previous'] == (previous[-1]['id'] if previous else None), 'broken event chain')
            d, kind = e['data'], e['kind']
            if not previous:
                require(kind == 'genesis' and d == {'manifest': digest(canonical(m))}, 'invalid genesis')
            elif kind == 'custody':
                require(d['object'] in objects and d['action'] == 'ingest', 'invalid custody')
                o = objects[d['object']]
                require(d['origin'] == o['origin'] and set(o['parents']) <= seen_objects, 'broken lineage')
                seen_objects.add(d['object'])
            elif kind == 'intent':
                require(e['actor'] == m['owner'] and bool(d['text'].strip()), 'invalid intent owner/text')
                require(set(d['objects']) <= seen_objects and set(d['capabilities']) <= CAPS and set(d['types']) <= TEXT_TYPES,
                        'invalid intent scope')
                require(type(d['max_bytes']) is int and 0 <= d['max_bytes'] <= MAX_BLOB, 'invalid budget')
            elif kind in ('admission', 'execution'):
                require(any(p['id'] == d['intent'] and p['kind'] == 'intent' for p in previous), 'intent not earlier')
                if kind == 'admission':
                    require(d['object'] in seen_objects, 'object not yet in custody')
                    code = self._admission_reason(d['intent'], d['object'], previous)
                    require(d['code'] == code and d['decision'] == ('allow' if code == 'within-explicit-scope' else 'deny')
                            and d['role'] == 'data' and d['granted_authority'] == [] and bool(d['rationale'].strip()), 'invalid admission')
                else:
                    code = self._run_reason(d['intent'], d['object'], d['admission'], d['capability'], previous)
                    require(d['code'] == code and d['status'] == ('completed' if code == 'authorized' else 'denied'), 'invalid execution')
                    require(d['runner'] == 'gptfs-text-stats/0.1.0', 'unknown runner')
                    if code == 'authorized':
                        require(d['evidence'] in seen_objects and objects[d['evidence']]['type'] == 'evidence'
                                and objects[d['evidence']]['parents'] == [d['object']], 'invalid evidence lineage')
                        require(self.content(d['evidence']) == canonical(stats(self.content(d['object']))), 'evidence mismatch')
                    else:
                        require(d['evidence'] is None, 'denied event has evidence')
            elif kind == 'import':
                require(d['bundle'] in seen_objects and objects[d['bundle']]['type'] == 'bundle'
                        and d['authority_granted'] == [] and d['adapter'] == 'claude-plugin/0.1', 'invalid import')
                require(set(d['files'].values()) <= seen_objects, 'missing imported object')
                for oid in d['files'].values():
                    require(objects[oid]['parents'] == [d['bundle']], 'import lineage mismatch')
                members, prefix, plugin = plugin_members(self.content(d['bundle']))
                require({n[len(prefix):] for n in members} == set(d['files']), 'incomplete import map')
                require(plugin['name'] == d['plugin_name'], 'plugin name mismatch')
                for rel, oid in d['files'].items():
                    require(members[prefix + rel] == self.content(oid), 'import bytes mismatch')
            else:
                raise ValueError('unknown event kind')
            previous.append(dict(e, id=eid))
        require(previous and seen_objects == set(objects), 'unlogged objects or empty ledger')
        require({o['blob'] for o in objects.values()} == set(blobs), 'orphan blobs')
        if checkpoint:
            require(checkpoint['project_id'] == m['project_id'] and checkpoint['manifest'] == digest(canonical(m)), 'checkpoint project mismatch')
            n = checkpoint['seq']
            require(type(n) is int and 1 <= n <= len(previous) and previous[n-1]['id'] == checkpoint['head'], 'checkpoint history mismatch')
        return {'ok': True, 'objects': len(objects), 'blobs': len(blobs), 'events': len(previous),
                'head': previous[-1]['id'], 'project_id': m['project_id']}

    def checkpoint(self):
        v = self.verify()
        return {'project_id': v['project_id'], 'manifest': digest(canonical(self.manifest())),
                'seq': v['events'], 'head': v['head']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version', action='version', version=VERSION)
    sub = p.add_subparsers(dest='command', required=True)
    for command in ('init', 'add', 'intent', 'admit', 'run', 'import-plugin', 'inspect', 'verify', 'checkpoint'):
        a = sub.add_parser(command)
        a.add_argument('container')
        if command == 'init':
            a.add_argument('--name', default='Untitled'); a.add_argument('--owner', default='Drew')
        elif command == 'add':
            a.add_argument('file'); a.add_argument('--type', choices=sorted(TYPES), default='source')
            a.add_argument('--origin', required=True); a.add_argument('--parent', action='append', default=[])
        elif command == 'intent':
            a.add_argument('--text', required=True); a.add_argument('--object', action='append', default=[])
            a.add_argument('--capability', action='append', default=[])
            a.add_argument('--type', action='append', choices=sorted(TEXT_TYPES), default=[])
            a.add_argument('--max-bytes', type=int, default=65536)
        elif command in ('admit', 'run'):
            a.add_argument('--intent', required=True); a.add_argument('--object', required=True)
            if command == 'admit':
                a.add_argument('--reason', required=True)
            else:
                a.add_argument('--admission', required=True); a.add_argument('--capability', default='text.stats')
        elif command == 'import-plugin':
            a.add_argument('file')
        elif command == 'verify':
            a.add_argument('--checkpoint')
        if command not in ('init', 'inspect', 'verify', 'checkpoint', 'run'):
            a.add_argument('--actor', default='Drew')
    args = p.parse_args()
    s = None
    try:
        if args.command == 'init':
            s = Store.create(args.container, args.name, args.owner); result = s.verify()
        else:
            s = Store(args.container)
            c = args.command
            if c == 'add':
                require(Path(args.file).stat().st_size <= MAX_BLOB, 'file too large')
                result = {'object': s.put(Path(args.file).read_bytes(), args.type, args.origin, args.actor, args.parent)}
            elif c == 'intent':
                result = {'intent': s.intent(args.text, args.object, args.capability, args.type, args.max_bytes, args.actor)}
            elif c == 'admit': result = s.admit(args.intent, args.object, args.reason, args.actor)
            elif c == 'run': result = s.run(args.intent, args.object, args.admission, args.capability)
            elif c == 'import-plugin': result = s.import_plugin(args.file, args.actor)
            elif c == 'inspect':
                s.verify()
                result = {'manifest': s.manifest(), 'objects': [dict(s.object(r[0]), id=r[0]) for r in s.db.execute('SELECT id FROM objects ORDER BY id')], 'events': s.events()}
            elif c == 'checkpoint': result = s.checkpoint()
            else: result = s.verify(json.loads(Path(args.checkpoint).read_text(encoding='utf-8-sig')) if args.checkpoint else None)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 3 if isinstance(result, dict) and (result.get('decision') == 'deny' or result.get('status') == 'denied') else 0
    except (ValueError, KeyError, TypeError, OSError, RuntimeError, NotImplementedError,
            sqlite3.Error, zipfile.BadZipFile) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        return 2
    finally:
        if s: s.close()


if __name__ == '__main__':
    sys.exit(main())
