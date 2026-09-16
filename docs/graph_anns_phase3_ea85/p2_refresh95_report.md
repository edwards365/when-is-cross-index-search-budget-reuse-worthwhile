# Phase 2 Recall@10=.95 mixed-refresh report

Decision: **REFRESH95_SEARCH_GATE_PASSED_LIFECYCLE_COST_CONDITIONAL**.

This report uses 20 fixed target builds, disjoint 500/500/1000 selection/certification/cold-evaluation roles, one-sided 95% Clopper–Pearson certification, and 5,000 paired target-build bootstrap replicates (seed 991).

| Dataset | Method | Certified builds | Fallback builds | Eval risk | Mean gain | 95% CI | p95 noninferior | Min LOBO | Delete-largest | Median repeated-set break-even |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sift100k | FIXED_SAFE_NATIVE_ENDPOINT | 10/10 | 0/10 | 0.0097 | 0.0000 | [0.0000, 0.0000] | 1 | 0.0000 | 0.0000 | inf |
| sift100k | SOURCE_TCP_POOL_REUSE | 0/10 | 0/10 | 0.0669 | 0.5951 | [0.5898, 0.6005] | 1 | 0.5948 | 0.5948 | 8.2 |
| sift100k | ICBA_AUDITED_SOURCE_TCP_WITH_FIXED_SAFE_FALLBACK | 10/10 | 10/10 | 0.0097 | 0.0000 | [0.0000, 0.0000] | 1 | 0.0000 | 0.0000 | inf |
| sift100k | TARGET_SELECTION_TCP_RECALIBRATION | 10/10 | 0/10 | 0.0179 | 0.4439 | [0.4388, 0.4491] | 1 | 0.4437 | 0.4437 | 11.0 |
| arxiv_nomic_100k | FIXED_SAFE_NATIVE_ENDPOINT | 10/10 | 0/10 | 0.0101 | 0.0000 | [0.0000, 0.0000] | 1 | 0.0000 | 0.0000 | inf |
| arxiv_nomic_100k | SOURCE_TCP_POOL_REUSE | 0/10 | 0/10 | 0.0724 | 0.6421 | [0.6367, 0.6474] | 1 | 0.6418 | 0.6418 | 6.8 |
| arxiv_nomic_100k | ICBA_AUDITED_SOURCE_TCP_WITH_FIXED_SAFE_FALLBACK | 10/10 | 10/10 | 0.0101 | 0.0000 | [0.0000, 0.0000] | 1 | 0.0000 | 0.0000 | inf |
| arxiv_nomic_100k | TARGET_SELECTION_TCP_RECALIBRATION | 10/10 | 1/10 | 0.0204 | 0.4479 | [0.3472, 0.5015] | 1 | 0.4423 | 0.4423 | 8.7 |

## Interpretation

The raw source TCP row is a transfer diagnostic; certification status is reported but evaluation is not replaced by fallback. The audited and target-recalibrated rows are deployable lanes: a rejected candidate falls back to the independently checked ef=200 endpoint. Fixed-safe fallback is not counted as adaptive-method value.

A one-dataset improvement is conditional evidence only. The primary promotion gate requires simultaneous safety, mean, tail, bootstrap, LOBO, and delete-largest closure on both datasets.

The search-only Gate closes for target-selection recalibration, but this is not yet an unconditional end-to-end lifecycle claim. Source profiling is charged separately: the break-even column is the number of repeated passes over the same profiled query set needed for target-serving savings to repay conservative source-grid profiling. Exact-truth, rebuild, and control-plane costs are not harmonized, so the lifecycle conclusion remains conditional.
