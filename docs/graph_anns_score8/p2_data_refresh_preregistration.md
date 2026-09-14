# Graph-ANNS Score8 P2 — Data-refresh transfer preregistration

This stage tests an unmeasured premise in the paper motivation: whether a build-pool budget learned on an old graph snapshot transports through a fixed-size delete/insert refresh and rebuild. It is not an algorithm search. The registered matrix is SIFT-100K and Arxiv-Nomic-100K, refresh fractions 1%, 5%, and 10%, ten paired build seeds, 1,000 new query vectors disjoint from base and insertion candidates, and the fixed ef grid 10/20/40/80/120/200.

The deployable comparison is old-snapshot k=9 conformal transport against fixed ef=200 and single-build reuse. A k=9 conformal pool rebuilt on the refreshed snapshot is reported only as a non-deployable upper bound on recovery. BOT is positive infinity and causes an explicit abstention to ef=200. Exact truth is recomputed for each refreshed snapshot from the frozen query set.

The primary unit is the held-out target build. Risk and cost summaries use target-build outer/query inner bootstrap with 5,000 repetitions and seed 991, plus LOBO and deletion of the largest-contribution build. The strict Gate requires safety, tail control, robustness, and old-to-refreshed transfer non-inferiority as frozen in the JSON manifest. Failure of the strict Gate may still support a narrower safety-only or within-snapshot-recovery conclusion; it cannot be promoted to a broad transport claim.

All index and per-query material is written under `/home/wlk/data500/graph_anns_score8/data_refresh`. The main repository receives only code, the frozen protocol, compact summaries, tests, and checksums. No independent Codex task or Git worktree is permitted.
