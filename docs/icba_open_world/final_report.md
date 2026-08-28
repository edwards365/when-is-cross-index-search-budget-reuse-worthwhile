# ICBA open-world final report

## Decision

`OPEN_WORLD_IMPOSSIBILITY_SUPPORTED_STRUCTURE_UNRESOLVED`

Frozen inputs reproduce exactly: 81 graphs, 972000 query-budget rows, 648 directed build pairs and 123/123 hashes. Endpoint strata are 54 certified feasible, 17 right-censored and 10 without a practical safe endpoint. GloVe is not used to claim migration failure because all 27 GloVe graphs fail endpoint certification.

On feasible SIFT/Arxiv builds, formal 5000-replicate build-cluster bootstrap intervals remain above delta_q=0.05 for every implementation. Increasing labeled sentinels from 32 to 256 does not approach safety. Historical-library growth helps hnswlib but leaves every observed maximum-library risk above 0.05. Z0 admits empirical collisions; common Z1 is absent. The frozen successful lane depends on labeled target information and a per-query source Oracle and is not deployable.

T-OW0 and T-OW2 are formally complete. T-OW1 is a restricted two-environment finite-grid proposition. T-OW3 is a restricted event union bound, T-OW4 is refuted for current Z0/Z1, and T-OW5 is a proof sketch. The project should prioritize the no-structure boundary paper and should not start algorithm design or access sealed data. Unsupported support/OOD and Z1 figures are deliberately omitted rather than populated with proxy or duplicated plots; their tables are marked NOT_ESTIMABLE.
