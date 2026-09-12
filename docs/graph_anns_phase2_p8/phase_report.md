# Phase P8 report — rebuttal evidence cycle (response to two external reviews)

Inputs: R1 (5/10) and R2 (6/10) review reports. All four computable reviewer asks were
executed pure-code; all numbers machine-verified (12/12 checks).

## Results summary
1. h-sensitivity (R1-C1): every cell at h=8 stays above the 2% gate (min 5.96%);
   monotone in h. Reviewer 1's stated upgrade condition (5->6) is met by the data.
2. gamma-sensitivity (R2-Q4): margin condition passes point-estimate at small gamma
   (16-21/24 targets at gamma=0.005); zero everywhere at gamma=0.02; the binding
   constraint is zero-failure certification power, not margin existence. Paper wording
   will be sharpened accordingly.
3. Rich-probe distinguishability (R2-Q2): runtime features give weak-moderate separation
   (median 0.56-0.58, max 0.72); hit-transcript remains chance. Theorem-1 instantiation
   becomes explicitly probe-class-conditional; worst-case TV 0.44 still leaves 0.28*Delta
   residual loss.
4. Quantile pooling (R2-Q3): q=0.9 ~= max; median unusable; no aggregation sweet spot.

## Remaining (scheduled)
P8-D policy latency/DistComp quantile ledger (data ready); origin-unlocated aggregate
re-derivation; presentation pass (takeaway table, hedging consolidation, gate rationale).

## Execution notes
Three script defects fixed during the cycle (flush-position syntax error, ndarray/Series
mismatch, over-deleted line during repair); all fixes code-only, no data changes.
