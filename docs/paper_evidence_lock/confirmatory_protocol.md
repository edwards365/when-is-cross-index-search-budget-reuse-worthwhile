# Confirmatory protocol (frozen contract; no run in this round)

**Status:** E4 design only. Confirmatory and future-replication query roles were not accessed.

- Implementation: hnswlib; datasets: SIFT-100K and Arxiv-Nomic-100K.
- Budget grid: `{10,20,40,80,120,200}` from auditable Gate-A artifacts; Cross-Index/Tournament twelve-level grids are separate historical protocols.
- Builds: minimum 18, preferred 24 per dataset; build is the inference unit.
- Query roles: `protocol_design`, `confirmatory_query`, `future_replication`; only the first may be used in this round.
- Hypotheses: H1 build changes safe-budget response; H2 source→target reuse incurs risk or conservative cost; H3 survives endpoint filtering/build robustness; H4 target recovery value is limited by full deployment cost.
- Baselines: Same-Build Tuned, Source-Reuse, Worst-Build Conservative, Target Profiling/Recalibration, Fixed-Safe Endpoint, and Per-Target Oracle as a non-deployable upper bound.
- Statistics: paired query bootstrap 5000/seed 991, build-cluster bootstrap 5000/seed 991, leave-one-build-out, top-1% query deletion, top-contribution build deletion.
- System measurement: one fixed machine, fixed CPU/threads/affinity/compiler, warm-up, randomized order, mean/p95/p99, explicit I/O/truth/build accounting.

P0 numeric reconciliation is complete by context: Gate-A main raw files yield 1,656,000 physical rows and 552,000 unique query-budget units; 972,000 belongs to the historical Cross-Index protocol and 648,000 to the historical Tournament protocol. P2 passes prospectively: nine historical hnswlib target-build units per primary dataset estimate variance, and the registered 18/24-build designs exceed 80% residual-bootstrap power even under leave-one-build-out sensitivity. This does not create an E4 result or authorize query access while P3 remains conditional.
