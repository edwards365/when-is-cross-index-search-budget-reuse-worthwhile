# When Is Cross-Index Search Budget Reuse Worthwhile?

**Experiment, analysis, and benchmark of information limits, quality recovery, and conditional reuse costs.**

Rebuilding a physical ANN index can change the search budget needed by a query even when the data, query vector, and retrieval semantics remain fixed. This project asks three distinct questions:

1. What target decisions can a source-budget summary support?
2. How do target qualification and fallback change the deployed quality–work operating point?
3. When can search savings repay information acquisition, and what else could the same information support?

The current paper is an evaluation and analysis study, not a claim of a universally faster search algorithm. The repository is named after the paper; its earlier effective-resistance research remains in the history.

## Start here

- **[Public artifact entry](artifact/README.md)** — included files, a read-only check, and explicitly missing reproduction inputs.
- **[Response-analysis runbook](artifact/RUNBOOK.md)** — versioned input download, pinned environment, and portable reconstruction of nine analysis tables.
- [Evidence and terminology map](artifact/EVIDENCE.md) — connects saved results to the paper's main questions.
- [Publication and branch reconciliation](artifact/REPOSITORY_STATUS.md) — explains why the research history has not been merged wholesale.
- [Legacy project overview](docs/history/README_before_icde_artifact.md) — the preceding research agenda, retained as history rather than current claims.

## Current evidence and its limits

| Question | Evidence | Interpretation |
|---|---|---|
| Source-summary information | Finite-grid analysis and same-target saved-response cost optima for different summaries | Target-informed empirical references; not learned deployment policies or future-query guarantees |
| Quality recovery | Candidate/endpoint qualification, locked fallback, and comparisons with target-calibrated fixed budgets | Different quality–cost operating points; not a demonstrated same-risk incremental advantage of history |
| Cost of reuse | Acquisition ledgers, sharing scenarios, repeated-service models, and valid-answer lookup measurements | Conditional cost analysis, not complete end-to-end deployment acceleration |

The study includes 100K and roughly million-vector panels. They differ in more than scale, so they do not isolate a pure scale effect. Cross-build evidence and single-index native implementation checks have different roles. In particular, completed DARTH/Vamana native inner-product chains do not substitute for multi-build transfer validation.

The current release supplies selected saved results and a portable reconstruction of the same-target summary-cost, qualification-sensitivity, and fixed-cost-component tables from archived responses. It is **not yet the complete paper artifact**: other response panels, original ANN execution, and the submission-version paper/figure package remain to be curated. Publication adds no new ANN experiments or bootstrap analyses.

## Quick check

From a checkout of this version, using Python 3.11 or later and only the standard library:

```sh
python artifact/check_saved_results.py
```

This checks file identity and selected CSV arithmetic. It does not reconstruct raw ANN responses, retrain models, recompute confidence intervals, or validate all historical branches.

## Historical code and license

Earlier effective-resistance, rebuild-portability, and recovery studies remain in the repository history. Their README status labels and planned algorithms are not current paper claims. The existing [MIT license](LICENSE) is unchanged. Third-party components retain their own licenses; this snapshot grants no redistribution rights to external vector datasets. Citation metadata describes the repository, not an accepted publication.
