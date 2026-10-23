# Ordered roadmap

This is an implementation plan, not a feature-completeness claim. Work is ordered
by dependency; public naming/source review can run alongside engineering.

| Order | Issue | Milestone | Acceptance / present status |
|---|---|---|---|
| 1 | [Recover and review foundation](https://github.com/DH-LStudios/GPT-FS/issues/1) | [M1](https://github.com/DH-LStudios/GPT-FS/milestone/1) | 21 archive members, 37 original tests, charter and preserved history; prepared for review |
| 2 | [Snapshot interoperability](https://github.com/DH-LStudios/GPT-FS/issues/2) | M1 | 14 tests, exact records/bytes/IDs/relationships/extensions/receipts, denials preserved; experimental implementation |
| 3 | [Independent semantic validator](https://github.com/DH-LStudios/GPT-FS/issues/3) | [M2](https://github.com/DH-LStudios/GPT-FS/milestone/2) | Shared vectors; two independent readers agree; not implemented |
| 4 | [Revocation and authority](https://github.com/DH-LStudios/GPT-FS/issues/4) | M2 | Versioned revocation; stale admissions denied; history retained; not implemented |
| 5 | [Writable directory binding](https://github.com/DH-LStudios/GPT-FS/issues/5) | [M3](https://github.com/DH-LStudios/GPT-FS/milestone/3) | Atomic append, recovery, races, same policy semantics; not implemented |
| 6 | [Naming and licensing review](https://github.com/DH-LStudios/GPT-FS/issues/6) | M3 | Recorded naming decision, source rights, licensing ADR if needed; preliminary research only |
| 7 | [Reviewed release](https://github.com/DH-LStudios/GPT-FS/issues/7) | M3 | Reproducible package, compatibility evidence, publication decision; not published |

## Deliberately later

Model-context assembly, richer semantic types, other vendor adapters, remote storage,
signatures, external tools, encrypted storage, and a graphical reader are candidates.
They must preserve the small kernel and honest capability negotiation. No commitment
to a vendor, service, or particular storage engine follows from listing a candidate.

## Review gate

Review the foundation and transport draft PR first. Keep issues 1–2 open until
review acceptance. Main remains the original branch until an explicit merge decision.
Then implement issue 3 and use it to independently test the issue 4 authority profile.
