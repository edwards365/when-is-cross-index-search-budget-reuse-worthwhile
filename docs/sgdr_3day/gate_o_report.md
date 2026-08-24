# SGDR Gate O report

Decision: `FAIL_ORACLE_UPPER_BOUND`.

The complete-policy query oracle passed strongly, but the identifiable additive-edge
stage experiment did not convert that heterogeneity into navigation savings. The exact
matrix contains 9 dataset×seed runs and 297,000 paired query-mode-ef rows. Every
Original reconstruction matched frozen E0 edges and mappings, every custom Original
search matched native HNSW query-by-query, and all temporary indexes were deleted.

No preregistered fixed scale or depth mode passed even one dataset in two of three
seeds under the joint fixed-ef Recall margin and NDC/p95 improvement rule. Modes with
thresholds high enough to preserve behavior simply converged to Original and produced
approximately zero benefit. Modes that actually inspected more delta edges increased
distance computations. `Union-All` preserved mean Recall but increased mean NDC by
2.616% on SIFT, 2.880% on GloVe, and 2.445% on Arxiv-Nomic.

Thus the Original/R4 query oracle signal is not realizable by the frozen 10% additive
R4-delta scale/depth mechanism. SGDR implementation, E1, and BEP remain unauthorized.
The project now follows the preregistered negative branch
`STOP_ALGORITHM_PIVOT_TO_BOUNDARY_STUDY`; remaining work is evidence packaging,
formal boundary statements, Pareto summaries, and the primary-source novelty matrix.
No validation-dev or formal-test member was accessed.
