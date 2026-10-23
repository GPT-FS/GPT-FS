# Comparison with Drew's actual Idea Lab bundle

Inspected October 23, 2026. Sources: the `idea-lab.plugin` attachment recovered from the referenced **Black Book Launch** conversation and `Screenshot 2026-10-22 153502.png`. The prior conversation's research briefings were not used as verified factual sources for this implementation.

## Observed archive, not a hypothetical Claude format

The uploaded `.plugin` file is a ZIP. Its SHA-256 is:

```text
01af0fa7d47ca4988f4e0f9c8a86b899bb29d96bbc52323d75aba40d4d4fdd8a
```

It contains eight files and eight directory entries:

```text
.claude-plugin/plugin.json
README.md
skills/brainstorm/SKILL.md
skills/brainstorm/references/techniques.md
skills/next-steps/SKILL.md
skills/pick-best/SKILL.md
skills/save-session/SKILL.md
skills/stress-test/SKILL.md
```

The manifest declares `name: idea-lab`, `version: 0.1.0`, a brainstorming description, seven keywords, and `license: MIT`. It contains no authority policy, intent ledger, context admission receipt or execution receipt. All eight files were read. The five skills describe brainstorming, stress testing, weighted selection, planning, and session write-up. Their YAML front matter includes skill names, activation descriptions and version metadata. The reference document contains creative techniques. The README says no agents, hooks or external connections are included; the archive listing supports that narrower structural claim. Its broader “works anywhere” claim was not tested.

The screenshot shows Claude's saved `idea-lab` plugin card, a save dialog proposing `idea-lab.plugin`, and an editor tree with the same manifest and skill paths. It corroborates the packaging/UI layout. It does not establish Claude's internal storage, enforcement architecture, or future plans. The prototype does not claim Anthropic copied this idea or that this format is first in the industry.

The per-file sizes and SHA-256 hashes are in `evidence/archive-inventory.json`. The raw ZIP is retained in `sample/research.gpt` as a bundle object, and each imported child is linked to it. `verify` compares every mapped child's bytes against that ZIP. The sample import is 9 objects: the ZIP plus 8 files.

## Differences demonstrated by this release

| Concern | Actual uploaded Idea Lab archive | GPTFS v0.1 implementation |
|---|---|---|
| Container | ZIP of path-named documents | SQLite logical object store with explicit format identity |
| Manifest | Plugin name/version/description/keywords/license | Format/schema/project identity and fixed capability ceiling |
| Content identity | Member paths; ordinary ZIP metadata | SHA-256 blobs plus canonical provenance-bearing object IDs |
| Skill content | Markdown instructions and references | Preserved Markdown bytes with `skill` type, no inherent authority |
| Provenance | No explicit object-parent graph in this bundle | Parent graph and local custody events |
| User intent | Not stored as a ledger in this bundle | Immutable-through-API intent records with structured scope |
| Admission | No per-use admission receipts in this bundle | Allow/deny records, rationale, exact intent/object binding |
| Execution | No execution history in this bundle | One local measured operation plus evidence/denial receipts |
| Integrity history | No hash-linked operational history in this bundle | Event chain and optional external checkpoint |
| Portability | Installable plugin-oriented package | Standalone local experiment; inert Claude bundle import |

The comparison is between **these actual files** and **this implementation**. Absence of a field in this plugin does not imply that Claude's host lacks permissions, analytics, audit logs, or other protections. The plugin and the runtime are different layers.

## Official documentation checked

[Claude Code's plugin manifest reference](https://code.claude.com/docs/en/plugins-reference), accessed October 23, 2026, documents `.claude-plugin/plugin.json`, plugin metadata, standard component layout, and component declarations such as skills, hooks, and MCP servers. It also says the manifest is optional in certain Claude Code loading paths; our adapter deliberately requires one for this small interoperability profile.

[Claude's Plugins API documentation](https://platform.claude.com/docs/en/manage-claude/plugins-api), accessed October 23, 2026, describes organization-level plugin inventory, version publication, installation control and content download. Those host-level facilities are outside the uploaded archive and outside this MVP comparison.

## Design judgment

🧠 The useful independent contribution here is the integration contract: context identity, recorded provenance, explicit scoped intent, admission, and evidence fit into one inspectable local container. ZIP versus SQLite is only the storage choice. Content-addressed stores, append-only logs and capability checks are established techniques; this release combines them for Drew's context-integrity workflow without claiming a new cryptographic primitive or universal standard.

🧠 Two directions remain plausible. An extension of existing plugin packaging would maximize immediate installation compatibility. A separate context/evidence container makes the provenance and authority contract more explicit. This prototype chooses the second and preserves the first through an inert importer, keeping that tradeoff reversible.
