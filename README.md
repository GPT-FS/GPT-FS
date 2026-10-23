# GPT File System

**HYBRID · FLEXIBLE · AGNOSTIC · ALL-INCLUSIVE**

The canonical project home for **Drew Hester / Labyrinth Studios' GPT File System
initiative** is [GPT-FS/GPT-FS](https://github.com/GPT-FS/GPT-FS).
The [founding charter](CHARTER.md) is dated **October 23, 2026**, building on the
repository created in 2025.

**.GPT is a proposed portable logical specification. GPTFS is a reference implementation.**
SQLite is one storage binding, not a requirement for every implementation. The aim is
to carry original content, relationships, provenance, and inspectable authority
records across tools without turning imported text into permission.

[![Conformance](https://github.com/GPT-FS/GPT-FS/actions/workflows/ci.yml/badge.svg)](https://github.com/GPT-FS/GPT-FS/actions/workflows/ci.yml)

**[Try the live inspector](https://gpt-fs.github.io/GPT-FS/) · [First contributions](https://github.com/GPT-FS/GPT-FS/issues?q=is%3Aopen+label%3A%22good+first+issue%22) · [Discussions](https://github.com/GPT-FS/GPT-FS/discussions)**

The browser demo uses synthetic source material and computes integrity checks locally.
Open your own exported snapshot to inspect its content, relationships, and receipts.
The inspector evaluates integrity, not permission to execute. [Quickstart and demo guide](docs/DEMO.md).

## Where the project stands

This is a **working prototype and draft specification**, not a published standard.
The real GPTFS v0.1.0 archive has been recovered, hashed, imported unchanged, and
tested. It provides a Python CLI/zipapp, SQLite object store, SHA-256 identities,
intent ledger, inert Claude `.plugin` import, admission/execution receipts, and
deterministic verification. All 37 original tests pass locally.

The project includes a working **SQLite ↔ directory snapshot transport**, independent integrity readers in Python and the browser, and interoperability tests. Unknown fields inside stored
record bodies are preserved. Unknown required manifest extensions block policy
approval. Unsupported SQL schema additions and unindexed files are rejected rather
than dropped. Full independent policy validation, revocation, and a writable
directory backend remain explicit next milestones.

## Run it

Python 3.10+; standard library only. No API keys or network calls are required.
From the repository root:

```sh
python prototype/v0.1/gptfs.pyz verify prototype/v0.1/sample/research.gpt --checkpoint prototype/v0.1/sample/checkpoint.json
python tools/build_demo.py
python tools/portable.py verify website/data/demo.gpt --checkpoint website/data/demo.checkpoint.json --policy
python tools/portable.py export prototype/v0.1/sample/research.gpt my-directory
python tools/portable.py verify my-directory --checkpoint prototype/v0.1/sample/checkpoint.json --policy
python tools/portable.py import my-directory restored.gpt
python tools/portable.py verify restored.gpt --checkpoint prototype/v0.1/sample/checkpoint.json --policy
```

Use new destinations. Conversion preserves logical records, not SQLite page layout.
It grants no authority. `verify` reports integrity separately from `--policy`, which
reuses the prototype's policy verifier. This is a Python executable, not a standalone
Windows `.exe`, a mounted filesystem, or a general agent runner.

## Project map

| Path | Purpose |
|---|---|
| [CHARTER.md](CHARTER.md) | Founding principles and stewardship |
| [SPEC.md](SPEC.md) | Storage-neutral draft and experimental transport profile |
| [ARCHITECTURE.md](ARCHITECTURE.md), [DECISIONS.md](DECISIONS.md) | Boundaries and ADRs |
| [SECURITY.md](SECURITY.md), [COMPATIBILITY.md](COMPATIBILITY.md) | Guarantees, limits, compatibility evidence |
| [ROADMAP.md](ROADMAP.md), [CONTRIBUTING.md](CONTRIBUTING.md) | Ordered delivery and review workflow |
| [LICENSING.md](LICENSING.md), [NAMING.md](NAMING.md) | Preserved MIT notices and publication research |
| [prototype/v0.1](prototype/v0.1) | Every original release member: source, pyz, sample, tests |
| [tools](tools), [tests](tests), [examples](examples) | Transport, new tests, runnable examples |
| [audit/IMPORT-AUDIT.md](audit/IMPORT-AUDIT.md) | Repository baseline and archive evidence |

See [CONTRIBUTING.md](CONTRIBUTING.md) for test commands. CI runs both suites on
Windows and Ubuntu with Python 3.10 and 3.14; consult the actual runs for results.

## Authority and publication

An imported document can provide information; it cannot grant itself permission.
Owner labels in v0.1 are not authenticated grants. There is no revocation or expiry
yet, and a hash chain needs an independently retained checkpoint to detect rollback.

The existing [MIT license](LICENSE) and recovered source notices are preserved.
Names remain provisional pending publication review. This project is independent
of OpenAI and Anthropic; no affiliation, endorsement, or novelty claim is implied.
The repository is public under the GPT-FS organization. Changes are reviewed through pull requests.

## Public launch work

See [docs/LAUNCH.md](docs/LAUNCH.md) for the launch checklist, concrete contribution paths, and release-candidate scope.
The current candidate adds a static browser inspector and synthetic fixtures; core revocation and independent full policy validation remain open.
