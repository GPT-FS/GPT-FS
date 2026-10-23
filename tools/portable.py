"""Experimental lossless transport for GPTFS 0.1; never executes imported text."""
import argparse
import hashlib
import importlib.util
import json
import sqlite3
import tempfile
from pathlib import Path

PROFILE = 'gptfs-0.1-directory-1'
LIMIT = 64 * 1024 * 1024
TABLES = {'manifest': ('id', 'body'), 'blobs': ('id', 'data'),
          'objects': ('id', 'body'), 'events': ('seq', 'id', 'body')}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique)


def snapshot(path):
    """Read a consistent SQLite snapshot; never copy or run supplied SQL."""
    path = Path(path).resolve()
    require(path.is_file() and path.stat().st_size <= LIMIT, 'missing/oversized database')
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    try:
        db.execute('PRAGMA trusted_schema=OFF')
        db.execute('BEGIN')
        require(db.execute('PRAGMA application_id').fetchone()[0] == 0x47505446,
                'unknown application')
        require(db.execute('PRAGMA user_version').fetchone()[0] == 1, 'unknown schema')
        require(db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok', 'SQLite corruption')
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        require(tables == set(TABLES), 'unsupported tables: refusing lossy conversion')
        rows = {}
        for table, columns in TABLES.items():
            require(tuple(r[1] for r in db.execute(f'PRAGMA table_info({table})')) == columns,
                    'unsupported columns: refusing lossy conversion')
            rows[table] = db.execute(f'SELECT * FROM {table} ORDER BY {columns[0]}').fetchall()
        validate(rows)
        return rows
    finally:
        db.close()


def validate(rows, checkpoint=None):
    """Independent byte/hash/graph validator. Policy replay is a separate layer."""
    require(set(rows) == set(TABLES), 'invalid table set')
    require(len(rows['manifest']) == 1 and rows['manifest'][0][0] == 1, 'invalid manifest')
    manifest_raw = rows['manifest'][0][1]
    m = parse(manifest_raw)
    require(m['format'] == 'GPTFS' and m['format_version'] == '0.1.0'
            and m['schema_version'] == 1, 'unsupported format')
    require(m['hash'] == 'sha256' and m['canonicalization'] == 'gptfs-json-1', 'unknown identity')
    blobs, objects = {}, {}
    for bid, raw in rows['blobs']:
        require(bid not in blobs and digest(raw) == bid, 'blob hash/duplicate mismatch')
        blobs[bid] = raw
    for oid, raw in rows['objects']:
        require(oid not in objects and digest(b'GPTFS:object:1\0' + raw) == oid, 'object hash/duplicate mismatch')
        o = parse(raw)
        require(o['blob'] in blobs and o['size'] == len(blobs[o['blob']]), 'missing/wrong blob')
        objects[oid] = o
    for o in objects.values():
        require(set(o['parents']) <= set(objects), 'missing relationship target')
    previous, ids = None, []
    for expected, (seq, eid, raw) in enumerate(rows['events'], 1):
        e = parse(raw)
        require(seq == expected == e['seq'] and e['previous'] == previous, 'broken ledger')
        require(digest(b'GPTFS:event:1\0' + raw) == eid, 'event hash mismatch')
        if expected == 1:
            require(e['kind'] == 'genesis' and e['data'] == {'manifest': digest(manifest_raw)}, 'invalid genesis')
        ids.append(eid)
        previous = eid
    require(ids, 'empty ledger')
    if checkpoint is not None:
        n = checkpoint['seq']
        require(checkpoint['project_id'] == m['project_id'] and checkpoint['manifest'] == digest(manifest_raw), 'checkpoint project mismatch')
        require(type(n) is int and 1 <= n <= len(ids) and ids[n-1] == checkpoint['head'], 'checkpoint history mismatch')
    return {'integrity': 'valid', 'policy': 'not-evaluated', 'events': len(ids), 'head': previous}


def write_db(rows, path):
    """Only the known schema is generated; arbitrary imported SQL is never executed."""
    with Path(path).open('xb'):
        pass
    db = sqlite3.connect(path)
    try:
        db.executescript('''
        CREATE TABLE manifest(id INTEGER PRIMARY KEY CHECK(id=1), body BLOB NOT NULL);
        CREATE TABLE blobs(id TEXT PRIMARY KEY, data BLOB NOT NULL);
        CREATE TABLE objects(id TEXT PRIMARY KEY, body BLOB NOT NULL);
        CREATE TABLE events(seq INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, body BLOB NOT NULL);
        PRAGMA application_id=1196446790;
        PRAGMA user_version=1;
        ''')
        for table, columns in TABLES.items():
            db.executemany(f'INSERT INTO {table} VALUES ({",".join("?" for _ in columns)})', rows[table])
            for action in ('UPDATE', 'DELETE'):
                db.execute(f"CREATE TRIGGER {table}_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'append-only'); END")
        db.commit()
    finally:
        db.close()


def replay(rows, checkpoint=None):
    """Reuse v0.1 policy replay; this is explicitly NOT an independent policy engine."""
    spec = importlib.util.spec_from_file_location('prototype_gptfs', Path(__file__).resolve().parents[1] / 'prototype/v0.1/gptfs.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Unknown required extensions may carry policy; preserve them but never approve them.
    m = parse(rows['manifest'][0][1])
    require(not m.get('required_extensions'), 'unsupported required extension: policy blocked')
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'verify.gpt'
        write_db(rows, path)
        store = module.Store(path)
        try:
            return store.verify(checkpoint)
        finally:
            store.close()


def export_directory(source, destination):
    rows = snapshot(source)
    dest = Path(destination)
    require(not dest.exists(), 'destination exists')
    dest.mkdir()
    index = {'profile': PROFILE, 'tables': {}}
    for table, values in rows.items():
        (dest / table).mkdir()
        index['tables'][table] = []
        for n, row in enumerate(values):
            raw = row[-1]
            name = f'{table}/{n:08d}.bin'
            (dest / name).write_bytes(raw)
            index['tables'][table].append({'keys': list(row[:-1]), 'file': name, 'sha256': digest(raw)})
    (dest / 'index.json').write_text(json.dumps(index, indent=2) + '\n', encoding='utf-8')


def read_directory(source):
    root = Path(source)
    require(root.is_dir() and not root.is_symlink(), 'directory required')
    files = list(root.rglob('*'))
    require(len(files) <= 100000 and all(not p.is_symlink() for p in files), 'links/too many files')
    require(sum(p.stat().st_size for p in files if p.is_file()) <= LIMIT, 'directory too large')
    index = parse((root / 'index.json').read_bytes())
    require(set(index) == {'profile', 'tables'} and index['profile'] == PROFILE, 'unknown transport profile')
    require(set(index['tables']) == set(TABLES), 'unknown tables')
    rows, expected = {}, {'index.json'}
    for table, entries in index['tables'].items():
        rows[table] = []
        for n, entry in enumerate(entries):
            name = f'{table}/{n:08d}.bin'
            require(set(entry) == {'keys', 'file', 'sha256'} and entry['file'] == name, 'unsafe/noncanonical path')
            require(len(entry['keys']) == len(TABLES[table])-1, 'invalid row keys')
            raw = (root / name).read_bytes()
            require(digest(raw) == entry['sha256'], 'transport hash mismatch')
            rows[table].append(tuple(entry['keys']) + (raw,))
            expected.add(name)
    require({p.relative_to(root).as_posix() for p in files if p.is_file()} == expected, 'unindexed files: refusing data loss')
    validate(rows)
    return rows


def import_directory(source, destination):
    rows = read_directory(source)
    require(not Path(destination).exists(), 'destination exists')
    write_db(rows, destination)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['export', 'import', 'verify'])
    p.add_argument('source')
    p.add_argument('destination', nargs='?')
    p.add_argument('--checkpoint')
    p.add_argument('--policy', action='store_true')
    args = p.parse_args()
    try:
        if args.command == 'verify':
            rows = read_directory(args.source) if Path(args.source).is_dir() else snapshot(args.source)
            cp = parse(Path(args.checkpoint).read_bytes()) if args.checkpoint else None
            result = validate(rows, cp)
            if args.policy:
                replay(rows, cp)
                result['policy'] = 'valid-under-prototype-0.1'
            print(json.dumps(result))
        else:
            require(args.destination, 'destination required')
            (export_directory if args.command == 'export' else import_directory)(args.source, args.destination)
            print(json.dumps({'converted': True, 'policy': 'not-evaluated'}))
        return 0
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error) as exc:
        print(json.dumps({'error': str(exc)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
