# GPT File System v0.1

**A runnable local proof of concept for context with provenance, explicit intent, bounded authority, and replayable receipts.** Built for Drew, October 23, 2026. Independent experimental format; no affiliation with OpenAI or Anthropic and no claim that these underlying techniques are novel.

The `.gpt` file is a SQLite database with content-addressed blobs, typed immutable object envelopes, and a hash-linked event ledger. It is a logical object file system, not a mounted operating-system filesystem. The download ZIP is only the delivery package; the `.gpt` format itself is not ZIP.

## Run in two minutes

Requires Python 3.10 or newer, with no third-party packages, API keys, network calls, or installation step. Validated on Windows with Python 3.14.2; other platforms/versions are intended but not validated in this release. Extract the release ZIP, open a terminal in the extracted `gptfs-v0.1` folder, and run:

```powershell
python gptfs.py verify sample/research.gpt --checkpoint sample/checkpoint.json
python demo.py my-experiment
python -m unittest discover -s tests -v
```

`my-experiment` must be a new directory. The demo writes a fresh `.gpt`, a readable report, a ledger export, and an external checkpoint. The included sample already imports Drew's actual Idea Lab bundle. To repeat with another bundle:

```powershell
python demo.py another-experiment --plugin "C:/path/to/idea-lab.plugin"
```

The release also provides `gptfs.pyz`, a single-file Python executable with the same CLI:

```powershell
python gptfs.pyz --help
python gptfs.pyz verify sample/research.gpt
```

This is executable Python software, not a standalone Windows `.exe`. `gptfs.cmd` is a Windows convenience launcher; Python must be available as `python`.

## What the demo proves

1. Store an original observation, a derived note with a parent reference, and hostile skill text.
2. Record a new owner-declared intent with exact object IDs, permitted types, a byte budget, and the `text.stats` capability.
3. Admit the source as data and issue an admission receipt. Reject the skill because its type is outside this intent's allowed types.
4. Run the deterministic text-statistics capability using the accepted receipt. Store the result as an evidence object linked to its input.
5. Reject a `shell.exec` request and retain its denied execution receipt.
6. Optionally import a Claude plugin as inert context, preserve its exact ZIP bytes, and map its files to child objects.
7. Recompute hashes, lineage, policy decisions, and text-statistics results; validate the history against a checkpoint.

The hostile text is a boundary fixture, not a model prompt-injection evaluation. No language model is called.

## Implemented and intentionally narrow

| Area | Implemented in v0.1 | Not implemented |
|---|---|---|
| Canonical storage | SHA-256 raw blobs; canonical JSON envelopes; deduplication | Distributed storage, encryption, chunking |
| Manifest/versioning | GPTFS 0.1.0, SQLite schema 1, project UUID, fail-closed version check | Migration tooling, schema negotiation |
| Typed objects | source, reference, skill, note, evidence, plugin-manifest, bundle | Rich semantic schemas for each domain |
| Provenance/custody | Original bytes, origin labels, parent IDs, actor/time ingest events | Authenticated identity or independent custody witnesses |
| Intent ledger | Append-only owner-labelled intent records, no edit/delete API | Cryptographic user approval, revocation, expiry |
| Authority | Exact object scope, allowed types, total distinct context-byte budget, capability ceiling | OS sandbox, network tool policy, general policy language |
| Admission | Allow/deny receipts tied to intent and object; data role only | Actual model-context assembly/token counting |
| Execution/evidence | Guarded local `text.stats`, denied receipts, result objects, deterministic replay | Arbitrary commands, model calls, external effects |
| Claude compatibility | Inert ZIP import, root or wrapped-root layout, exact file mapping | Claude runtime emulation, hooks, MCP launch, plugin export |
| Integrity | SQLite transactions, append-only triggers, hashes, replay, checkpoint ancestry | Signatures, trusted timestamps, remote transparency log |

## A manual CLI session

The CLI emits JSON; PowerShell can capture returned IDs:

```powershell
python gptfs.py init my-project.gpt --name "Drew's project"
$obj = python gptfs.py add my-project.gpt examples/observation.txt --origin "local:observation" | ConvertFrom-Json
$intent = python gptfs.py intent my-project.gpt --text "Measure this source" --object $obj.object --capability text.stats --type source | ConvertFrom-Json
$admit = python gptfs.py admit my-project.gpt --intent $intent.intent --object $obj.object --reason "Original source required" | ConvertFrom-Json
python gptfs.py run my-project.gpt --intent $intent.intent --object $obj.object --admission $admit.receipt
python gptfs.py inspect my-project.gpt
python gptfs.py checkpoint my-project.gpt > my-project.checkpoint.json
python gptfs.py verify my-project.gpt --checkpoint my-project.checkpoint.json
```

For CLI `intent`, omitted `--capability` and `--type` mean **empty grants**, deliberately. The Python demo API supplies explicit default lists documented in the source. `--actor` is a local label, not authentication. Preserve the checkpoint somewhere outside the container's writer's control for meaningful historical anchoring.

Exit codes: `0` success; `2` malformed input, storage or verification error; `3` a recorded policy denial. Policy denials commit their receipts. Validation errors roll back without a receipt. Existing output containers are never overwritten by `init`.

## Read next

- `SPEC.md`: format, fields, identity rules, transitions, compatibility.
- `COMPARISON.md`: actual uploaded archive and screenshot, with evidence boundaries.
- `SECURITY.md`: threat model and limits of every guarantee.
- `ROADMAP.md`: lean next steps with acceptance criteria.
- `TEST-RESULTS.md`, `evidence/test-results.txt`: validation and environment.
- `sample/report.json`, `sample/ledger.json`: the completed experiment.
- `evidence/archive-inventory.json`: source archive and per-member hashes.

The source bundle contains the imported Idea Lab material inside the sample container. Its manifest declares MIT; that declaration is preserved as source metadata, not an independently verified ownership claim. The prototype's own source is licensed under `LICENSE`.
