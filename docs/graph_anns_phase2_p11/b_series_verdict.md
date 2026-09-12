# P11-B verdict — decisive online head-to-head (cold queries, SIFT-1M workload)

## Setup (pre-stated before the run, see phase_report step 3)

24 registered E4 hnswlib builds rebuilt on SIFT-100K (single-thread, 13.5-14.2 s each);
fresh workload = 500 SIFT-1M test queries, disjoint from every registered role
(forensics gate PASS). Brute-force exact top-10 per query (base fixed across builds).
Per-build offline labeling cost measured: ~0.13 s per build for the whole 500-query
workload (6 ef levels) + brute-force truth.

## Results (24 targets, mean over targets)

| Route | Cold-query serving cost | Risk (fresh queries) | Certify |
|---|---|---|---|
| M1 naive transport (random source) | 1 search | **22.9%** | none |
| M2 pooled replay, COLD query | **1.73 s graded / 17.1 s upper** (23 source searches) | deployable 0.96%, overall 1.68% (abstain 3.9%) | no |
| M2 pooled replay, REPEAT query (cache hit) | ~1 search at pooled action | 0.18-2.5% (registered) | no |
| M3 profile+certify max (m=59) | 0.13 s labeling/target | = M5 when passed | **pass 0.61 mean (0.54-0.73)** |
| M5 always max | 1 search (276 us p95) | 0.82% | no |
| Contract (D3) | 12.9 s build (100K reg.) | 0 | by replay identity |
| Oracle | --- | 0.82% (= endpoint mass) | reference |

## Pre-stated win condition: FAILED -> pivot executed

"Online-M2 achieves risk <= 1% overall with >= 90% coverage at DistComp <= 2x" — for
cold queries the coverage of any label cache is 0% and the source-search cost is
1.73 s/query (graded; 6,300x the always-max search). M2 is NOT a cold-query service.
The pivot per the pre-registered exit clause: pooling is a **repeat-traffic optimizer**,
not a standalone mitigation.

## The decision rule, now fully measured

1. Cold/repeat mix at 100K: naive transport fails (22.9%); ALWAYS-MAX is itself safe
   (0.82% < delta) at 276 us p95; pooling buys 3x DistComp over max on the repeat
   fraction only (A3 rho-sweep: effective risk interpolates 1.26% -> 0.09% as coverage
   goes 0 -> 1).
2. Certification at practical sample sizes certifies only the max budget and fails
   39-46% of the time; it adds no deployable action beyond max.
3. The deterministic contract is the only zero-risk route and its 1M build time is
   measured (252 s median).

So the paper's practical claim sharpens to: **at 100K, the cheap fix for rebuild risk is
"never transport blindly; fall back to max or pin the order" — pooling and certification
are refinements, not the headline.** At 1M/10M the max-fallback risk (0.8-1.3% at 1M;
10M pending) remains under delta, and the scale-dependent pooling boundary (10.4% at
k=7/1M) rules pooling out as the primary mitigation at scale.

## Files

online_head_to_head.csv/.npz/.json (records incl. per-(build,q,ef) hits+latency),
b1_cold_cost.json. Tests: added to test_p11.py in the final P11 commit.
