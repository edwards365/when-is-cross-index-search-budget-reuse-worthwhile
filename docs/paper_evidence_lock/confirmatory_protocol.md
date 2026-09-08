# Confirmatory protocol (frozen contract; no run in this round)

**Status:** E4 design only. Confirmatory and future-replication query roles were not accessed.

- Implementation: hnswlib; datasets: SIFT-100K and Arxiv-Nomic-100K.
- Budget grid: `{10,20,40,80,120,200}` from auditable artifacts; the unverified twelve-level claim is not used.
- Builds: minimum 18, preferred 24 per dataset; build is the inference unit.
- Query roles: `protocol_design`, `confirmatory_query`, `future_replication`; only the first may be used in this round.
- Hypotheses: H1 build changes safe-budget response; H2 source→target reuse incurs risk or conservative cost; H3 survives endpoint filtering/build robustness; H4 target recovery value is limited by full deployment cost.
- Baselines: Same-Build Tuned, Source-Reuse, Worst-Build Conservative, Target Profiling/Recalibration, Fixed-Safe Endpoint, and Per-Target Oracle as a non-deployable upper bound.
- Statistics: paired query bootstrap 5000/seed 991, build-cluster bootstrap 5000/seed 991, leave-one-build-out, top-1% query deletion, top-contribution build deletion.
- System measurement: one fixed machine, fixed CPU/threads/affinity/compiler, warm-up, randomized order, mean/p95/p99, explicit I/O/truth/build accounting.

The contract is not executable until Gate P0 resolves the conflicting historical row counts and pair-count claims.
