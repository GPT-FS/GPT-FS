# Public launch foundation

**October 23, 2026.** The organization home is https://github.com/GPT-FS and the
canonical repository is https://github.com/GPT-FS/GPT-FS. Drew Hester / Labyrinth
Studios stewards the project. The owner merged the original foundation PR #8.

## Deliverables

- Organization identity and profile README; main repository description, topics,
  Discussions, contribution labels, and required main-branch checks.
- A GitHub Pages site with the project introduction, local-file inspector,
  independently implemented browser integrity reader, quickstart, synthetic fixtures,
  and a captioned walkthrough.
- Reviewed code path through a development branch and draft PR. The Pages preview
  may be published from that branch without merging it into main.
- Reproducible runtime/demo kit `0.1.1-rc.1`, checksum, manifest, and draft prerelease.
  It uses only synthetic sample data and the preserved prototype engine.
- Specific starter issues and announcement drafts. No external announcements or
  unsolicited messages are sent as part of preparing this foundation.

## What we can claim

The project has executable local tools, supported SQLite/directory snapshot round-trips,
recorded provenance and receipts, inert plugin import, and independent integrity checks.
It has an experimental storage-neutral specification and is open for contributions.
It does not yet have revocation, authenticated authority, independent full semantic
conformance, or a writable directory engine. Test results must name the layer checked.

## Contribution paths

Start with the `good first issue` label. The first tasks focus on byte-preserving
fixtures, quickstart reproduction, and export/extension behavior. Issue #3 is the
larger independent semantic validation project; issue #4 handles versioned revocation.
Use Discussions for concrete use cases and design questions; use issues for bounded work.

## Outreach sequence

1. Review the public launch PR and organization profile PR, then merge by owner decision.
2. Review the runtime candidate and the existing naming/source-rights issue #6.
3. Ask a few relevant developers to reproduce a specific example or identify an
   interoperability gap. Prepare the message; the owner chooses recipients and sends it.
4. Gather results and fix friction. Then use the captioned demo and runnable example
   for a wider introduction. Track independent runs, useful bug reports, real use cases,
   and outside implementations in addition to stars.

Draft announcements are in [ANNOUNCEMENT-DRAFTS.md](ANNOUNCEMENT-DRAFTS.md). The
Show HN option is a founder outline: its final post must be written personally by
the submitting human, in line with HN's rules on generated text.

## Administration decisions

Main requires a PR, all four existing conformance matrix checks, resolved review
conversations, and up-to-date checks. Force pushes and deletion are blocked, including
for admins. Zero approving reviews are required while the founder is the sole
maintainer; increase that count when another reviewer can approve. No bots receive
write permission. Existing MIT notices remain unchanged.

GitHub Pages serves a static snapshot from `gh-pages`. Its deployment commit records
the reviewed source SHA in `deployment.json`. The workflow regenerates it on owner-run
publication; visitors should treat the current launch site as a preview until the
launch PR is merged. The Pages branch contains generated site assets only.
