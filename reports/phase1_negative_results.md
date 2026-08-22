# Phase I negative results

All negative results remain part of the project record.

1. Aggressive full reselection degraded matched-ef recall and cost relative to Original; resistance-only was worst among the main repair variants in the first smoke test.
2. Scheme A is strongly locality-correlated and recovers only 42.47% of Algorithm 4's accepted set at a matched local budget.
3. Scheme B under-enriches cross-cloud rejected edges: 20.70% rejected-set baseline versus 7.42% top-1 and below 4.7% top-5/top-10.
4. Scheme B has only weak association with progressive trace support (`Spearman=0.1458`), and a navigation-supported edge can rank as low as 67.
5. On the formal independent holdout, Trace+Resistance does not improve Recall@10 at `ef=10`: difference `-0.000390625`, interval `[-0.00107421875,0.00029296875]`.
6. Resistance-only also does not improve recall. Its small NDC reduction is not unique because Geometry reduces NDC more in point estimate.
7. The base-identity perturbation evaluation produced a false optimistic impression and was invalidated for leakage before Phase I closure.

These results do not prove that every possible resistance-aware ANN method must fail. They do reject the tested claims that resistance directly predicts navigation value or that the Phase I interventions are improved HNSW methods.
