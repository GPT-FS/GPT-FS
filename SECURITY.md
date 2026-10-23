# Security and authority boundaries

This is experimental local software. Supported review targets are the preserved
GPTFS 0.1 prototype and the new portable transport. There is no hardened general
runner, authenticated grant service, encryption layer, or OS sandbox.

## What is enforced

The prototype uses content hashes, object relationships, a chained event ledger,
bounded imports, exact intent scope, admission receipts, and deterministic text
statistics. Imported plugin text does not become executable authority. The transport
preserves raw records, rejects unsupported table/column additions and unindexed
files, and never executes imported SQL. Required extensions block its policy replay.

## What is not established

- Hashes do not authenticate an author. A writer can rewrite a whole history unless
  checked against an independently retained checkpoint or other trust root.
- Owner/actor fields are labels. They are not signatures or user authentication.
- v0.1 has no revocation or expiry. An old admission remains usable under its policy.
- Independent integrity checks do not independently reproduce all policy decisions.
- A losslessly converted unknown extension remains unsupported, not authorized.
- Local filesystem inputs can change during inspection. Do not validate attacker-
  mutable directories concurrently; filesystem race hardening remains follow-up work.
- Resource caps reduce accidental overload; this is not a hardened hostile-input service.
- A failed export can leave an incomplete destination. Treat absence or failure of
  `index.json` verification as an incomplete package; never run partial output.

The historical runner understands only its original profile. Do not use it as an
execution path for extended packages. No external-effect runner should be added
before authenticated authority, revocation, and independent policy conformance exist.

## Reporting

For non-sensitive defects, use the repository bug template with synthetic fixtures.
For a vulnerability, use GitHub private vulnerability reporting if enabled; otherwise
contact the repository owner privately through an already established channel.
Do not place secrets or live exploit credentials in an issue. No response-time or
private-reporting availability guarantee is claimed here.


## Browser inspector

The static inspector uses same-origin modules, a restrictive meta CSP, text-node
rendering of untrusted content, bounded input, and SHA-256 via Web Crypto. It does
not persist local snapshots, upload their content, fetch external package references,
or evaluate imported instructions. The bundled synthetic fixture is fetched from
the site. GitHub serves normal page requests; hosting access logs and browser
extensions are outside this application's boundary. The reader evaluates integrity,
not policy permission. Required extensions are surfaced without approval.
