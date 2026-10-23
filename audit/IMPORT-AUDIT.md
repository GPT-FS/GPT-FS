# Repository and archive audit

**Inspection date: October 23, 2026.**

## Repository baseline

The connected GitHub profile identifies Drew Hester, login `DH-LStudios`, account
ID `2816895`. Its owner-affiliated repository `DH-LStudios/GPT-FS`, repository ID
`1110033635`, grants admin/push access and is private, not a fork or archived.
It was created on December 4, 2025. This is not a similarly named third-party project.

Before this work the complete repository consisted of `README.md` (two lines) and
`LICENSE` (MIT, copyright 2025 Drew Hester), in one commit:
`f17d1aa1f7893acacf2c22ed6168ec17d7cf6c39`, authored by Drew Hester.
The only branch was `main`, reported unprotected. There were no issues/PRs,
milestones, releases, or Actions runs. All existing files and history were inspected.
The new branch is `codex/founding-charter-portable-mvp`; main is not changed.

## Recovered output

The prior local output `GPTFS-v0.1.0.zip` was accessible. It is **85,891 bytes**, SHA-256
`3ca444bdf40d7d61a4db89617197bb77e41d7bece054ee97d9ea4383a43851bc`.
It contains **21 files**, now preserved byte-for-byte under `prototype/v0.1/`.
[archive-inventory.json](archive-inventory.json) records every path, length, and hash.
The original ZIP is not duplicated in Git; its exact extracted members and checksum
are retained. `tools/check_archive.py` checks all members and the pyz's embedded source.

Inspected implementation: four-table SQLite store, raw SHA-256 blobs, canonical
JSON envelopes, domain-separated object/event hashes, append-only triggers, intent
scope and byte budgets, admission/denial receipts, text.stats execution/evidence,
bounded inert Claude ZIP import, replay and checkpoint validation. The bundled
sample contains 13 objects, 13 blobs, and 20 events. Its original checkpoint verifies.

The 37-test report was reproduced locally, rather than accepted from conversation.
The pyz source matches `gptfs.py`, and its sample verification succeeds. The new
transport adds 14 tests including the real sample and extension preservation.

## Important limits

v0.1 supports a narrow type/capability set, not the whole charter. Its verifier
shares implementation with the writer. Actor labels are unauthenticated. There is
no intent revocation, expiry, independent semantic engine, or writable directory
backend. These are tracked work, not features claimed by this import.

The source sample includes original Idea Lab bytes and source license metadata.
Authorship/redistribution review remains a publication gate. Original archive
documents and reports retain their original wording as historical evidence.
