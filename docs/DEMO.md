# Try the public demo

Open **[the live inspector](https://gpt-fs.github.io/GPT-FS/)**. No account or API key
is required. The bundled notebook is wholly synthetic and MIT licensed.

1. Select **Original source**. Inspect the exact original text, identity, and blob digest.
2. Select **Trace a relationship**. The note links back to the observation; use its
   Parent button to navigate to the source.
3. Select **Inspect a denial**. The skill stays data. Its admission is denied by type
   scope; a shell.exec request is denied by capability scope. Those are historical
   receipts from the Python demo, not decisions made by the browser.
4. Select **Change a byte**. The browser changes a copy of one blob while retaining
   its claimed identity. Independent SHA-256 validation fails. **Reset demo** restores it.

The browser independently checks the supported canonical bodies, blob/object/event
hashes, reference targets, chain ordering, genesis, and checkpoint ancestry. It does
not implement full policy replay, authentication, or revocation.

## Open your own package

From the source checkout, export a browser snapshot locally:

```sh
python tools/browser_snapshot.py project.gpt project.snapshot.json --checkpoint project.checkpoint.json
```

The checkpoint option is optional. The source may also be a supported directory
snapshot. The command refuses to overwrite an existing destination. Open the JSON
using **Open your snapshot**. The page reads local files into tab memory, uses text
nodes for previews, and does not upload them or store them in browser persistence.
The page has no analytics or third-party assets. GitHub still serves ordinary site
requests; this is not a promise about hosting access logs or browser extensions.

**Add external checkpoint** accepts a separately retained checkpoint JSON. A match
is only as trustworthy as how that checkpoint was obtained and retained. A checkpoint
bundled with a package establishes internal consistency, not independent authenticity.

The inspector accepts this versioned JSON transport, not raw SQLite. It limits input
to 32 MiB and 10,000 rows per table; the CLI has its own bounds. Large or unfamiliar
profiles can be rejected. All local content is inert. There is no execution button.

## Reproduce the Python round-trip

```sh
python tools/build_demo.py
python tools/portable.py export website/data/demo.gpt notebook
python tools/portable.py verify notebook --checkpoint website/data/demo.checkpoint.json --policy
python tools/portable.py import notebook restored.gpt
python tools/portable.py verify restored.gpt --checkpoint website/data/demo.checkpoint.json --policy
```

Use new destinations. `--policy` reuses the historical GPTFS policy validator. Compare
this with the separately written browser integrity reader; neither claim is full
independent semantic conformance. The public fixture contains 7 objects and 14 events.

The recorded walkthrough, captions, and transcript are served with the site. Its
actions are browser captures of the actual UI; it does not represent a model evaluation.
