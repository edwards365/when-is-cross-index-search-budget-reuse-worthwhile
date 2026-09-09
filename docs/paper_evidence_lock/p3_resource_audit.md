# P3 resource audit

P3 is sealed from historical machine measurements without accessing a sealed query role or running a new build/search. The root filesystem has 17.16 GiB free and is excluded. The dedicated data500 path has 902.66 GiB free.

The preferred matrix contains 48 builds. A storage stress envelope of 100x the observed Gate-A artifact-per-run rate plus the mandatory 5 GiB reserve requires 651.67 GiB and leaves 250.99 GiB. Historical per-dataset maximum build and six-budget search timings plus exact-truth generation total 1.279 hours for the preferred matrix; a 4x operational multiplier gives 5.114 hours, within the frozen 8–14 hour target and 20 hour hard maximum.

**P3 status: PASS.** These are E1/E2 resource estimates, not E4 scientific results. Confirmatory and future-replication queries remain unopened, and the matrix is not started by this audit.
