# Post-E0 Gate D0-A: observed-point equal-recall Pareto

Decision: **PASS_CONTINUE_D0 / EQUAL_RECALL_EFFICIENCY_SIGNAL**.

Only the six frozen E0 `efSearch` points were used. No interpolation, extrapolation, new graph, validation-dev, or formal-test access was permitted.

| Dataset | Passing seeds | Dataset gate |
|---|---:|:---:|
| sift_10k | 0/3 | FAIL |
| glove100_10k | 3/3 | PASS |
| arxiv_nomic_10k | 2/3 | PASS |

Overall passing datasets: 2/3; required: 2/3.

GloVe shows approximately 4.6%–5.1% equal-recall NDC reduction at all three preregistered support points for every seed. Arxiv passes for seeds 17 and 29 with approximately 7.2%–9.9% reductions; seed 7 fails at the 0.95 and highest-common checks. SIFT improves at the low-recall point but fails the high-recall common-support requirement for every seed.

Next action: **CONTINUE_D0_B**.

Machine-readable observed-point selections are in `results/post_e0/d0a/equal_recall_points.csv`; the full frozen decision and input hashes are in `results/post_e0/d0a/decision.json`.

