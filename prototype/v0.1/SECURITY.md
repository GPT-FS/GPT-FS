# Security boundaries and limitations

This release is a local proof of concept with a small deterministic execution boundary. It is not a hardened general-purpose agent sandbox.

## What is enforced

- All exposed mutations verify the existing container, then use a serialized SQLite transaction.
- Update/delete triggers and the absence of mutation APIs make existing objects and ledger records append-only through the normal interface.
- SHA-256 addresses detect accidental corruption or edits that do not reconstruct all affected hashes and references.
- Exact object scopes, allowed types, total admitted byte budgets, and capability allowlists are checked in code. Imported text cannot modify them.
- Execution requires a previously allowed admission belonging to the exact intent/object pair.
- Only deterministic text statistics run. There is no arbitrary-command dispatcher to escape through.
- ZIP members are bounded and inspected without filesystem extraction. Scripts and hook/MCP configuration are stored inertly. The same bounded archive reader is used when replay-verifying imports.
- Verification independently recomputes text-statistics evidence from the stored input within this same implementation.

## What is not enforced

| Threat / limitation | Actual v0.1 behavior |
|---|---|
| Malicious owner or process with write access | Can drop triggers, replace the database, forge labels and recompute a self-consistent ledger. The container alone cannot defeat this. |
| History truncation/replacement | A checkpoint retained outside attacker control detects changes to its anchored prefix. A checkpoint stored beside the writable database is convenient but not an independent trust anchor. |
| False human approval | `actor=Drew` is a local label. Any caller can supply it. There are no signatures, UI approval ceremony, identity verification or secret keys. |
| Hostile model | No model is connected. Structural gating is tested; resistance to model prompt injection is not. |
| Semantic laundering | An actor may label hostile text as `source` or invent an origin. Types are not content classifiers. Parent links assert provenance rather than validate semantic derivation. |
| External side effects | No remote operations are implemented or attested. A caller can act outside this harness; those actions are not captured. |
| Custody authenticity | Times come from the local clock, identities are self-asserted, and no external witness signs transfers. Custody covers local ingestion, not an organization's entire chain of possession. |
| Revocation | Intents and admissions have no expiry or revocation. They remain reusable. Use separate containers for separate trust domains. |
| Secrets/confidentiality | The database and report exports are plaintext. No encryption or access-control layer. Hashes can disclose equality and are not anonymization. |
| Denial of service | Import has per-archive bounds. Container growth, event count and full-history verification are unbounded; a very large database can be slow or memory intensive. |
| Malicious SQLite files | This is not a hardened parser for arbitrary attacker-crafted SQLite schemas/files. Keep Python/SQLite patched and treat unknown containers as untrusted inputs; a separate parser process with resource limits is future work. |
| Crash evidence | Transactions protect committed logical state, but no durable execution-start receipt is written before the operation. Interrupted attempts may leave no receipt. Forced power-loss behavior was not tested. |
| Source attribution | Exact uploaded bytes are retained; that proves byte identity, not authorship, originality, ownership or truth. |
| Verification independence | Replay uses the same codebase as execution. An independent implementation would provide stronger assurance against shared implementation bugs. |

## Meaning of “immutable” in this MVP

The intent ledger is immutable **through the provided append-only API and SQLite triggers**. It is hash-linked and optionally anchored to an external checkpoint. It is not WORM storage, a signed log, a blockchain, or an unforgeable audit trail. The test suite demonstrates both unanchored tail-truncation acceptance and anchored rejection so this limitation is visible rather than hidden.

The next trust-boundary work should precede adding arbitrary actions: authenticated intent issuance, revocation, an external signed checkpoint, and an isolated runner. A future model adapter must log the actual assembled context and output, not merely claim that an admission receipt implies the model saw or obeyed the data.
