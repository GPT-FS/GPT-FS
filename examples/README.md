# Runnable examples

From the repository root, with Python 3.10+:

```sh
python prototype/v0.1/demo.py my-experiment
python tools/portable.py export prototype/v0.1/sample/research.gpt my-directory
python tools/portable.py verify my-directory --checkpoint prototype/v0.1/sample/checkpoint.json --policy
python tools/portable.py import my-directory restored.gpt
python tools/portable.py verify restored.gpt --checkpoint prototype/v0.1/sample/checkpoint.json --policy
```

All destination paths must be new. The directory exposes exact raw record bodies
and an index for inspection. Conversion returns `policy: not-evaluated`; the separate
verification command reports whether prototype policy replay passed. The independent
integrity layer is exercised even when policy replay is omitted.

To inspect another Claude bundle as inert data:

```sh
python prototype/v0.1/demo.py plugin-experiment --plugin /path/to/idea-lab.plugin
```

Nothing in a plugin grants permission. The demo's deterministic runner only supports
`text.stats`; a `shell.exec` request is denied. See the tests for binary, hostile-text,
extension-preservation, and tampering fixtures.
