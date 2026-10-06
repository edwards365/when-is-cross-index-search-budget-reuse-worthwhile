# Artifact: cross-index search budget reuse

**Status: public saved-result snapshot v0, 2026-10-06. Not a complete reproducibility release.**

This directory is the public entry for *When Is Cross-Index Search Budget Reuse Worthwhile?* The versioned Git commit identifies exactly what is supplied. It replaces the absence of a public entry; it does not close the remaining input, portability, or publication checks.

## What is available

| Layer | Included here | Remaining work |
|---|---|---|
| Saved-result inspection | Per-target mechanism/qualification CSVs, operating points and paired intervals, cost ledger, cache measurements, checksum manifest, standard-library checker | Review the complete paper-to-evidence coverage, not just this selected subset |
| Recompute analyses from responses | Numerical source for inspection, path-redacted configuration view and input hashes; saved historical completion and separate-check receipts | Distribute permissible profile arrays and role inputs; supply a portable analysis entry with an independent clean-environment test |
| Rebuild paper figures and PDF | Saved display values and evidence map | Curate the current TeX, editable PPT and export environment into a submission-version release; the separate Overleaf package is not this scientific artifact |
| Original ANN execution | Historical code remains in repository branches | Reconcile the execution code, frozen protocols, dependencies, input acquisition/licenses, hardware/resource requirements and runbook |

## Verify the supplied snapshot

```sh
python artifact/check_saved_results.py
```

Requires Python 3.11+; no third-party packages, network, ANN runs, or output files. The checker verifies the published manifest and selected aggregation identities. It does **not** independently verify the original measurements or regenerate bootstrap intervals. Do not execute historical workers against their original output directories to test this release.

The [manifest](manifest.json) pins the published payload. [Provenance](provenance.json) records original file hashes and the private research commit that produced the new mechanism analysis. That commit is a provenance identifier, not a promise that it is accessible in public Git history. The [configuration view](config/summary_bridge.public.json) replaces private absolute paths with basenames and retains input hashes; it is **not an executable reproduction configuration**.

The historical `analysis_final.json` says `PENDING_SEPARATE_CHECK` because it was written before the independent checker. `analysis_check.json` records the subsequent check and pins that exact final file. Neither receipt has been rewritten to look like a new public execution.

[Numerical reference source](reference/summary_analysis.py) preserves the analysis functions, omitting only the host-bound launcher and its resource import. It is inspectable code, not a tested portable reproduction entry. Importing or syntax-checking it does not reproduce results; its required raw inputs are not bundled here.

## Navigate the evidence

See [EVIDENCE.md](EVIDENCE.md) for file roles, paper locations, field conventions, and interpretation boundaries. Preserve all supplied targets, infeasible cases, and zero differences. In particular, do not replace infeasible full-query objectives with conditional-subset values.

## Access, scope, and licensing

These are small project-generated analysis tables and reports, not vector datasets, saved ANN indexes, environment archives, or complete raw response arrays. Repository code/documentation follows the existing [license](../LICENSE); external data/component licenses are not overridden. Source datasets and third-party papers are deliberately not redistributed here. The existing repository is non-anonymous; whether it is an appropriate submission link must be checked against the applicable review rules.

No artifact badge, publication acceptance, independent-host reproduction, or complete end-to-end reproduction is claimed. Before calling this the final paper artifact, finish the missing layers above and pin the final paper version and its release commit.
