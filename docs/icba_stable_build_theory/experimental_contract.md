# Frozen experimental contract for the stable-build pilot

This contract authorizes a future pilot only. It does not authorize access to validation-dev/formal-test, modification of frozen results, or use of evaluation truth during construction.

## Implementations

- **Primary:** Stabilize-then-Certify with critical-path/frontier repair.
- **Fallback:** Consensus-Stabilized Construction with explicitly protected registered bridges.
- **Required baselines:** original hnswlib; canonical deterministic order/seed; Best-of-R comparator if its truth cost is counted.
- **External comparison after pilot Gate:** Faiss HNSW or Vamana, not both in the two-day pilot.

## Pilot units

- Datasets: SIFT-100K and Arxiv-Nomic-100K.
- Index: hnswlib.
- Per dataset: at least 3 standard and 3 stable builds.
- Query roles: design, calibration, certification and evaluation are mutually disjoint by query ID; evaluation truth is sealed until the algorithm and Gates are frozen.
- Budget grid: 12 preregistered levels with exact action semantics.
- Seeds/orders: registered; standard builds vary legitimate construction environments, while canonical baseline fixes them.
- No GloVe, validation-dev or formal-test.

## Observable chain

| Link | Observable | Statistic | Pass condition |
|---|---|---|---|
| construction -> structure | edge/path/frontier logs | critical-edge retention, path overlap, entry reachability, intruder count | direction agrees on both datasets; no connectivity/degree violation |
| structure -> budget | independent calibration queries | one-sided exceedance `Pr(B_t>B_s+m)` and calibrated `d_phi -> d_B` curve | registered upper bound improves; endpoint infeasibility does not worsen |
| budget -> risk | certification queries | simultaneous one-sided risk UCB | at least one nontrivial action certifies at `delta,alpha` |
| risk -> cost | build/evidence/search/fallback accounting | total mean cost, query-pooled p95, `N*` | finite break-even and no mean/p95 regression |

## Required metrics

Recall@10; endpoint feasibility; right-censor count; `B_G(q)`; budget-change rate; rank inversion; mean/quantile/sup response diameter; edge overlap; path overlap; critical-edge retention; entry-point reachability; frontier intruders; mean NDC; query-pooled p95 NDC; build time; peak memory; index size; certification sample size; acceptance/fallback rate; truth acquisition; total cost; break-even workload; top-1% build-deletion robustness.

## Gates

1. Recall non-inferiority: `Delta Recall@10 >= -0.001` with a declared uncertainty procedure.
2. Response diameter decreases at least 20% on both datasets.
3. Fixed protocol open-world-style held-build under-budget risk decreases; no claim beyond sampled build support.
4. Certification sample need or fallback rate decreases at least 20%.
5. Mean NDC does not worsen.
6. Query-pooled p95 NDC does not worsen.
7. Build/evidence/control cost yields finite `N*` for a declared service scale.
8. SIFT and Arxiv directions agree.
9. Leave-one-build-out and removal of the highest-contribution build preserve direction.
10. No evaluation query or truth affects construction, ordering, repair, calibration or threshold selection.

Any failed Gate is recorded; definitions and thresholds are not changed after evaluation.

## Assumption contract

| ID | Theorem | Field/statistic | Pass | Failure meaning |
|---|---|---|---|---|
| A_UPWARD_SAFE_SET | T-SC2 | per-query recall across 12 budgets | zero registered monotonicity violations or use a monotone success envelope | T-SC2 raw-action proof invalid |
| A_ENDPOINT_FEASIBLE | T-SC2/T-SC4 | endpoint status | useful candidate has declared feasible scope | abstain/censor; do not impute max budget |
| A_TRACE_CERTIFICATE | T-SC5/T-SC10 | retained trace edges/nodes/keys | registered certificate premises pass | structural-to-budget theorem unavailable |
| A_FRONTIER_INTRUDERS_BOUNDED | T-SC5 | intruder count | calibrated one-sided bound | no finite structural budget shift |
| A_BUILD_INDEPENDENCE | T-SC6/outer build | build IDs and construction mechanism | build is resampling unit | query bootstrap cannot support build claim |
| A_POSITIVE_EFFECTIVE_MARGIN | T-SC4 | risk bound and shift allowance | `gamma_eff>0` | no finite margin-based gain |
| A_FIXED_TARGET_INDEPENDENCE | T-SC4 | role manifest/query IDs | zero overlap | selected-policy certificate invalid |
| A_POSITIVE_NET_GAIN | T-SC8 | compatible-unit cost ledger | denominator positive | `NO_FINITE_BREAK_EVEN_WORKLOAD` |

## Tail protocol

NDC p95 is computed from pooled evaluation queries within a build and summarized at the build level; build uncertainty resamples builds, not queries masquerading as builds. Wall time requires pinned hardware, warm-up, concurrency and cache policy. No p95 conclusion is inferred from a mean identity.

## Stop conditions

Stop the route if the surrogate calibration is nonmonotone/unstable, recall or endpoint feasibility fails, no candidate certifies, p95 worsens, or the break-even denominator is nonpositive. Return canonical baseline/fixed-safe/retrain according to the preregistered decision, not an oracle action.
