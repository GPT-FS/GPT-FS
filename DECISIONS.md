# Architecture decision records

All entries dated **2026-10-23**. Accepted direction reflects the founding instruction;
experimental implementation decisions remain subject to draft PR review.

## ADR-001 — Separate specification and implementation (accepted direction)

Context: the original prototype defines a SQLite file, while the founding principles
require storage neutrality. Decision: `.GPT` names the logical specification and GPTFS
names a reference implementation. Consequence: SQLite schema 1 is a compatibility
profile, not the universal .GPT format. Other bindings need explicit mappings and tests.

## ADR-002 — Preserve the recovered prototype (proposed implementation)

Decision: import every archive member unchanged under `prototype/v0.1/`, record
per-file hashes, and keep original licensing notices. Root guidance supersedes only
project direction, not historical evidence. Consequence: some historical README
phrasing is narrower than the charter; readers are directed to the root specification.

## ADR-003 — Transport exact record bodies (experimental)

Decision: an indexed directory stores raw BLOBs rather than reserializing JSON or
dumping executable SQL. Unknown record fields survive. Unsupported SQL additions
and unindexed files cause rejection. Consequence: lossless logical snapshots are
possible now; this is not a general SQL backup or writable directory engine.

## ADR-004 — Never infer authority from context (accepted direction)

Decision: imported content remains inert. Content inspection and grants are separate.
Unknown required policy extensions block semantic approval. Consequence: broad
representation does not imply broad execution compatibility.

## ADR-005 — Report validation layers separately (accepted direction)

Decision: independent integrity checking is separate from reused policy replay.
Revocation and independent policy validation remain explicit milestone gates.
Consequence: a green hash check cannot be presented as permission to execute.

## ADR-006 — Preserve MIT and defer public naming (proposed implementation)

Decision: keep the existing repository MIT license and imported notices unchanged.
Do not adopt a new license or assert naming clearance in this PR. Consequence:
specification/patent policy, third-party attribution, and public names require a
recorded publication decision. No endorsement or standards status is implied.
