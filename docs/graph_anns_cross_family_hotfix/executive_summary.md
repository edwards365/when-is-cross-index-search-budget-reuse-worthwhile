# Executive summary

Final decision: `CROSS_FAMILY_FINAL_HOTFIX_PASS_FREEZE_FOR_PAPER`. Across three registered Graph-ANNS implementations spanning HNSW and Vamana-style construction, independent rebuilds materially change query-level safe budget requirements and induce source-to-target transport violations. The risk-side phenomenon is consistent across all six registered data–operator cells, while its conservative-cost consequence is operator-dependent and is not statistically resolved for the current Vamana-style implementation.

The original endpoint-aware registered estimands are retained, and a separate jointly-feasible sensitivity estimand is added. Vamana checksum discrepancies are reconciled as line-ending-only. The hnswlib final 552-pair estimand passes the exact eight-query top-1% deletion test. No ANN search, index build, sealed query/truth access, or source mutation occurred.
