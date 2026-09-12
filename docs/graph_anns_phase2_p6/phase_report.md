# Phase P6 report — scale cell (SIFT-1M), predictor probe, distinguishability (user-authorized)

## Goal (user authorized option a)

- P6-A: SIFT-1M hnswlib registered cell — 8 builds, clean 500-query evaluation role,
  h=10 transport risk + variation + pooling k-curve + profiling cost re-measurement.
  Kills the 100K-scale attack (W1).
- P6-B: learned-predictor transfer probe (GBM on query features, source-train → target-build).
  Closes the three-layer story (W2).
- P6-C: probe-distinguishability curve for Theorem 1 (registered pairs).

## Step 1 — availability gates (must pass before any build)

1. SIFT-1M data source (local copy, or network: HF/ann-benchmarks mirrors).
2. hnswlib build toolchain (python package or repo submodule build).
3. Disk + RAM budget (1M×128 f32 = 512MB base; 8 indexes ≈ 500MB each on disk).

## Hard gates carried over
- Clean forensics BEFORE any risk number; preregister grid/roles in the P6 manifest before
  searching; no future-role access; every number traceable; transport results conditional.
