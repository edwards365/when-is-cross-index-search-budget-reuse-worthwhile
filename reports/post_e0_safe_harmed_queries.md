# Post-E0 Gate D0-B: safe/harmed query decomposition

Decision: **PASS_CONTINUE_D0 / SAFE_QUERY_EFFICIENCY_SIGNAL**.

| Dataset | Passing seeds | Dataset gate |
|---|---:|:---:|
| sift_10k | 3/3 | PASS |
| glove100_10k | 3/3 | PASS |
| arxiv_nomic_10k | 3/3 | PASS |

Safe/harmed status is paired by query and existing `ef`. Positive NDC improvement means Original used more distance computations than R4. The bootstrap resamples query IDs within each build seed; `ef` points are not treated as independent repetitions.

Candidate enqueue counts and terminal frontier states were not retained by E0 and were not replaced with proxy fields. Obtaining them requires a separately frozen trace replay in D0-D; no graph was rebuilt for D0-B.

Next action: **CONTINUE_D0_DFG**.

