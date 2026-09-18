# S9-3 Prospective Fixed-Slack Robustness Report

## Decision

`PRIMARY_REGISTERED_CONFIGURATION_PASS_WITH_PREREGISTERED_BOUNDARIES`

S9-3 prospectively confirms the fixed-slack route on two fresh eight-build panels under the registered six-level grid and 5% risk limit. It does **not** establish grid-invariant or stricter-risk-limit economic value: the preregistered sparse grid and 2.5% risk limit safely collapse to the endpoint and therefore yield no savings. S9-3 also does not close the still-open TCP target-global runtime or complete lifecycle-ledger estimands from S9-2.

## Frozen design and integrity

- Datasets: SIFT-100K and Arxiv-Nomic-100K.
- New units: eight insertion-permutation target builds per dataset, seeds 6011, 6211, 6421, 6637, 6841, 7057, 7273, and 7481.
- Query roles: 500 source-design, 500 target-certification, and 500 target-evaluation queries per dataset; all role overlaps and known prior-role overlaps are zero.
- Policy: the first source action whose one-sided Clopper--Pearson UCB is at most 5% with Bonferroni alpha 0.05/6; the candidate is one registered rung higher; candidate and endpoint receive separate target certification at alpha 0.025.
- Runtime: fixed CPU 2, one search thread, 50 warmups per action, seven query-level interleaved repetitions.
- Evidence cube: 144,000 native response cells and 112,000 raw runtime measurements. All 16 indexes replay with identical top-10 and NDC, and all 16,000 runtime/action/query top-10 comparisons match the native response cube.
- Faiss 1.8.0 records HNSW base-layer distance work in `hnsw_stats.n3`; `ndis` is unused by this path and remains zero. This implementation fact was caught before sealing and the response cube was regenerated without changing indexes, roles, actions, or thresholds.

## Primary scientific results

| Dataset | Decisions | Accepted / fallback / abstain | Evaluation risk (95% crossed CI) | NDC gain (95% crossed CI) | Wall-time gain (95% crossed CI) | p95 wall ratio (95% crossed CI) |
|---|---:|---:|---:|---:|---:|---:|
| SIFT-100K | 56 | 56 / 0 / 0 | 0.475% [0.125%, 0.950%] | 49.775% [49.708%, 49.842%] | 51.354% [50.866%, 51.844%] | 0.519 [0.509, 0.528] |
| Arxiv-Nomic-100K | 56 | 56 / 0 / 0 | 0.536% [0.146%, 1.068%] | 37.427% [35.632%, 39.273%] | 30.128% [28.638%, 31.881%] | 0.891 [0.855, 0.917] |

All intervals use 5,000 crossed target-build by query-ID bootstrap replicates with seed 991 while preserving all source directions within a sampled target/query cell. The 56 directions per dataset are not treated as 56 independent builds.

## Robustness and tail checks

- Leave-one-target-out minimum wall-time gain is 51.191% on SIFT and 29.490% on Arxiv.
- The largest leave-one-target-out p95 ratio is 0.522 on SIFT and 0.899 on Arxiv.
- After deleting the 1% query IDs with the largest aggregate wall-time benefit, gain remains 51.307% on SIFT and 30.088% on Arxiv.
- p99 wall ratios are 0.520 on SIFT and 0.937 on Arxiv.
- Median/max action-block CV is 1.011%/1.526% on SIFT and 0.309%/0.646% on Arxiv, below the preregistered 5%/10% limits.
- Every primary safety, mean-wall, p95, leave-one-target-out, and timing-stability gate passes on both datasets.

## Preregistered sensitivity boundaries

The primary six-level grid at the 5% risk limit retains the gains above. Two preregistered alternatives are safe but economically null:

1. On the sparse grid `(16, 64, 256, 512)`, the one-rung rule advances a selected 256 action directly to the 512 endpoint, giving zero gain.
2. At the 2.5% risk limit, the stricter source/certification rule likewise resolves to the endpoint on both datasets, giving zero gain.

The upper grid `(32, 64, 128, 256, 512)` at 5% reproduces the primary decision because action 16 is not selected. These outcomes delimit the mechanism: fixed-slack recovery is prospectively supported when the registered action grid leaves a non-endpoint certified rung, not as an invariant property of every grid or risk tolerance.

## Gate table

| Gate | SIFT | Arxiv | Result |
|---|---:|---:|---|
| Evaluation risk crossed-CI upper <= 5% | 0.950% | 1.068% | PASS |
| Mean wall-gain CI lower > 0 | 50.866% | 28.638% | PASS |
| p95 wall-ratio CI upper <= 1.05 | 0.528 | 0.917 | PASS |
| Leave-one-target-out wall gain > 0 | 51.191% | 29.490% | PASS |
| Timing median/max CV <= 5%/10% | 1.011%/1.526% | 0.309%/0.646% | PASS |

## Scope

This is prospective evidence on fresh queries and fresh insertion-permutation builds in the frozen DARTH/Faiss HNSW 1.8.0 environment. It is not a campaign-wide simultaneous certificate, a second hardware replication, a proof of grid invariance, a complete lifecycle-economic result, or evidence for the open TCP target-global runtime estimand. The correct paper claim is conditional but strong: under a registered grid with recoverable non-endpoint slack, independent target certification preserves low risk and yields positive mean and tail wall-time gains across both fresh build panels.
