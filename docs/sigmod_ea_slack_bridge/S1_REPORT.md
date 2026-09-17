# S1 — Boundary Slack and Stable-Tail Reanalysis

## Scope and evidence level

This phase is a preregistered, post-hoc reanalysis of frozen response cubes. It runs no new ANN search and builds no index. The evidence level is `POST_HOC_FROZEN_RESPONSE_REANALYSIS`. The unit of resampling is a shared query with its complete directed build-pair response vector; all confidence intervals use 5,000 bootstrap replicates and seed 991.

The source action is the first frozen action satisfying the source-side response criterion. The registered interventions execute that action, one grid level above it, two grid levels above it, a retrospective stable-tail action, or the endpoint. The historical `+0` values are reproduced exactly.

## Results

| Operator | Dataset | Lane | Incremental target risk | 95% bootstrap interval | Mean NDC | p95 NDC |
|---|---|---:|---:|---:|---:|---:|
| hnswlib | SIFT-100K | +0 | 21.55% | [20.76, 22.33]% | 741.82 | 1,753 |
| hnswlib | SIFT-100K | +1 | 6.83% | [6.18, 7.46]% | 1,070.86 | 2,435 |
| hnswlib | SIFT-100K | +2 | 1.65% | [1.31, 2.00]% | 1,473.86 | 2,723 |
| hnswlib | Arxiv-Nomic-100K | +0 | 17.17% | [16.33, 18.06]% | 677.71 | 1,751 |
| hnswlib | Arxiv-Nomic-100K | +1 | 4.70% | [4.14, 5.24]% | 971.36 | 2,398 |
| hnswlib | Arxiv-Nomic-100K | +2 | 0.83% | [0.61, 1.08]% | 1,372.05 | 3,046 |
| Faiss HNSW | SIFT-100K | +0 | 23.60% | [22.78, 24.39]% | not estimable | not estimable |
| Faiss HNSW | SIFT-100K | +1 | 6.11% | [5.64, 6.62]% | not estimable | not estimable |
| Faiss HNSW | SIFT-100K | +2 | 1.18% | [0.99, 1.39]% | not estimable | not estimable |
| Faiss HNSW | Arxiv-Nomic-100K | +0 | 17.77% | [16.86, 18.68]% | not estimable | not estimable |
| Faiss HNSW | Arxiv-Nomic-100K | +1 | 4.41% | [3.96, 4.87]% | not estimable | not estimable |
| Faiss HNSW | Arxiv-Nomic-100K | +2 | 0.85% | [0.68, 1.02]% | not estimable | not estimable |

One slack level removes 68.30–75.18% of the observed incremental risk, but leaves 4.41–6.83 percentage points. Two levels remove 92.33–95.24%, leaving 0.83–1.65 percentage points; every +2 interval remains above zero. For hnswlib, +2 costs 1.99× and 2.02× the +0 mean NDC on SIFT and Arxiv, respectively, while still using 33.57% and 43.69% less mean NDC than the endpoint. The frozen Faiss response cube does not contain cumulative visited-node cost, so Faiss NDC is correctly reported as `NDC_NOT_ESTIMABLE_BATCH_CUMULATIVE`; requested `ef` is not substituted for NDC.

## Stable-tail diagnostic

The retrospective stable-tail label does not materially improve on the first-passing label. Raw response non-monotonicity occurs for 0.106% of hnswlib SIFT query-build curves and 0% in the other three settings. The stable and first labels are therefore identical almost everywhere, and all finite stable labels are at least as large as the corresponding first label. This rules out response reversals as the main explanation for the transfer failures in these frozen cubes.

## Decision

The registered decision is `SLACK_REDUCES_RISK_ACROSS_SETTINGS`. This is neither a null result nor evidence that transfer is cost-free. The original phenomenon is boundary-sensitive: modest upward movement sharply reduces failure, but one level is insufficient and two levels incur material search cost while retaining a small, statistically resolved residual risk. The defensible paper claim is therefore narrower and more useful: portability failure is concentrated near the source decision boundary, and ICBA exposes the cost–risk frontier needed to decide whether slack, target calibration, or fallback is deployable. This phase does not by itself authorize a fixed universal slack policy.

## Integrity checks

- Frozen `+0` risk reproduced exactly for all four operator–dataset settings.
- 96 raw input files recorded with SHA256.
- 24 target builds and 750 shared queries per setting.
- 50/50 automated semantic and consistency checks passed.
- No W6 manuscript file, frozen result, ANN index, or unrelated worktree file was modified.
