# Announcement drafts — for founder review and sending

These are prepared copy and talking points. None has been posted or sent. Confirm
the live demo, current CI, and naming decision before using branded launch copy.

## Short project introduction

We’re building GPT File System: a proposed portable logical format and local-first
tools for carrying original content, provenance, and relationships between systems.

The key boundary is simple: a document can supply information, but it cannot grant
itself permission to act.

There’s working Python software, a SQLite ↔ directory snapshot round-trip, and a
browser inspector that verifies original bytes and history locally. The public demo
lets you trace a derived note to its source, inspect a denied capability request,
and change a byte to see verification fail.

This is an experimental prototype, with independent policy validation and revocation
still ahead. We’re looking for concrete use cases, interoperability tests, and people
who want to challenge the format's assumptions.

Demo: https://gpt-fs.github.io/GPT-FS/
Source: https://github.com/GPT-FS/GPT-FS

## Personal invitation draft

I’m developing an open-source project called GPT File System with Labyrinth Studios.
It explores portable context, provenance, and explicit authority records across tools.

Would you be willing to try one small example and tell me where it breaks down for
your work? I’m especially interested in what gets lost when you move information
between systems, and whether our object and relationship model captures it.

The demo is local in the browser, requires no account, and uses synthetic data:
https://gpt-fs.github.io/GPT-FS/

Source and limitations: https://github.com/GPT-FS/GPT-FS

— Drew

## Show HN founder outline (not a generated submission)

Write the final post in your own words. HN asks people not to post generated text:
https://news.ycombinator.com/newsguidelines.html

- Explain the problem you personally encountered and why you began the project.
- Link directly to the runnable demo, with source as a second link.
- Describe the exact demonstrated behavior: bytes, relationships, policy receipts,
  round-trip conversion, and independent integrity checks.
- State the unfinished pieces: revocation, authentication, and independent semantics.
- Ask one specific engineering question you want help answering.
- Avoid claims of novelty, universal compatibility, standards adoption, or guaranteed safety.

## Maintainer response notes

If asked “Is SQLite the format?”, explain the logical-spec/reference-implementation
distinction. If asked “Is it authenticated?”, distinguish integrity and owner labels
from signatures and trust roots. If asked about unknown extensions, explain preservation
and required-extension blocking without implying runtime support.
