# ICBA Micro-Closure Input Audit

## Integrity and recovery

- Status: `PHASE0_PARTIAL_PAUSED_DISK_BELOW_10_GIB`.
- Frozen base: `exp/icba_theory_lock@ed8d1e0d84c075fddbbc4d8aa5e77a57683a2fb6`.
- Independent worktree: `/home/wlk/projects/navigation-aware-resistance-hnsw-icba-micro`, branch `exp/icba_micro_closure`.
- The worktree was clean when opened. Existing evidence remains read-only.
- The old complete bundle stops at `b374e9b`; the verified incremental bundle containing `ed8d1e0` is `/home/wlk/projects/icba_theory_lock_ed8d1e0_incremental.bundle`, SHA256 `336dd347bbbab343bd83b7bad877cf2ae5b056780ab5e37a50431eb444dbe124`, with prerequisite commit `b374e9b788eb572f59b826e8b5c9532e44a5129a`.
- Exact free space at the first audit was `10233819136` bytes (9.53 GiB), below the 10 GiB protocol threshold. Bulk endpoint tables, Parquet materialization, synthetic sweeps and replay are paused. No frozen evidence was deleted.

## Locked problem definition

- Safety quality threshold: Recall@10 `>= 0.9`.
- Frozen Cross-Index budget grid: `{10,16,24,32,48,64,96,128,192,256,384,512}`; maximum observed budget is `512`.
- Stable sufficient budget: the least observed budget whose entire remaining frozen-grid tail reaches the threshold.
- Cost: native exact distance computations (NDC), interpreted within implementation; raw NDC is not pooled across implementations.
- Primary query risk: marginal under-budget probability. Pointwise safety and conditional safety remain distinct claims.
- Right censoring: a query that has no stable sufficient budget by 512 is not known safe at 512; its observed cost is a clipped lower bound.
- Frozen master seed for this phase: `991`; principal `alpha=delta_q=0.05`.

## Endpoint and policy answers

- **Fixed endpoint:** the endpoint must be established graph-by-graph by Phase 1. The prior RCRS `fixed_e0_fallback` is not a valid safe endpoint: on GloVe it failed 32/256 calibration queries and 45/256 design-evaluation queries (12.500% and 17.578%). It therefore cannot certify `delta_q=0.05`.
- **Maximum endpoint:** ef=512 on the frozen Cross-Index grid; it is only an observed candidate and cannot be declared safe for right-censored queries.
- **Source policy:** the unified prior analysis uses each query's frozen source stable budget as its source summary.
- **Deployability:** that source stable-budget summary requires per-query source truth/Oracle labels and is therefore `NON_DEPLOYABLE_SOURCE_ORACLE_UPPER_BOUND`, not a deployable source policy. No already-certified deployable source policy was found in the frozen reports.
- **Target truth:** frozen exact top-10 truth and the complete target budget trajectory determine whether each budget reaches Recall@10 0.9. New target truth acquisition is forbidden in this phase; sentinel truth may be priced only from frozen design-side evidence.
- **Sentinel cost:** NDC/search work can be estimated from frozen traces. Exact external truth-acquisition effort and wall-clock latency are not identified; these must remain `NOT_ESTIMABLE` unless a frozen cost field is located.
- **Prefix state:** hnswlib prefix/native equivalence is established for the frozen pilot (500-query spike and, on GloVe, 768/768 checks per seed), including no duplicate distance computations. Equivalent complete prefix state is not established for every implementation/build.
- **Oracle-only analyses:** source stable-budget transfer, perfect-label target checkpoint decisions, and target-aware minimum budgets are upper bounds and may not enter the deployable lane.

## Frozen evidence located

- 81 builds, 972,000 query-budget rows, 648 directed source-target pairs and 2,592 risk cells are documented by the theory lock.
- Required identifiers and metrics are represented across the frozen Cross-Index run CSV/metadata and derived tables: dataset, implementation, history/order, seed, query id, budget, Recall, NDC and graph metadata.
- The prior GloVe signal pilot tested 16 fixed candidate policies with calibration `n=256`; 0/16 certified and actual failures ranged 32--181/256. This is evidence of endpoint/policy infeasibility, not merely Bonferroni power loss.

## Missing or unresolved inputs before Gate E0

- A graph-level safe endpoint label has not yet been recomputed under the new five-label Phase 1 rule.
- The exact endpoint-query failure Parquet is not yet materialized because of the disk stop.
- A deployable source policy independent of per-query source Oracle labels is absent.
- Full prefix/native state equivalence outside the frozen hnswlib pilots is absent.
- Real latency and exact truth-acquisition labor are not estimable from the located trace evidence.

## Data firewall

No `validation-dev` or `formal-test` contents were opened. No graph was built, no data downloaded, no model trained and no Graph-ANNS replay started.
