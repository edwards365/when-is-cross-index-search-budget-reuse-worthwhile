# Frozen Graph-ANNS Replay

## Scope

The replay uses only the 81 frozen Cross-Index graphs and their 972,000 design-side query-budget rows. A seed-991 hash split fixes 256 labeled sentinels and 744 disjoint evaluation queries per dataset. No graph, truth, query or search result was generated. The evaluated ECSE lane uses exact target sentinel stable-budget labels and per-query source stable-budget responses; it is therefore `LABELED_TARGET_SENTINEL_PLUS_NON_DEPLOYABLE_SOURCE_ORACLE`, not a deployable controller. Exact truth-acquisition effort and real latency are not available (`NOT_ESTIMABLE` and `LATENCY_NOT_ESTIMABLE_FROM_TRACE`).

## Closed world

The target graph remains in the finite environment library. Sentinel matching includes the target in 81/81 sets; ambiguity is one for hnswlib/Faiss and three for Vamana's tied graph responses. On hnswlib, conservative under-budget rates are 0.00060 for SIFT, 0 for Arxiv and 0.0530 for GloVe. The GloVe value is right-censoring at the maximum frozen budget and agrees with Gate E0's absence of a safe endpoint. Search-only NDC savings relative to the fixed endpoint are 49.68%, 49.89% and 67.69%, respectively, but the GloVe saving is infeasible and all three are nondeployable upper bounds.

## Open world leave-one-build-out

Removing the target graph breaks safety. Conservative under-budget rates for hnswlib are 9.32% (SIFT), 19.59% (GloVe) and 7.03% (Arxiv); Faiss HNSW gives 22.83%, 32.41% and 15.71%; Vamana gives 16.89%, 30.51% and 7.62%. Every implementation-by-dataset cell exceeds `delta_q=0.05`. Deleting the top 1% of queries ranked by apparent NDC saving does not repair the mechanism. The failure is consistent with library coverage/response mismatch: a nearest sentinel environment need not safely dominate an unseen target build.

## Cost

The labeled sentinel response uses the complete twelve-budget trajectory for 256 queries. Search-only break-even workloads average roughly 1.5K--20.5K queries depending on implementation/dataset/lane, and at `N=10^5` the closed-world trace-level net NDC savings remain positive. These are lower bounds on total deployment cost because truth acquisition and controller latency are unidentified. Positive cost savings do not override safety failure.

## Gate outcome

G3 is `CLOSED_WORLD_PASS_OPEN_WORLD_FAIL`. G4 fails because no deployable source policy is present, exact labeled target sentinels are charged but not operationally estimated, and open-world risk is above threshold. The unique direction label implied by the frozen evidence is `CLOSED_WORLD_ONLY_NOT_OPEN_WORLD_PORTABLE`.
