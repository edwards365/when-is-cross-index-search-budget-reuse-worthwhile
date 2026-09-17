# S3 Frozen Protocol — Unchanged-Data Source-Policy Bridge

Registered after the S2 result commit and before producing S3 tables.

## Evidence status and role limitation

This phase replays the already frozen 750-query response cubes. Those query outcomes have been inspected in earlier project stages, so the phase is unconditionally labeled `POST_HOC_ROLE_LIMITED`; the deterministic split below prevents within-analysis target leakage but does not create prospective or independent evidence.

Using `default_rng(991).permutation(750)`, the first 375 IDs form `source_certification`, the next 94 form an unused `bridge_holdout`, and the final 281 form `target_evaluation`. The ID lists and hashes are frozen before result production. Target evaluation cannot select a source action, grid, shift, threshold, fallback, or dataset-specific rule.

## Source policy

For every source build independently, candidate policies are the six native fixed actions in the registered operator grid. On the 375 source-certification queries, compute a one-sided Clopper–Pearson upper bound with Bonferroni allocation `alpha/6`, where `alpha=delta=0.05`. Select the lowest action whose upper bound is at most 0.05. If none qualifies, deploy the endpoint and record `NO_SOURCE_QUALIFIED_ACTION_ENDPOINT_FALLBACK`.

The selected action is frozen before target evaluation. The registered comparison lanes are selected `+0`, `+1`, `+2` grid levels (clamped at endpoint), and the endpoint. No target truth is used to select any lane.

## Outputs and statistics

For each directed source–target pair and lane, report selected and executed actions, source certification failures and upper bound, target-evaluation failures, risk, one-sided 95% evaluation interval/state, and legal cost. hnswlib reports stored NDC mean/p95; Faiss remains `NDC_NOT_ESTIMABLE_BATCH_CUMULATIVE` because the frozen cube lacks cumulative per-query work.

Aggregate using the target-evaluation query as the bootstrap cluster while retaining its full directed-pair vector: 5,000 repetitions, seed 991. Also report LOBO and deletion of the largest-contribution 1% of evaluation queries. The 552 directed pairs are not independent build replicates.

## Gate

S3 passes as a mechanism bridge if roles are disjoint, source decisions are invariant to target outcomes, every action is a native registered action or endpoint fallback, cost semantics are legal, and results reproduce from the frozen input hashes. Passing does not upgrade the evidence beyond `POST_HOC_ROLE_LIMITED`.
