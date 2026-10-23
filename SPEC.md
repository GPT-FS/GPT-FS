# .GPT logical specification — working draft 0.1

**Status: proposed, October 23, 2026. Not a ratified or stable standard.**
The implemented legacy format is documented in
[prototype/v0.1/SPEC.md](prototype/v0.1/SPEC.md). Its SQLite-specific statements apply
only to that prototype. This document does not retroactively change its wire format.

## Scope and terminology

`.GPT` describes a portable logical package of objects, their relationships, and
explicitly identified extensions. GPTFS is one implementation of selected profiles.
The extension `.gpt` alone never identifies a valid profile or grants permission.
A binding maps logical records to storage, such as SQLite or a directory.

The words MUST, MUST NOT, and SHOULD below express proposed conformance requirements
for this draft, not a claim that every requirement is implemented today.

## Small mandatory kernel

| Record | Proposed minimum meaning |
|---|---|
| Manifest | Logical format/profile and version, package identity, identity algorithm, required extension identifiers, binding identifier |
| Object | Stable identity, claimed type/media type, embedded bytes or explicit external reference, provenance, extension fields |
| Relationship | Source/target identity and namespaced relation type; distinguish internal and external targets |
| Namespace | Globally distinguishable extension identifier and version; conflict handling |
| Extension | Exact opaque payload, declared criticality, optional interpretation profile |

Objects are data by default. Claimed authorship, origin labels, and timestamps are
assertions unless authenticated under an explicitly supported profile. External
references MUST NOT be fetched merely by opening or validating a package.

## Identity and fidelity

Bindings MUST preserve payload bytes, identifiers, relationship targets, and all
unknown extension payloads in their supported interchange profile. They MUST NOT
silently rewrite line endings, Unicode, envelopes, or policy records. Logical
equivalence does not require identical SQLite pages or ZIP compression bytes.

The provisional GPTFS 0.1 profile uses SHA-256 for raw blobs and domain-separated
hashes for canonical object/event bodies. Its `gptfs-json-1` canonicalization excludes
floats, non-ASCII keys, and integers outside the exact 53-bit range. These are profile
choices, not permanent constraints on every future .GPT identity scheme.

Unknown optional extensions may be preserved without interpretation. Unknown required
extensions MUST prevent policy approval and execution. Retaining bytes does not
establish semantic support. Unsupported schema additions MUST be rejected explicitly
if the binding cannot preserve them. Extension stripping requires a new, explicitly
derived package; it is never a lossless round-trip.

## Authority extension — proposed direction

An authority profile distinguishes declarations of intent from authenticated grants.
An admission is bound to a package, intent, object identities, permitted use, budget,
and policy version. An execution receipt binds that admission to a capability and
result or denial. Imported text MUST NOT produce a grant.

Revocation is an append-only event referring to an existing grant/intent. Proposed
semantics: effective from its ledger position; historical receipts remain true as
historical records; later admissions and executions are denied, including replay of
an earlier admission. An execution MUST recheck current authority at dispatch.
Expiry, authenticated principals, external revocation freshness, concurrent dispatch,
and offline rollback protection remain open design work. **v0.1 has no revocation.**

## Validation levels

1. **Transport:** all indexed files and exact bytes are present.
2. **Integrity:** identities, reference targets, and event chain agree; a separately
   retained checkpoint can detect rollback relative to that checkpoint.
3. **Semantics:** a known policy profile reproduces decisions and deterministic evidence.
4. **Authority:** authenticated principals, current grants/revocations, and trust roots
   are verified. This level is not implemented by v0.1 owner labels.

Results MUST report their level and unsupported requirements. No lower level implies
a higher one. Full independent semantic conformance is a release gate, not a current claim.

## Implemented experimental directory binding

`tools/portable.py` implements `gptfs-0.1-directory-1`, a lossless transport snapshot
of the prototype's four logical record collections. It is not yet a writable directory
runtime or the finalized generic .GPT kernel.

`index.json` contains `profile` and `tables`. The tables are `manifest`, `blobs`,
`objects`, and `events`. Each ordered row has `keys` (the original primary/identity
columns), `file` (`<table>/<8-digit-index>.bin`), and `sha256` (raw file digest).
The `.bin` file is the original BLOB body, including canonical JSON bodies unchanged.
Rows use ascending SQLite primary-key order. No supplied SQL is evaluated on import.

Only the known columns are supported. Extra SQL tables/columns and unindexed directory
files are rejected to avoid data loss. Unknown fields inside supported record bodies
are retained byte-for-byte; preserving them makes no policy claim. SQL indexes,
triggers, physical layout, and application-specific SQL are not transported. Import
recreates the known schema and append-only triggers. The binding has a 64 MiB input
limit and directory entry limit; these are prototype resource bounds.

`verify` independently checks hashes/graph/chain. `verify --policy` additionally uses
the original GPTFS verifier on a disposable reconstruction and blocks nonempty
manifest `required_extensions`. This reused policy engine is not independently
implemented. Direct use of the historical v0.1 runner does not enforce that new
extension convention; do not feed extended profiles to it.
