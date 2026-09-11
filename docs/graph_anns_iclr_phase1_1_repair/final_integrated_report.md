# Final integrated report

The repair branch preserves all Phase-1.1 parent outputs. D3 and Vamana are reused read-only; only clean Faiss-100K evaluation queries were searched.

## Clean Faiss-100K h=10

- sift_100k: 24 builds, 552 directed pairs, 750 queries; minimum-safe variation=0.910667; endpoint variation=0.005333; inclusive variation=0.910667; unresolved=0.000722; all-build-feasible=746; at-least-two-feasible=750; diameter means=84.39678284182305 / 85.76; absolute/reference/incremental risk=0.236715/0.000722/0.235993; 95% CI=[0.227802,0.243872]; top-1% deletion=0.234269; LOBO range=[0.235344,0.236598].
- arxiv_nomic_100k: 24 builds, 552 directed pairs, 750 queries; minimum-safe variation=0.758667; endpoint variation=0.018667; inclusive variation=0.758667; unresolved=0.001667; all-build-feasible=736; at-least-two-feasible=750; diameter means=60.108695652173914 / 65.49333333333334; absolute/reference/incremental risk=0.179324/0.001667/0.177657; 95% CI=[0.168570,0.186756]; top-1% deletion=0.175349; LOBO range=[0.177141,0.178211].

## Semantic decisions

- τ mapping is computed as ceil(10τ); .95 and .99 both map to h=10 and are checked from hit counts.
- Endpoint, inclusive action-state and finite-action variation are separate. Diameter uses all-build-feasible and at-least-two-feasible denominators; no zero imputation.
- Historical source-censored primary transport maps to the maximum registered action; composite source-censoring risk is sensitivity only.
- Faiss native `ndis` remains NOT_ESTIMABLE_BATCH_CUMULATIVE; profiling remains primitive-only and break-even SYMBOLIC_ONLY.

## Cross-family conclusion

The registered hnswlib HNSW, clean Faiss HNSW and frozen Vamana-style cells retain positive h=10 transport-risk direction in both datasets. Vamana h=8/h=9 remain NOT_ESTIMABLE_FROM_FROZEN_HIT_COUNTS. No cross-family raw-budget or universal cost-tax equivalence is claimed.

## Final label

`ICLR_PHASE1_1_REPAIR_PASS_CROSS_FAMILY_EVIDENCE_CONFIRMED` (conditional on registered datasets/builds and clean Faiss replay; not an open-world claim).
