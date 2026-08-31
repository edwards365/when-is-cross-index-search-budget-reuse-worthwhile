# Frozen CIBS-Fixed algorithm

## Version boundary

`CIBS-Fixed` means fixed (K), fixed (n), a preregistered build set, and a preregistered raw fixed-`ef` grid. `CIBS-Race` is a future sequential method. `Best-of-R` lacks the simultaneous certificate. `Oracle Portfolio` uses unavailable truth and is only an upper bound.

```text
INPUT:
  preregistered candidate builds G_1...G_K
  preregistered raw fixed-ef grid E
  n shared sentinel queries with exact truth
  recall target tau
  risk threshold delta
  total error alpha
  fixed-safe fallback
  primary cost = mean NDC
  p95 non-inferiority threshold

1. Audit every build artifact and query ID.
2. Run every sentinel query on every action (G_k, e_l).
3. Record endpoint-aware failure Z_i(a), NDC, expansion, raw Recall.
4. Compute simultaneous one-sided risk UCB U_r(a).
5. Certified set:
       S = {a : U_r(a) <= delta}.
6. If S is empty:
       return fixed-safe fallback.
7. For every a in S, estimate mean NDC and p95 descriptively.
8. Select:
       a_hat = argmin_{a in S} mean_NDC_hat(a).
9. Fixed tie-breaking:
       lower estimated p95;
       then lower ef;
       then lower build ID.
10. Serialize selected index, selected ef, certificate,
    evidence count, fallback and artifact hashes.
OUTPUT:
  one selected index
  one fixed global ef
  safety certificate
  cost estimate
  fallback
```

## Required invariants

- The action family is frozen before sentinel outcomes.
- Every ((G_k,e_\ell)) is separately tested; the first version does not exploit budget order for multiplicity.
- Selection never reads evaluation or future-confirm truth.
- If fewer than 256 eligible frozen sentinel queries exist, use the actual number and recompute exact thresholds; never borrow from evaluation.
- Fixed-safe fallback is a preregistered external action with its own safety basis, not a retrospectively relabeled candidate.
- Output is one serialized index plus one global fixed-`ef`, not routing, ensemble, or dynamic build switching.

## Candidate-build preregistration

Before any sentinel response, record all random seeds and insertion orders; identical data, `M`, `efConstruction`, metric, compiler, threads, and SIMD; and immutable artifact IDs/hashes. Only legal seed and insertion-order variation is allowed. Do not select seeds from prior performance, discard failed builds, or use truth in build generation.

