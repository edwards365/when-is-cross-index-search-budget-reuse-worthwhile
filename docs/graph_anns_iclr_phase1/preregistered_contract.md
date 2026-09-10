# Graph-ANNS ICLR Phase-I preregistered contract

Frozen before any Phase-I scientific run on 2026-09-10 (Asia/Shanghai). Parent: `d2ad714541d73bedcd48580347b67880d37580f8`; branch: `exp/graph_anns_iclr_phase1_decisive_supplement`.

## Scope and firewall

The registered cells are SIFT-100K and Arxiv-Nomic-100K under hnswlib HNSW, Faiss HNSW, and one semantically distinct DiskANN3/Vamana-style implementation. Existing frozen result records may be reanalysed. `validation-dev`, `formal-test`, `future-replication`, HDF5 test members, and historically reserved future query/vector/truth roles remain inaccessible. Any new timing-only query must be assigned `profiling_cost_only`, be content-hash disjoint from design/evaluation/future roles, and may not affect action selection, budgets, risk, or performance claims.

No recovery-algorithm search, CALS/CIBS/GSC/Auditor restart, adaptive operator tuning, or cross-domain expansion is permitted. Old results and manifests are immutable. Historical unrelated untracked directories remain untouched.

## Failure event and workpoints

For query `q`, build `G`, and implementation-native action `a`, `Z(G,a,q)=1` iff per-query Recall@10 is below `tau`, or no safe action is observed within the registered action grid under the frozen endpoint/right-censoring semantics. The primary workpoint is `tau=0.95`; `tau in {0.90,0.99}` are sensitivity analyses and cannot replace the primary result. Missing exact response records imply `NOT_ESTIMABLE`; no interpolation is allowed.

## Budget categories

- `SAFE_FINITE`: a minimum registered-grid action meets the workpoint.
- `RIGHT_CENSORED`: the maximum registered action does not meet it when the record supports that distinction.
- `UNRESOLVED_ENDPOINT`: true infeasibility and finite-grid censoring cannot be separated.
- `INVALID_RECORD`: missing, mapping, or replay failure.

A1 is any categorical change across builds. A2 is numeric diameter only when every build is `SAFE_FINITE`. A3 is numeric diameter among finite actions when at least two builds are `SAFE_FINITE`. A4 is heterogeneity between `SAFE_FINITE` and censored/unresolved states. Bottom states are never encoded as the maximum action in numeric distances.

## Risk inference and certification

`delta=0.05`, familywise `alpha=0.05`. Candidate-family size `M` is reported as actually used; registered comparisons also include M=24 and M=36. Each action receives an independent one-sided Bonferroni–Clopper–Pearson upper bound at `alpha/M`. Raw ef/l_value risk events are not assumed nested. Fixed-sequence and nested-DKW are forbidden absent an independent proof. Query bootstrap uses 5,000 replicates with seed 991 and resamples query IDs while retaining every registered pair belonging to that query. Inference is conditional on the registered finite build family; it is not an unseen-build interval. The 2% transport threshold is a preregistered materiality threshold, not a significance threshold.

For zero failures, the upper bound is `1-(alpha/M)^(1/n)` and the zero-failure sample threshold is `ceil(log(alpha/M)/log(1-delta))`: 59 for M=1, 121 for M=24, and 129 for M=36. Allowed failures for n in `{59,121,129,256,750}` will be computed exactly from the same CP rule and recorded machine-readably before use.

## Phase 1A

Reanalyse the six frozen cells at all registered workpoints, reporting A1–A4, unresolved/right-censored and jointly-feasible mass, reference/absolute/incremental risk, implementation-internal cost, p50/p95/p99, LOBO/LOSO/LOTO, and separate deletion of the highest 1% risk and cost contributors. Stage-specific endpoint estimands and harmonized jointly-feasible sensitivities remain distinct.

## Phase 1B cost protocol

For n=`{59,121,129,256,750}`, measure truth, one-action search, shared-truth candidate family, certification/control, build, serialize/load/integrity, fixed-policy production, and fallback. Each timing configuration has one warm-up and at least five independent repeats. Report mean, median, and p95 under one scientific thread and one preregistered deployment setting. Cold load and resident index are separate; cache state is recorded. Never select the fastest run.

Compare P0 blind source reuse, P1 registered maximum budget/abstention, and P2 per-target certified profiling. P2 is an engineering prescription, not a new algorithm. Report `K0`, per-query net saving `d`, and `N*=K0/d` when d>0; otherwise `NO_FINITE_BREAK_EVEN_WORKLOAD`. Report search-only and measured wall-clock views and amortization at 1e4, 1e5, 1e6, and 1e7 daily queries.

## Phase 1C deterministic rebuild protocol

Canonical order is truth-free stable external-ID order, with content-hash order allowed only if fixed before results. D0 reuses registered random-order controls. D1 is canonical order with varied internal seed (target 8, minimum 6). D2 is canonical order plus fixed seed and normal fixed threading (target 8, minimum 6). D3 adds single-thread execution and frozen toolchain (3 builds; stop once all three are byte-identical). SIFT/hnswlib is mandatory priority; Faiss is secondary if resources and time permit. No Vamana expansion is required.

The actionable Gate requires category variation or transport risk to fall at least 80% relative to D0 or below 5%/2%, Recall loss >= -0.001, mean cost degradation <=3%, p95 degradation <=5%, build-time degradation <=20%, top-1% robustness, and concordant direction on two datasets. D3 states are `BYTE_IDENTICAL`, `SEARCH_IDENTICAL_GRAPH_DIFFERENT`, `SEARCH_DIFFERENT`, or `INVALID_NONREPRODUCIBLE`.

## Resource and stopping rules

Every new-build stage requires at least 20 GiB free after projected additions. At freeze time the root filesystem has only 15 GiB free, so all new D1–D3 builds are blocked until a compliant storage target is verified; Phase 1A and read-only cost-interface audit may continue. No historical data may be deleted to force the Gate. The scientific deadline is 2026-09-15 23:59 Asia/Shanghai. September 16 is artifact-only. Negative evidence is retained and never triggers algorithm search.

## Final labels

Semantic, Economics, and Mitigation use only the registered component labels in the governing prompt. The sole overall decision uses only A–E from that prompt. All three evidence chains are reported independently.
