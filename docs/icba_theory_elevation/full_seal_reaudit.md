# Full Seal re-audit (conditional continuation)

The stage starts from `a9f88bbcfd9b2c2f3e8a27e1471e16628b60cdb0` on `exp/icba_theory_elevation`. The current Full Seal artifact set verifies 59/59 SHA256 entries and its native seal test passes. It reproduces 81 graphs, 972,000 query-budget rows, 648 directed (324 unordered) within-cell build pairs, and endpoint strata 54 certified / 17 right-censored / 10 without a practical safe endpoint. GloVe remains excluded from migration-failure claims because its 27 graphs lack certified endpoints. No sealed validation or formal-test data were accessed.

## Mandatory integrity limitation

The inherited claim that the older micro-closure list reproduces 123/123 entries is not reproducible from Git commit `77e0d430bc04b819276b570a96eedb339a66c043`: 111/123 tracked blobs match, 8 tracked CSV blobs mismatch, and 4 listed `__pycache__` files are absent from Git. Work stopped at discovery; the user explicitly directed continuation. Therefore this stage uses a **conditional baseline** and must not claim exact 123/123 reproduction. The audit defect remains labeled `INVALID_FULL_SEAL_BASELINE` as a limitation; it is not silently repaired.

## Pair and collision audit

The 648 directed pairs reduce to 324 unordered pairs. Re-executing the frozen quartile rule in memory yields 94 directed collision candidates and 47 unordered collision pairs, involving 70 distinct builds. The CSV contains the complete deduplicated set rather than only the 20 published witnesses.

## Sentinel and inference audit

The sentinel implementation uses k in {32,64,128,256}, 300 persistent-RNG replicates at seed 991, and distinct without-replacement samples per replicate. It has no result cache, so no incomplete cache key can alias k/seed/target cells. The 256 sentinel and 744 evaluation IDs remain disjoint. Full uncertainty resamples target builds as clusters. Nine observed builds per dataset×implementation cell are treated as fixed-design evidence, never as a 5% meta-distribution certificate.

## Authorization

This conditional audit authorizes theory derivation and read-only Z1 field inspection. It does not authorize new graphs, sealed splits, algorithm claims, or a Z1 pilot before Gate Z1-A.
