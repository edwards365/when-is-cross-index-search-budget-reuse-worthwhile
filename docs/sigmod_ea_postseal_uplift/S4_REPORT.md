# S4 Target-Stage Lifecycle and Wall-Clock Boundary

## Decision

`S4_TARGET_STAGE_NDC_LIFECYCLE_GATE_PASSED_FULL_LIFECYCLE_NOT_ESTIMABLE`.

S4 closes the target-acquisition plus serving ledger in native Faiss HNSW distance computations without accessing a new query, truth value, policy, action, or index. It does **not** close the complete cold end-to-end ledger: the historical Faiss response cube used to acquire the source policy has no legal per-query NDC. Exact-truth wall time was also not recorded, so wall-clock remains a descriptive search-only sensitivity rather than a lifecycle or monetary result.

## Frozen accounting

Each target truth set costs `500 × 100,000 = 50,000,000` exact distance computations. Certification adds the measured NDC of the candidate and endpoint on the 500 independent S3 certification queries, deduplicating identical actions. Candidate and endpoint use the same target index, so rebuild and index-load costs cancel. Serving value is the independently measured endpoint NDC minus executed-action NDC from S3; fallback is already embedded in the executed action.

| Dataset | Scenario | Ratio-of-sums break-even (95% target-build bootstrap CI) | Non-amortizing units | First registered positive N |
|---|---|---:|---:|---:|
| SIFT-100K | pairwise target certification | 66,914 [64,805, 69,940] | 460 / 552 directions | 100,000 |
| SIFT-100K | one target audit shared across 23 sources | 3,019 [2,923, 3,157] | 0 / 24 targets | 10,000 |
| Arxiv-Nomic-100K | pairwise target certification | 17,018 [16,767, 17,276] | 230 / 552 directions | 100,000 |
| Arxiv-Nomic-100K | one target audit shared across 23 sources | 755 [744, 767] | 0 / 24 targets | 1,000 |

The many non-amortizing pairwise directions are not failures hidden by averaging: for those directions the one-rung candidate is already the fixed-safe endpoint, so serving saving is exactly zero while an isolated certification job still has positive acquisition cost. The pairwise ratio is therefore a portfolio estimand, not a guarantee for every direction. The shared-target estimand is the operationally relevant registered multi-history audit: one target truth set and each distinct required action are reused across 23 source histories; all 24 targets on both datasets amortize.

At `N=10^6` queries per direction, the pairwise mean net-NDC saving is 772.7M on SIFT (95% CI 736.6M–799.9M) and 3.319B on Arxiv (3.268B–3.372B). Under shared-target certification it is 18.989B on SIFT (18.159B–19.615B) and 77.611B on Arxiv (76.418B–78.811B). Every `N=10^6` bootstrap lower bound, LOBO minimum, and delete-largest-target result is positive.

## Wall-clock boundary

The existing single-thread, CPU-affined, per-query interleaved S3 measurements show positive serving-time savings, but they do not contain exact-truth/control acquisition time. Search-only timing break-even points are 5,760 / 2,458 queries for isolated SIFT / Arxiv directions and 337 / 125 queries for the shared-target scenario. These figures are diagnostic only: `SEARCH_ONLY_EXPLORATORY_FULL_LIFECYCLE_NOT_ESTIMABLE`. They are not promoted to a hardware-general latency, full lifecycle, or monetary claim.

## Verification and next boundary

- 1,104 directed-pair ledger rows, 48 target-build rows, 20 horizon rows, and four dataset-scenario summaries.
- 14/14 fail-closed validation checks pass.
- Both S3 datasets retain independent certification, risk, mean-NDC, p95, and build-robustness passes.
- No new graph, query role, truth access, validation-dev, formal-test, or reserved truth was used.
- S5 is not started and still requires explicit user authorization.
