# Contributing

Thank you for helping make the research easier to understand and reproduce. Start with the [artifact scope](artifact/README.md#coverage) and [runbook](artifact/RUNBOOK.md); the current release does not cover every historical experiment.

## Report a reproducibility issue

Use the [reproducibility issue form](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/issues/new?template=reproducibility.yml). Include:

- The tag or commit, operating system, Python and dependency versions.
- The exact command and whether you used the pinned input archive.
- Expected behavior, actual behavior, and a short sanitized log.

Remove credentials, personal paths, private host details, and restricted data before posting. Do not attach source datasets, indexes, or model files. Issues concerning historical experiments should name their originating commit and protocol.

## Propose a focused change

Separate documentation, portability fixes, numerical changes, and new experiments. Explain the intended scope and list checks actually run; identify unrun checks rather than treating them as passed.

- Preserve frozen inputs, outputs, manifests, failed runs, and original receipts. Do not change hashes simply to make a check pass.
- Do not rerun historical workers into their existing output directories.
- Keep new outputs separate. Changes to scientific semantics require a declared protocol, inputs, query roles, resource plan, and independent validation.
- Keep large data, generated indexes, credentials, and third-party papers out of Git.
- Preserve selection/qualification/evaluation separation and the distinction between diagnostic references and deployment policies.

## Validate artifact changes

From the repository root:

```sh
python artifact/check_saved_results.py
python -m unittest discover -s artifact -p "test_*.py"
```

For portable reconstruction, follow the isolated-environment instructions in [RUNBOOK.md](artifact/RUNBOOK.md). The saved-result check is not a substitute for reconstructing an analysis, and neither is an independent ANN run.

The manifest includes artifact documentation as well as data. An intentional edit requires updating the matching manifest entry and reviewing the changed-file list. Published release tags, inputs, and original evidence remain fixed; a scientific correction needs a separately identified version.

Changes to algorithms or the reference pipeline must also follow [AGENTS.md](AGENTS.md), including the relevant Python and C++ checks. Do not invent benchmark numbers, publication status, author metadata, or artifact certification.

## Review checklist

- Do links and commands resolve from a clean checkout?
- Are units, query roles, failure events, and comparison conditions unchanged or explicitly documented?
- Are reported measurements traceable to saved evidence?
- Are updated claims no stronger than the available evidence?
- Are existing user changes and unrelated research files preserved?
