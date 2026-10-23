# Lean roadmap after v0.1

Everything below is proposed, not shipped.

## Next: v0.1.1 — lifecycle and independent verification

1. Add intent revocation and explicit supersession. Acceptance: an old admission stops authorizing new work after its intent is revoked, while all past receipts still replay.
2. Add a standalone verifier with a separate implementation and fixed canonicalization test vectors. Acceptance: both implementations agree on valid sample IDs and reject the same mutated fixtures.
3. Add schema validation and strict limits for untrusted containers. Acceptance: extra unknown fields, malformed graphs, excessive nesting and excessive history cannot bypass validation or exhaust a bounded verifier process.
4. Add a read-only local receipt browser. Acceptance: Drew can follow original source → derivation → intent → admission → execution → evidence without reading raw JSON.

## Then: v0.2 — one real model adapter

1. Build exactly one opt-in provider adapter behind the same admission boundary. Record exact assembled context, provider/model identifier, request metadata and output bytes; never save credentials in the container.
2. Add token budgets alongside byte budgets. Record actual context inclusion, truncation and ordering; an admission decision alone is not evidence of inclusion.
3. Add authenticated human intent approval and a signed checkpoint stored separately from the runner. A signature proves possession of a key; identity binding and key custody must be explicit.
4. Keep external actions disabled until the runner is isolated and tested. Acceptance: malicious source/skill text cannot expand tools or object scope, and every tested action is paired with an independently observable result.

## Later, only if usage justifies it

- Process isolation and external action adapters with before/after observations, timeouts, durable start/failure events and idempotency keys.
- Richer provenance: verified observations versus reported observations, named derivation activities, authenticated custody transfers.
- Multi-writer history, merge semantics and offline synchronization.
- Encrypted storage, selective export and explicit redaction lineage.
- Cross-runtime export, richer Claude component mapping, and migration tools.
- OS integration or a mounted filesystem only if it adds useful workflows beyond the local object API.

🧠 The next demonstration should be one model completing a small research task from two admitted sources, with an inspectable record of exactly what it received and what it produced. That would test the central value proposition more directly than adding another dozen object types or building a large UI first.
