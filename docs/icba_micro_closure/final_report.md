# ICBA Finite-Environment Micro-Closure Final Report

## Decision

Unique label: `CLOSED_WORLD_ONLY_NOT_OPEN_WORLD_PORTABLE`.

The sprint forms a valid finite closed-world theory--algorithm micro-closure but does not produce a deployable Graph-ANNS method. It supports continued ICBA v2 theory only if the next work addresses unknown-environment coverage; it does not authorize a C++ controller, new graphs, validation access or a large CPU rental.

## Integrity and scope

The work starts from `exp/icba_theory_lock@ed8d1e0d84c075fddbbc4d8aa5e77a57683a2fb6` in the independent `exp/icba_micro_closure` worktree. The old complete bundle lacked the frozen head, so a verified incremental bundle was created before analysis. All empirical inputs are the frozen 81 graphs and 972,000 design-side rows; no graph, query, truth or search was generated. `validation-dev` and `formal-test` were not accessed. Exact free disk remained below 10 GiB, so large intermediates and the optional query-failure Parquet were not materialized.

## Endpoint safety

All 81 graph files have complete twelve-budget grids and protocol-consistent rows. Of them, 54 are certifiably safe, 17 are grid-right-censored and 10 have no practical safe endpoint. hnswlib is safe on SIFT and Arxiv (18/18 graphs) but on no GloVe graph (0/9). GloVe maximum-grid empirical failure is 4.5%--5.5% for hnswlib and the one-sided confidence bound remains above the 5% risk target. The previous fixed fallback failed 32/256 calibration and 45/256 design queries. Gate E0 therefore passes only with a dataset boundary.

## Lower bound

For two environments on a common visible state space with deterministic aligned sufficient-budget responses, the proved bound is

`inf_pi sup_theta E loss >= (min{lambda,1} Delta/2)[rho-TV(P0^Z,P1^Z)]_+`.

It is nontrivial under positive overlap and budget separation, and vanishes at perfect visible identification, zero gap or zero separated mass. Randomized policies are covered by the pointwise inequality. The result excludes unaligned response histograms and unidentified right-censored labels. Eight test families cover state counts 2--8, budget levels 2--6, randomized mixtures, TV endpoints, nonmonotonicity and censoring. G1 passes only as `PASS_RESTRICTED_ALIGNED_RESPONSE_CLASS`.

## Constructive upper bound

ECSE builds a nested confidence set over a finite environment library and executes the maximum frozen budget response in that set, failing closed to a separately certified endpoint. With true-environment coverage at least `1-alpha` and a target response whose query risk is at most `delta_q`, ECSE has query risk at most `delta_q` with sentinel-sampling probability at least `1-alpha`. Nested sets make execution envelopes nonincreasing, but acquisition-adjusted total cost need not decrease. The cost gap separates environment miss, confidence-set diameter, fallback and acquisition work.

In the two-environment `p=0` versus `p=1` sentinel class, eight probes identify the target exactly. Across 24 positive-gap main cells, identification error, under-budget risk and execution overcost are all zero; ambiguity is one and probe-adjusted cost at `N=10^5` is `1.6e-7`. The lower bound is 50%--100% of exact source minimax loss (mean 86.81%). G2 passes as `PASS_FINITE_CLOSED_WORLD_CLASS`. A discovered boundary is retained: with zero budget gap, migration tax is zero but rare empty-set fallback can still create certification cost, so total overhead need not vanish.

## Synthetic grid

The deterministic grid contains 1,152 bound cells and 37,632 ECSE cells over K={2,4,8}, L={2,3,4,6}, gap steps {0,1,2,4}, sentinel separations, k={0,8,16,32,64,128,256}, delta_q={0.01,0.05,0.10} and alpha={0.01,0.05}. The source lower bound is positive in 864 cells; its ratio to nonzero exact minimax is 0.5--1.0. Under the main alpha=delta_q=0.05, every ECSE cell is safe and the maximum under-budget risk is 0.00913. Ambiguity has no monotonicity violations across 5,376 fixed configuration-target paths.

## Graph-ANNS replay

The seed-991 split fixes 256 labeled sentinels and 744 disjoint evaluation queries per dataset. In closed world, target graphs are recovered in all 81 cases. hnswlib conservative under-budget rates are 0.00060 for SIFT, 0 for Arxiv and 0.0530 for GloVe; trace-level NDC savings against fixed endpoints are 49.68%, 49.89% and 67.69%. GloVe is infeasible and all savings are nondeployable upper bounds because this lane uses labeled target sentinels and per-query source Oracle responses.

Open-world leave-one-build-out fails: hnswlib under-budget rates are 9.32%, 19.59% and 7.03% for SIFT, GloVe and Arxiv; Faiss gives 22.83%, 32.41% and 15.71%; Vamana gives 16.89%, 30.51% and 7.62%. Every cell exceeds 5%, and deleting the highest-savings 1% of queries does not repair safety. Search-only break-even is roughly 1.5K--20.5K queries, but truth acquisition and latency are not estimable; cost savings cannot override unsafe transfer.

## Unified Gates

- G0: `PASS_WITH_DATASET_BOUNDARY`.
- G1: `PASS_RESTRICTED_ALIGNED_RESPONSE_CLASS`.
- G2: `PASS_FINITE_CLOSED_WORLD_CLASS`.
- G3: `CLOSED_WORLD_PASS_OPEN_WORLD_FAIL`.
- G4: `FAIL` because no deployable source policy is available and open-world safety fails.

## Answers and next action

The safe endpoint is feasible only for SIFT and Arxiv; the fixed fallback failed because the maximum/fallback budget is not safe on GloVe. The source-only bound is nontrivial and depends on visible-state TV and aligned budget separation. ECSE has a finite-sample closed-world upper bound and exactly matches a natural separable class, but not unknown builds. Target sentinels have high closed-world Oracle value; their search cost amortizes by about 20.5K queries in the slowest observed cell, while truth and latency remain unknown. Closed/open-world performance differs qualitatively. No deployable source policy exists in the frozen evidence. hnswlib is the primary operational instance; Faiss/Vamana reinforce the boundary.

ICBA is worth a narrowly scoped v2 theoretical extension to hierarchical or robust unknown-environment coverage, not a broad claim of general AI universality. Algorithm implementation is not authorized. Renting a CPU server is not justified before an open-world safe-dominance theorem and deployable source response exist. A small non-ANNS finite-environment example may be useful only after that theorem is specified; no broad new empirical matrix is recommended now.
