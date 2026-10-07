# Versioned synthetic model control correction

The first Linux full-source DARTH CI reached compiled IP controls, then rejected
the authored model predictions. The failed run and its outputs are retained;
this was not an original scientific experiment rerun.

The old positional probe varied `start_iteration` from 0 to 10 while keeping
`num_iteration=1` on one Booster via `LGBM_BoosterPredictForMatSingleRow`.
In pinned LightGBM 4.5.0 `src/c_api.cpp`, `SetSingleRowPredictorInner` reuses its
cache when `IsPredictorEqual` succeeds. That comparison checks iteration count
but not starting iteration. The captured predictions consequently repeated the
tree-0 result for all eleven requested trees. The source file SHA-256 is
`8b1a3871320a5edad031beb0caaaa62a3385c5a713bc8586a6c73fe754090074`.
It is available in the already-pinned LightGBM source archive; no source upgrade
or library patch is part of this correction.

`darth_compiled_interface_probe_v2.cpp` uses `LGBM_BoosterPredictForMat` with one
row, which constructs a predictor for each requested iteration range. The
authored eleven stumps, canonical/native/restored feature arms, 363 unique
prediction identities, and exact expected values are unchanged. The verifier
also rejects duplicate identities and nonfinite predictions. The original v1
probe is retained byte-for-byte. The builder generates v2 using two explicit
API-name replacements and one row-dimension insertion; it refuses unexpected
source layouts.

The actual scientific `DeclarativeRecall.cpp` and genuine-IP variant each have
three SingleRow calls, all with fixed `start_iteration=0, num_iteration=-1`
(all trees), unlike the varying-range control. A local source regression test
checks all six sites. Neither file nor the production prediction API was
changed. This specific control failure does not establish a defect in those
fixed-range calls, nor does the control replace scientific outcome validation.

Local tests exercise the expected matrix and reproduce rejection of the
observed cached-tree pattern; Linux compiled execution of v2 must still pass
the separate CI build-only contract before being reported as verified.
