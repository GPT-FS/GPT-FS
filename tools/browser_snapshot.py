"""Export a bounded GPTFS snapshot for the browser inspector; never grant authority."""
import argparse
import base64
import json
from pathlib import Path

from portable import PROFILE, snapshot, read_directory, validate


def browser_snapshot(source, checkpoint=None):
    rows = read_directory(source) if Path(source).is_dir() else snapshot(source)
    validate(rows, checkpoint)
    tables = {}
    for name, records in rows.items():
        tables[name] = [{'keys': list(row[:-1]),
                         'body': base64.b64encode(row[-1]).decode('ascii')}
                        for row in records]
    return {'profile': 'gptfs-browser-snapshot-1', 'source_profile': PROFILE,
            'tables': tables, 'checkpoint': checkpoint}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('destination')
    parser.add_argument('--checkpoint')
    args = parser.parse_args()
    cp = json.loads(Path(args.checkpoint).read_text(encoding='utf-8-sig')) if args.checkpoint else None
    data = browser_snapshot(args.source, cp)
    with Path(args.destination).open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=True, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
