# Contributing

Read [CHARTER.md](CHARTER.md), [SPEC.md](SPEC.md), and [SECURITY.md](SECURITY.md).
Use a development branch and a draft PR. Do not rewrite preserved release evidence
or silently change identity and authority semantics. New format behavior needs an ADR,
an explicit profile/version decision, and positive and adversarial fixtures.

Run from the repository root:

```sh
python tools/check_archive.py
python -m unittest discover -s tests -v
```

Run the historical suite from `prototype/v0.1`:

```sh
python -m unittest discover -s tests -v
python gptfs.pyz verify sample/research.gpt --checkpoint sample/checkpoint.json
```

PR descriptions must distinguish implemented, tested, proposed, and unsupported
behavior. Include exact commands and results, migration consequences, and which
validation layer was exercised. Use synthetic inputs unless distribution rights
and privacy have been checked. Preserve attribution; see [LICENSING.md](LICENSING.md).

Do not commit caches, credentials, new private research data, or generated local
experiments. Recovered sample data is included as provenance-bearing prototype
evidence and remains subject to its source terms. Public distribution review is open.
