# S4 Frozen Protocol — Fresh-Query Confirmation and Cost Closure

Registered after S1–S3 passed their input, semantic, and mechanism-bridge Gates and before accessing any future-replication vector or truth.

## Fresh roles

The pre-existing E4 role manifest contains 1,000 `future_replication_ids` per dataset, content-disjoint from historical design, confirmatory sentinel, and confirmatory evaluation roles. Every audited decision file records `future_replication_accessed=false`; no contrary access record was found. In the already frozen list order, IDs 0–499 become `fresh_source_certification` and IDs 500–999 become `fresh_target_evaluation`. The exact lists, hashes, action rules, index inventory, and input hashes are sealed in `s4_fresh_preregistration.json` before vector or truth access.

## Fixed actions and certification

For each source build, the S3 source-selected action is frozen. The three registered candidate lanes are that action at +0, +1, and +2 grid levels, clamped at endpoint. Each lane is evaluated as a separate fixed estimand. On the 500 fresh source-certification queries, its one-sided Clopper–Pearson candidate UCB uses `alpha=0.025`; the endpoint UCB uses `alpha=0.025`. A candidate is deployable only when both its own and the endpoint UCB are at most `delta=0.05`; otherwise the lane uses the certified endpoint. If the endpoint itself does not qualify, the source is `NO_CERTIFIED_ACTION`. Target evaluation cannot change actions, thresholds, or fallback.

The retrospective per-query stable-tail action is recorded as `NON_DEPLOYABLE_TRUTH_DEPENDENT` and is not used as an input to deployment.

## Search and truth

- Reuse only the 24 existing hnswlib and 24 existing Faiss HNSW indexes per dataset; do not construct or mutate an index.
- Read query vectors only from the frozen future IDs. Exact top-10 truth is computed against the same 100,000-vector base used by the indexes.
- Run only the six registered native actions. Record per-query Recall@10 and legal cumulative distance computations. hnswlib uses a counting distance-space replay executable; Faiss uses its HNSW distance-statistics counter. Requested `ef` is never substituted for NDC.
- SIFT uses L2. Arxiv-Nomic uses normalized vectors and inner product, matching the frozen index contract.

## Statistics and stopping

Report each implementation and dataset separately. Primary intervals resample the 500 target-evaluation query IDs with their complete directed-pair vector, 5,000 times with seed 991. Also report per-build results, LOBO, deletion of the largest-contribution 1% queries, mean/p95/p99 NDC, and cost relative to endpoint. The 552 directed pairs are not independent builds. Wall-clock is descriptive only.

Stop immediately on any index hash mismatch, query-role overlap, missing input, truth mismatch, illegal action, absent per-query NDC, or replay divergence. Negative results are retained. No W6 manuscript edit is authorized.
