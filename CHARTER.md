# Founding charter

**October 23, 2026 — Drew Hester / Labyrinth Studios**

**HYBRID. FLEXIBLE. AGNOSTIC. ALL-INCLUSIVE.**

This charter establishes [DH-LStudios/GPT-FS](https://github.com/DH-LStudios/GPT-FS)
as the canonical project home for the GPT File System initiative: its proposals,
reference implementation, conformance evidence, decisions, and development history.
It records the founder's direction; it is not a claim of standards-body adoption,
trademark clearance, or invention priority. The repository predates this charter.

`.GPT` is the proposed portable **logical specification**. **GPTFS** is a reference
implementation. No database, model provider, operating system, programming language,
commercial service, or execution runtime owns the meaning of the specification.

## The four principles

- **HYBRID:** structured records and original files; human and agent contributions;
  local and remote references; immutable evidence and explicitly versioned working
  state can coexist. A reference is distinguishable from embedded content.
- **FLEXIBLE:** a small mandatory kernel supports namespaced extensions and explicit
  profiles. Unknown information survives transport; unsupported meaning is disclosed.
- **AGNOSTIC:** SQLite is one binding. Directories and other storage engines can
  implement the same logical model. A conforming reader need not use a language model.
- **ALL-INCLUSIVE:** any media or object domain can be represented without forcing
  it into a prompt, skill, or vendor-specific format. Inclusion never implies trust,
  authorization, execution, or universal runtime compatibility.

## Commitments

1. Preserve original bytes and traceable provenance. Derived interpretation is a
   separate object with relationships to its sources.
2. Separate context from authority. Imported prose, plugin manifests, filenames,
   and metadata cannot authorize themselves or expand a user's grant.
3. Make intent, admission, execution, denial, and evidence inspectable.
4. Preserve identities, relationships, opaque extensions, and policy meaning across
   supported storage bindings; reject conversions that would silently lose meaning.
5. State uncertainty and implementation limits. A passing integrity check is not
   proof of authentic authorship, permission, or a safe external effect.
6. Prefer executable examples, adversarial fixtures, and independent validation over
   declarations of compatibility. Revocation must be designed before general runners.
7. Keep progress reviewable through branches, draft PRs, issues, and recorded decisions.

## Stewardship and publication

Drew Hester / Labyrinth Studios stewards this initiative. Changes to the core meaning
require a recorded decision and review. Experimental profiles can evolve without
pretending to be stable standards. The existing MIT license remains in place;
preserve separate source notices. Public branding, releases, and any new licensing
scheme require the publication work in [NAMING.md](NAMING.md) and [LICENSING.md](LICENSING.md).
