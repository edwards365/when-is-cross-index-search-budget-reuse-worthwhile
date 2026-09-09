# E4 final report

Final label: `E4_STRONG_CONFIRMATION_TWO_DATASETS`

All 48/48 preregistered builds completed: 24 SIFT and 24 Arxiv. Each dataset used 1,000 confirmatory queries (250 sentinel, 750 evaluation), six budgets, and five latency repetitions. Native and instrumented result equality was checked by the runner for every query-budget cell.

## Dataset results

- sift_100k: gate STRONG_SUPPORT; budget-change fraction 0.8920; mean diameter 43.130; endpoint conversion 0.0260; source-reuse absolute risk 0.0324 (build-cluster 95% CI 0.0298, 0.0349); NDC regret 1.7833 (95% CI 1.7388, 1.8303).
- arxiv_nomic_100k: gate STRONG_SUPPORT; budget-change fraction 0.7590; mean diameter 29.729; endpoint conversion 0.0250; source-reuse absolute risk 0.0332 (build-cluster 95% CI 0.0299, 0.0364); NDC regret 2.4383 (95% CI 2.3835, 2.4970).

## Evidence boundary
