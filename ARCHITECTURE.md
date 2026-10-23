# Architecture

**Current:** recovered GPTFS 0.1 plus experimental portable transport.
**Proposed:** storage-neutral .GPT kernel with separately negotiated extensions.

```text
Original bytes -> inert import -> objects + provenance + ledger
                                    |
                      SQLite snapshot <-> directory snapshot
                                    |
                     independent integrity validation
                                    |
                    known-profile policy replay (v0.1)
                                    |
              explicit grant + admission -> text.stats -> receipt
```

The immutable original release lives under `prototype/v0.1/`. Its source, executable,
sample, tests, documents, and notices are preserved. Root documents govern ongoing
development; historical documents describe the recovered artifact, not the full vision.

`tools/portable.py` reads SQLite in a read-only transaction, copies raw record bodies,
and regenerates only a fixed schema. The independent integrity validator uses the
standard library and does not import the writer. Optional semantic replay imports
the historical validator and operates on a temporary database. Validation never
launches a plugin, invokes a model, or retrieves an external reference.

The directory is an interchange binding today. A future storage protocol should
expose immutable blob/record retrieval, atomic append, snapshot consistency, and
checkpoint operations, without exposing SQL to the logical model. A writable
directory backend must prove crash recovery and concurrent append behavior first.

## Trust boundaries

- Package bytes and imported text are untrusted input.
- The prototype owner is a label, not an authenticated identity.
- The host controls execution and trust roots; a package cannot authorize its host.
- A checkpoint only protects history relative to where and how that checkpoint is
  retained. A checkpoint stored beside mutable data is not an independent witness.
- Storage preservation, semantic verification, and external execution are separate operations.

## Immediate engineering order

Freeze conformance vectors; implement independent semantic replay and versioned
revocation; then introduce a writable second backend. Broader runners and remote
services depend on those foundations. See [ROADMAP.md](ROADMAP.md).
