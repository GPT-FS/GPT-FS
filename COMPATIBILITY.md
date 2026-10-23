# Compatibility and conformance

| Surface | Actual status | Boundary |
|---|---|---|
| GPTFS 0.1 SQLite schema 1 | Recovered implementation, 37 original tests | Fixed types and text.stats only |
| SQLite ↔ directory | Implemented experimental snapshot transport | Exact four-table logical rows; not physical database bytes |
| Bytes, IDs, parents, intent/admission/execution records | Tested unchanged through round-trip | No conversion-time authority grant |
| Unknown fields/extensions in record bodies | Raw bytes preserved | No semantic support inferred |
| Unknown required manifest extensions | Preserved; transport policy replay blocked | Historical runner lacks this guard |
| Extra SQL tables/columns, extra directory files | Rejected | Explicit incompatibility instead of silent loss |
| Claude .plugin | Existing inert importer and exact original ZIP retention | No Claude runtime emulation or plugin export |
| Independent validator | Hashes, blob sizes, graph targets, chain, checkpoint | Not independent full policy replay |
| Revocation/expiry | Proposed only | No current enforcement |
| Generic .GPT kernel | Working draft | Not a published standard |
| Other providers, MCP launch, remote storage | Not implemented | Representation is not runtime compatibility |

Python 3.10+ standard library is the declared baseline. CI covers Python 3.10 and
3.14 on Ubuntu and Windows; consult actual run results rather than inferring success
from the matrix. Local validation is on Windows/Python 3.14.

## Conformance vectors

`tests/test_portable.py` covers binary and CRLF/NUL bytes, object ancestry, policy
denials, receipts, external checkpoints, unknown required extensions, repeat export,
tampering, traversal, duplicate JSON keys, unsupported tables, extra files, and the
real recovered sample. The original suite includes inert hostile skill text and
forged decision replay. These are deterministic software tests, not model safety tests.

A future binding must pass common vectors and negative cases against at least two
independent readers before claiming semantic interoperability. Identity algorithm
changes require a versioned migration with explicit old/new mappings.
