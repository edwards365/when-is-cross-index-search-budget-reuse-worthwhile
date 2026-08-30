# RACS — Risk-Aware Certified Selection

**Status:** `THEORETICAL_METHOD_TEMPLATE`; not implemented or deployable evidence.

## Inputs

A frozen source policy; finite recovery actions; fixed target; disjoint selection and certification sentinels; threshold `delta`; confidence `alpha`; workload `N`; symbolic or measured full costs; and a separately justified safe fallback.

## Procedure

1. On `D_sel`, compute design-valid estimates `hat rho(a),hat C_N(a)` and simultaneous errors `epsilon_R,epsilon_C`.
2. Retain only actions with `hat rho(a)+epsilon_R<=delta`.
3. If none remain, return fallback.
4. Choose the retained action with minimum estimated total cost.
5. On independent `D_cert`, compute the preregistered one-sided UCB for only the chosen action.
6. Accept it if the UCB is at most `delta`; otherwise return fallback.
7. Before evidence acquisition, skip recovery and return the preregistered baseline when the best available symbolic break-even denominator is nonpositive.

## RACS-P1 — fixed-target safety

Under a valid independent level-alpha selected-action certificate and a safe fallback, the final rule has risk at most `delta` with probability at least `1-alpha` over certification data. This is not an open-world build guarantee.

## RACS-P2 — near-oracle cost

On the T-OO5 uniform estimation event, if the optimal safe action has risk slack at least `2 epsilon_R`, the pre-certificate choice is safe and within `2 epsilon_C` of the fixed-target oracle. The final expected excess total cost is bounded by

`2 epsilon_C + P(reject)[C_N(fallback)-C_N(a*)]_+ + (C_evidence+C_offline)/N + C_control`,

with any negative terms discarded only to produce an upper bound. Exact recovery additionally needs a unique safe optimum and `Gamma_C>2epsilon_C`.

## RACS-P3 — break-even

Let `C_M=P(accept)E[C_search(hat a)|accept]+P(reject)C_search(fallback)+C_control`. If `C_M>=C_baseline`, no finite `N` gives positive net value. Otherwise

`N*=(C_evidence+C_offline)/(C_baseline-C_M)`

is the strict break-even boundary. Unknown truth/retraining costs remain symbolic.

## Scope boundary

RACS assumes the target evidence law and confidence bounds are valid for the named target. It does not infer a target meta-law, certify unseen builds, or show that the frozen Graph-ANNS sentinel features carry positive information.
