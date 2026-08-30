# Theorem dependency map

## Negative chain

`information model -> T-OO2 finite obstruction -> T-OO3 testing lower bound -> T-OO8 adaptive information requirement`.

T-OO4 is an optional Fano packing offshoot. It does not feed the selected method or produce a matched `log K` result, so it remains appendix-only.

## Positive chain

`cost/risk model -> T-OO5 robust safe screening -> T-OO6 independent certification -> RACS-P1/P2`.

The amortized cost model plus Lemma L5 yields `RACS-P3`. T-OO7 determines evaluation metrics but is not required for safety.

## Shared bridge

Both sides use the same finite action set, target-specific costs/risks, explicit fallback, and evidence transcript. The bridge is only partial:

- the lower side measures information by TV/KL;
- the upper side assumes uniform estimation errors and margins;
- T-OO8 connects the two only for a known binary finite-alphabet channel.

There is no proved general map from KL separation to `epsilon_R/epsilon_C` for the current Graph-ANNS observation channel.

## Main-result selection

1. Main I: T-OO3 with T-OO8 consequence.
2. Main II: T-OO5 with T-OO6 and RACS.

T-OO1 is not promoted because it is feasible-class inclusion plus an algebraic identity.
