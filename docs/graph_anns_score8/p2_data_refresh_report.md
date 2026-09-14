# Graph-ANNS Score8 P2 — Data-refresh transfer result

## Decision

`DATA_REFRESH_BREAKS_SOURCE_TRANSFER_BUT_WITHIN_SNAPSHOT_RECOVERS`

The old-snapshot k=9 conformal pool remained below the preregistered 10% operational risk ceiling in all six dataset/refresh cells, including target-build-cluster upper confidence bounds and LOBO. It nevertheless failed the stricter source-to-target transfer Gate: compared with a k=9 pool rebuilt inside the refreshed snapshot, its absolute risk gap exceeded the frozen 2% non-inferiority margin at 5% and 10% refresh on both datasets. Thus the evidence supports safety under this pilot ceiling, but does not support snapshot-invariant conformal transport.

## Key data

| Dataset | Refresh | Old-pool risk (95% cluster upper) | Refreshed-pool risk | Gap | Old mean ef |
|---|---:|---:|---:|---:|---:|
| SIFT-100K | 1% | 4.47% (4.96%) | 4.02% | 0.45 pp | 78.952 |
| SIFT-100K | 5% | 6.56% (7.21%) | 3.58% | 2.98 pp | 78.952 |
| SIFT-100K | 10% | 7.96% (8.62%) | 4.09% | 3.87 pp | 78.952 |
| Arxiv-Nomic-100K | 1% | 4.39% (4.85%) | 3.34% | 1.05 pp | 60.377 |
| Arxiv-Nomic-100K | 5% | 6.04% (6.63%) | 3.67% | 2.37 pp | 60.377 |
| Arxiv-Nomic-100K | 10% | 8.31% (9.00%) | 3.59% | 4.72 pp | 60.377 |

All registered methods have selected-ef p95=200, so the experiment supplies no favorable tail-cost result. The refreshed-snapshot pool is a non-deployable upper bound: it demonstrates that rebuilding the calibration pool can recover the risk profile, not that a deployable adaptive refresh mechanism has been established.

## Evidence and limits

The run used two frozen 100K datasets, three equal delete/insert fractions, ten paired seeds, 1,000 disjoint train-row queries, the fixed ef grid, and target-build outer/query inner bootstrap with 5,000 repetitions and seed 991. Heavy hit tensors and identity ledgers remain under `/home/wlk/data500/graph_anns_score8/data_refresh`; their SHA-256 values are recorded in the decision manifest. The result is exploratory and preregistered, not formal-test evidence.

The initial smoke exposed and corrected a local-row versus persistent-vector-ID truth mapping error before the full matrix. A second post-run semantic patch changes only the precedence of the final label; it does not alter raw tensors, CSV values, seeds, thresholds, or tests.

## Gate consequence

The strict transfer Gate failed, so the external-method comparison stage is not automatically authorized under the sequential protocol. The result instead motivates a narrowly scoped refreshed-snapshot calibration or data-refresh-specific method, subject to a new preregistration.
