# Contributing

Contributions are welcome when they preserve the repository's evidence and reproducibility contracts.

## Before opening a change

1. Read the [repository map](docs/REPOSITORY_MAP.md) and [reproducibility contract](docs/reproducibility.md).
2. Keep datasets, indexes, credentials, private paths, raw traces, and large generated outputs out of Git.
3. Do not modify frozen scientific outputs in place. Add a derived output with its inputs and protocol recorded.
4. Do not use evaluation outcomes to choose a candidate, threshold, action order, or fallback rule.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[analysis,test]'
```

Run the relevant checks before submitting:

```bash
python -m pytest tests/python theory/tests -q
ruff check python scripts tests theory
cmake -S . -B build
cmake --build build --config Release
ctest --test-dir build -C Release --output-on-failure
```

Documentation-only changes need not build native targets, but links and commands should be checked from a clean checkout.

## Scientific changes

A claim-bearing pull request must state:

- the frozen question and stop rule;
- input manifests and SHA-256 hashes;
- build, seed, dataset, action-grid, and query-role identities;
- the statistical unit and confidence procedure;
- which outputs are exploratory, confirmatory, or post-hoc;
- negative results, fallbacks, censoring, and protocol deviations; and
- the exact claim(s) the evidence can and cannot support.

If a new result changes a paper number, update the compact evidence, provenance map, generated table/figure, manuscript text, and validation test together.

## Code style

- Python: Ruff-configured style, 100-character lines.
- Native code: C++17.
- Prefer deterministic seeds and explicit configuration files.
- Preserve old manifests and results needed by published or submitted artifacts.

## Pull requests

Use the repository pull-request template. Keep unrelated changes separate, and call out compatibility effects on public commands, package imports, schemas, or replay paths.
