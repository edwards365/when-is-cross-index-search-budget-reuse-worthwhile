# Narrative-panel reconstruction

This supplement reconstructs retained narrative results, without launching ANN, training, old workers, or timing experiments. It supplements, rather than replaces, the two earlier immutable releases.

## Run from a clean checkout

Use Python 3.12 with `artifact/requirements-analysis.txt` (NumPy 1.26.4, SciPy 1.13.1). Download these two attachments from [artifact-paper-v2](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-paper-v2):

- `narrative-analysis-inputs-v2.zip`: 19,990,429 bytes, 46 members; [manifest](manifest.json).
- `graph-grid-records.zip`: 32,740,427 bytes, 96 original compressed CSVs plus their source manifest; [manifest](grid_manifest.json).

```sh
git clone --branch artifact-paper-v2 https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile.git budget-reuse
cd budget-reuse
python -m venv .venv
# Activate .venv using the command for your shell.
python -m pip install -r artifact/requirements-analysis.txt
python artifact/check_saved_results.py
python artifact/reproduce_grid.py --archive ../graph-grid-records.zip --output ../grid-output
python artifact/reproduce_narrative.py --archive ../narrative-analysis-inputs-v2.zip --output ../narrative-output
```

Place downloaded archives beside the cloned directory for these example paths. Outputs must be new directories outside `artifact/`. Inputs are checked before use; failures retain a diagnostic, never overwrite an earlier output. There is no network access inside either runner. A selected narrative route can be requested with `--parts recovery deep diagnostic refresh cost extensions` (all are the default).

## Result map

| Route | Input level | Output and manuscript use |
|---|---|---|
| `reproduce_grid.py` | 96 byte-preserved recorded CSVs, with original recall/hit fields | All 3,000 query clusters compared to Figure 2 inputs; `finite_variation.csv` and `query_labels.csv` reconstruct §IV-A finite-label variation. Figure 2 intervals remain the `reproduce_paper.py --parts F02` route. |
| `recovery` | Locked 100K source-target/query rows; saved seven-repeat means | `recovery_points.csv`, `recovery_decisions.csv`: prospective and all nine baseline arms; four original prospective risk/time intervals. Checks SIFT's two certified policies both execute 256. Original qualification selection and timing extraction remain upstream. |
| `deep` | All 72,000 recorded action rows | Source selection, separate qualification, all 56 deployed decisions, risk/work means and two intervals; `deep_recovery.csv`, `deep_decisions.csv`. |
| `diagnostic` | Original confirm-role query labels, including encoded no-finite-tail states | `diagnostic_pairs.csv`: all 648 directions and 594 mixing directions. `diagnostic_zero_cases.csv`: 18 Vamana pairs per dataset have 750 identical envelope/demand actions each; zero recorded-cost difference follows action identity, not an independent NDC measurement. |
| `refresh` | Saved initial/refreshed paired failure matrices | `refresh100k.csv`: both actual-failure increments and two original intervals. |
| `extensions` | Million-refresh full hit arrays/locks; million-transfer direction counts | `million_refresh.csv`: union-risk changes and two intervals, including the fallback pair. `million_transfer.csv`: all 56-direction means per dataset, not simultaneous certification. |
| `cost` | SHA-checked component ledger from the paper supplement | `alternative_costs.csv`: 14 policy/baseline component comparisons, including TG1000 and exact-answer reuse. No new measurement or equal-risk comparison. |

Repeated targets/queries are not treated as independent directions. Each panel retains its historical estimator: query-cluster sampling, crossed target/query index sampling, or product-multinomial sampling. The million-refresh RNG stream continues across datasets, as in its original analysis. Do not substitute one panel's estimator for another.

## Verification and limits

The final clean-export receipts are in `artifact/receipts/`. The first local integration attempt rejected the original `endpoint_fallback` field because the wrapper initially expected a different spelling; the corrected wrapper preserves the original decision and verifies its numeric arm. This was a wrapper error, not an ANN failure or new scientific retry.

`registered_sensitivities.csv` is an explicitly copied saved table, not an independently recalculated sensitivity experiment. Recovery timing inputs already aggregate seven repetitions. The 100K diagnostic retains source label encoding; `right_censored` does not imply a finite solution outside the grid. Raw returned IDs/truth have not been independently re-audited by these runners. The known historical status strings inside saved reports remain unchanged.

The archives contain project-generated records, IDs, hits, counters and timing observations, not source vectors, documents, indexes, models, credentials or third-party papers. The [whole-paper evidence map](../EVIDENCE.md) records remaining upstream gaps. Full original ANN execution is not claimed.
