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

## Execution record (steps 2-3)

- P6-A: 8 builds + 2 identity builds at SIFT-1M (41.4 min wall); forensics gate passed
  before any risk number; analysis per preregistration; incremental CI recomputed on the
  incremental estimand after a spec fix (retry 1); tests updated to the measured pooling
  boundary (1M k=7 = 10.4% - a finding, not an expectation failure). 17/17 checks.
- P6-B: predictor probe complete (commit earlier in phase).
- P6-C: distinguishability complete with exact plug-in TV.

## Theory/paper consistency review (step 5)

- All P6 numbers are new registered results on a new preregistered cell; no frozen number
  touched; no estimand reinterpreted (h=10 event identical to registered semantics).
- Paper impact: R4 table gains a 1M row; R1 abstract gains one sentence; new limitations
  entry for the pooling source-count boundary; Theorem 1 section gains the instantiated
  premise with probe-class caveat.
