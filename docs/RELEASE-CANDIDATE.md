# Public demo kit 0.1.1-rc.1 — draft release notes

The public demo kit packages the preserved GPTFS 0.1 engine with experimental
SQLite/directory transport, a browser inspector, and synthetic examples. It gives
people an executable way to inspect original content, provenance, relationships,
and recorded admission/execution decisions.

## Added

- An independent browser integrity reader and local-file snapshot viewer.
- A synthetic notebook and synthetic MIT plugin, with no recovered third-party sample.
- A byte-change experiment, relationship navigation, receipt history, and local downloads.
- A browser-snapshot exporter for the existing supported SQLite/directory profile.
- A reproducible runtime ZIP, file manifest, and SHA-256 checksum.

## Compatibility

The engine remains GPTFS 0.1.0, SQLite schema 1. This packaging version does not
change the identity or policy profile. The directory is snapshot transport.
The browser accepts `gptfs-browser-snapshot-1` JSON; it does not open raw SQLite files.
Python 3.10+ is required for CLI tools; no third-party Python dependencies are needed.

## Limits

Browser verification checks integrity, not policy authorization. The optional Python
policy replay uses the original verifier. Revocation, expiry, authenticated grants,
independent full semantic validation, and a writable directory backend remain open.

Names remain provisional. The kit avoids the recovered Idea Lab sample, but broader
project naming and source-rights work in issue #6 still needs a recorded decision.
This release stays draft and prerelease until the owner reviews it.

## Build

```sh
python tools/build_demo.py
python tools/build_launch_release.py --output build/release
```

Archive timestamps and ordering are fixed. `SHA256SUMS.txt` verifies the archive;
`MANIFEST.json` verifies its contents. A second build from the same inputs must
produce the same archive hash. The repository carries the complete conformance suite;
the runtime ZIP is deliberately narrower and includes START-HERE.md instructions.
