# Confirmatory protocol (frozen contract; no run in this round)

**Status:** `READY_FOR_CONFIRMATORY_HNSWLIB_REBUILD_MATRIX`. This round freezes the E4 design but does not run it. Confirmatory and future-replication query roles were not accessed.

- Implementation: hnswlib; datasets: SIFT-100K and Arxiv-Nomic-100K.
- Budget grid: `{10,20,40,80,120,200}` from auditable Gate-A artifacts.
- Builds: minimum 18, preferred 24 per dataset; build is the inference unit.
- Confirmatory queries: 1,000 new mutually exclusive queries per dataset; `future_replication` remains separately sealed.
- Hypotheses: H1 build changes safe-budget response; H2 source→target reuse incurs risk or conservative cost; H3 survives endpoint filtering/build robustness; H4 target recovery value is limited by full deployment cost.
- Baselines: Same-Build Tuned, Source-Reuse, Worst-Build Conservative, Target Profiling/Recalibration, Fixed-Safe Endpoint, and Per-Target Oracle as a non-deployable upper bound.
- Statistics: paired query bootstrap 5000/seed 991, build-cluster bootstrap 5000/seed 991, leave-one-build-out, top-1% query deletion, top-contribution build deletion.
- System measurement: one fixed machine, fixed CPU/threads/affinity/compiler, warm-up, randomized order, mean/p95/p99, explicit I/O/truth/build accounting.
- Resource placement: all large artifacts under `/home/wlk/data500/graph_anns_paper_evidence_lock`; the root filesystem is excluded.
- Runtime contract: 5.11 h conservative compute envelope, 8–14 h operator target, 20 h hard maximum.

P0 reconciles 1,656,000 physical rows and 552,000 unique query-budget units. P2 passes at both 18 and 24 builds under residual-bootstrap and leave-one-build-out sensitivity. P3 passes with a 651.7 GiB storage stress envelope and 251.0 GiB remaining data500 margin. P4 confirms sealed roles. The matrix is authorized by the contract but is not automatically started by this evidence-lock round.
