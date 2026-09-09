# P2 build-level power analysis

P2 is a prospective design Gate. It does not require the future 18–24-build matrix to exist before authorization. Variance is estimated from the pinned historical hnswlib matrix at `6a8cbcf7cf9f8f2f6734b05132e13d0f21e476bb`, which contains nine target-build units per primary dataset (three construction seeds × three registered histories). Historical query outcomes are used only to estimate build residuals; current `confirmatory_query` and `future_replication` roles remain unopened.

The frozen estimand is target-build mean cross-order normalized transfer regret minus mean same-order normalized transfer regret. The minimum scientifically meaningful effect is `0.05`, inherited from the historical portability Gate. Power uses a two-sided one-sample t rejection rule at alpha `0.05` with 5,000 empirical residual-bootstrap studies (seed 991 family). Each leave-one-target-build-out sensitivity repeats the complete power calculation.

| Dataset | Historical units | Mean | SD | Power at 18 | LOTO minimum | Power at 24 | LOTO minimum |
|---|---:|---:|---:|---:|---:|---:|---:|
| SIFT-100K | 9 | 0.1536 | 0.0703 | 91.5% | 85.7% | 98.5% | 95.7% |
| Arxiv-Nomic-100K | 9 | 0.1127 | 0.0650 | 89.1% | 84.9% | 96.7% | 94.7% |

Both planned sample sizes exceed 80% estimated power on both primary datasets, including the minimum leave-one-build-out sensitivity. P2 therefore passes through the preregistered power route. This is design evidence, not an E4 empirical result, and it does not authorize query access while P3 remains conditional.
