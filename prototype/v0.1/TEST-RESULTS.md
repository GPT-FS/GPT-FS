# Validation results — GPTFS v0.1.0

Validated October 23, 2026 on Windows with Python 3.14.2 and SQLite 3.50.4.

**37 automated tests passed**, run from a freshly extracted release package. Full output: `evidence/test-results.txt`.

Tests cover object deduplication, origin-sensitive identity, parent lineage, scope/type/aggregate-budget denial, capability escalation, missing admission, cross-intent and cross-object receipt reuse, owner-label checks, append-only triggers, blob/manifest/event corruption, rehashed false admission detection, transactional rollback, refusal to append to corrupt stores, checkpoint extension and truncation, root/wrapped plugin layouts, byte preservation, binary members, traversal and normalized paths, duplicate names, symlinks, oversized members, invalid manifests, canonicalization, unsupported versions, overwrite refusal and CLI denial exit codes.

Package checks passed:

- Delivery ZIP CRC check and fresh extraction.
- Single-file Python executable version and sample verification.
- Included 13-object / 20-event sample verifies against its checkpoint.
- Fresh end-to-end demo imports Drew's actual uploaded Idea Lab bundle.
- Fresh demo verifies and its manifest, objects and event ledger can be inspected through the packaged executable.
- Source archive and all member hashes recorded in `evidence/archive-inventory.json`.
- Windows `gptfs.cmd --version` succeeded. The README's PowerShell ID-capture workflow completed init, add, intent, admit, run, checkpoint export and checkpoint verification in the extracted package.

The sample measurement produced 72 bytes, 72 characters, 11 whitespace-separated words and 1 line. Skill admission was denied by type policy; shell execution was denied by capability policy. The plugin import preserved all 8 files and its original ZIP.

Two issues caught during development were fixed before this pass: a connection left open during unsupported-version rejection on Windows, and ZIP path normalization that could hide an original backslash path. The final importer compares original and normalized member names and rejects changes.

Not validated: other operating systems/Python versions, language-model behavior, external execution, OS sandboxing, signatures, multi-process stress, hostile SQLite parser resilience, forced power loss, production security, or semantic truth of provenance claims. The test suite intentionally shows that tail removal can pass without a trusted checkpoint.

Machine-readable environment and smoke-check outputs: `evidence/release-validation.json`.
