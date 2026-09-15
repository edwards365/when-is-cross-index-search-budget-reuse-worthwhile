# Phase 5 DARTH comparator addendum

Frozen before any DARTH output on the prospective query/build matrix is read.
The preregistration calls for the frozen official DARTH model but did not name
which historical source build supplies it. To avoid target retraining and any
best-of-source selection, the comparator uses the first historical source in
the frozen order, seed 1103, for every prospective target build. The model file
and its SHA-256 are recorded before execution.

This comparator measures direct source-to-target DARTH transfer. It is not a
claim about a newly target-trained DARTH model. For each target build, the
deployment family is source-seed-1103 DARTH, source-only global fixed ef, and
ef=200. The three policies use simultaneous one-sided CP bounds at confidence
`1-0.05/3`; failure moves to the next fixed rung. Evaluation cannot select a
model, multiplier, interval, or fallback.

The command remains the official `early-stop-testing` path with target recall
0.90, initial interval 20, minimum interval 5, and logging interval 5. No
result-dependent calibration is allowed.
