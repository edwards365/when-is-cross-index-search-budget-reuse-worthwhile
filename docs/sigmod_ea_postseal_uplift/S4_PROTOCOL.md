# S4 Protocol — Target-Stage Lifecycle and Wall-Clock Boundary

S4 begins only after the independent S3 certification, evaluation-risk, mean-NDC, p95, and build-robustness gates pass. It reuses the frozen S3 raw counters and makes no new query, truth, policy, action, or index access.

The primary currency is Faiss HNSW native distance computations (NDC). For each source–target direction, target acquisition contains 500 exact labels at 100,000 base distances each plus the measured certification searches for the candidate and endpoint; identical actions are deduplicated. Rebuild and index-loading work cancel because the deployed candidate and fixed-safe endpoint use the same target index. Serving value is endpoint evaluation NDC minus executed-action evaluation NDC; fallback is already represented by the executed action.

Two estimands are frozen: `PAIRWISE_TARGET_CERTIFICATION`, which charges a separate target truth/certification job to each direction, and `SHARED_TARGET_CERTIFICATION_23_SOURCES`, which reuses one target truth set and each unique required action across the 23 registered source policies. The latter is a registered multi-history audit, not an assumption of free certification.

Report N in `{1e3,1e4,1e5,1e6,1e7}`, target-build cluster bootstrap with 5,000 replicates and seed 991, LOBO, and deletion of the largest-net-saving target build. The target-stage NDC gate requires both datasets to have positive bootstrap lower bound, LOBO minimum, and deletion check at N=1e6.

The historical Faiss cube used to acquire the source policy has no legal per-query NDC, so source-policy acquisition is `NOT_ESTIMABLE`, never zero. Consequently S4 may close target-stage lifecycle NDC but cannot claim complete cold end-to-end lifecycle economics. S3 interleaved wall time may support descriptive search-only timing; exact-truth/control wall time is absent, so full wall-clock lifecycle and monetary claims remain out of scope.
