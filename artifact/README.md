# Artifact: cross-index search budget reuse

[Project home](../README.md) · [Runbook](RUNBOOK.md) · [Evidence map](EVIDENCE.md) · [Release](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-response-v1)

**Status: narrative-panel reconstruction supplement, 2026-10-07. Numerical figures and the listed narrative panels have runnable saved-record routes; full original execution remains incomplete.**

This directory is the public entry for *When Is Cross-Index Search Budget Reuse Worthwhile?* The versioned Git commit identifies exactly what is supplied. It replaces the absence of a public entry; it does not close the remaining input, portability, or publication checks.

## Choose your task

| Task | Entry | What it establishes |
|---|---|---|
| Inspect the saved results | `python artifact/check_saved_results.py` from the repository root | File identity and selected arithmetic |
| Reconstruct nine analysis tables | [Pinned environment and commands](RUNBOOK.md) | Selected derived results from saved responses |
| Reconstruct Figures 2, 4, 5 and 6 | [Paper reconstruction commands](paper/README.md) | Migration and paired intervals, cost curves and batch lookup means from pinned saved records |
| Reconstruct narrative panels and Figure 2 raw-to-cluster extraction | [Narrative commands](narrative/README.md) | Finite labels, recovery, demand mixing, refresh intervals and alternative-cost arithmetic |
| Find evidence behind a claim | [Evidence map](EVIDENCE.md) | File roles, terminology, and interpretation boundaries |
| Understand remaining delivery work | Coverage below and [repository status](REPOSITORY_STATUS.md) | What this partial release does and does not include |

## Coverage

| Layer | Included here | Remaining work |
|---|---|---|
| Saved-result inspection | Per-target mechanism/qualification CSVs, operating points and paired intervals, cost ledger, cache measurements, checksum manifest, standard-library checker | Review the complete paper-to-evidence coverage, not just this selected subset |
| Recompute saved-record analyses | Nine-table route, numerical-figure inputs, and narrative/raw-grid archives | Original response-generation routes remain incomplete; zero-cost diagnostic uses action identity, not new NDC measurement |
| Rebuild paper figures and PDF | Saved display values and evidence map | Curate the current TeX, editable PPT and export environment into a submission-version release; the separate Overleaf package is not this scientific artifact |
| Original ANN execution | Historical code and selected closure summaries | [Explicit remaining source/input/configuration work](EXECUTION_SCOPE.md); no original launch is implied by a saved-record PASS |

## Verify the supplied snapshot

```sh
python artifact/check_saved_results.py
```

Requires Python 3.11+; no third-party packages, network, ANN runs, or output files. The checker verifies the published manifest and selected aggregation identities. It does **not** independently verify the original measurements or regenerate bootstrap intervals. Do not execute historical workers against their original output directories to test this release.

To regenerate the nine selected tables from saved responses, follow [RUNBOOK.md](RUNBOOK.md). The [input manifest](input_manifest.json) pins the Release archive and each member. [Portability verification](receipts/portability_verification.json) records the new environment and complete output comparisons. This is a new portable derivative-analysis entry, not a rerun of a frozen host launcher or an independent ANN measurement.

The [manifest](manifest.json) pins the published payload. [Provenance](provenance.json) records original file hashes and the private research commit that produced the new mechanism analysis. That commit is a provenance identifier, not a promise that it is accessible in public Git history. The [configuration view](config/summary_bridge.public.json) replaces private absolute paths with basenames and retains input hashes; it is **not an executable reproduction configuration**.

The historical `analysis_final.json` says `PENDING_SEPARATE_CHECK` because it was written before the independent checker. `analysis_check.json` records the subsequent check and pins that exact final file. Neither receipt has been rewritten to look like a new public execution.

[Numerical reference source](reference/summary_analysis.py) preserves the analysis functions, omitting only the host-bound launcher and its resource import. The new [portable runner](reproduce_summary.py) validates the archive, resolves paths in a separate output directory, and compares every regenerated table with the saved output. It leaves original inputs and saved results unchanged.

## Navigate the evidence

See [EVIDENCE.md](EVIDENCE.md) for file roles, paper locations, field conventions, and interpretation boundaries. Preserve all supplied targets, infeasible cases, and zero differences. In particular, do not replace infeasible full-query objectives with conditional-subset values.

## Access, scope, and licensing

Git contains small project-generated tables, reports and code. Larger saved-response inputs are provided as a Release attachment: numeric row IDs, returned IDs, hits, work counters and decision/cost records. They contain no source vectors, documents, saved indexes or model files. Repository code/documentation and these project-generated outputs use the existing [license](../LICENSE); external data/component licenses are not overridden. Source datasets and third-party papers are deliberately not redistributed here. The repository is non-anonymous; suitability as a submission link must be checked against the applicable review rules.

No artifact badge, publication acceptance, independent-host reproduction, or complete end-to-end reproduction is claimed. Before calling this the final paper artifact, finish the missing layers above and pin the final paper version and its release commit.
