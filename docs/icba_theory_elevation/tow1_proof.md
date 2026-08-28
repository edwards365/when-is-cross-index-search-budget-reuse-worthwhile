# Proof of T-OW1

Fix `x in A`. Couple observations `Z0~Q0` and `Z1~Q1` maximally, so `Pr[Z0=Z1]>=1-TV(Q0,Q1)`. Use the same independent policy randomizer `U` in both environments. On the event `Z0=Z1`, the policy receives identical inputs `(x,Z,U)` and selects the same action.

If that action is below `b*_1(x)` and is not a certified-safe fallback, it contributes to high-environment under-budget. Otherwise it is at least `b*_1(x)` or fallback, and by definition contributes to low-environment conservative/fallback. These two cases cover every identical-observation outcome. Therefore, conditional on `x`,

`Pr_1(under | x) + Pr_0(conservative/fallback | x) >= 1-TV(Q0,Q1)`.

Integrating over `A` under the common query law yields

`U_1(pi;A)+CF_0(pi;A) >= P(A)(1-TV) >= rho(1-TV)`.

Randomized policies require no separate argument because the shared `U` is part of the Markov kernel; total variation contracts under that kernel. If every conservative/fallback action has excess cost at least `gamma>0`, Markov decomposition gives `E[excess_cost*1_A] >= gamma*CF_0`, producing the cost form.

For `k` probes, replace `Qj` by the joint law `Qj^(k)` and repeat verbatim. For iid probes, KL tensorizes: `KL(Q0^k||Q1^k)=k KL(Q0||Q1)`. Pinsker's inequality gives `TV <= sqrt(k KL/2)`, clipped at one, and substitution gives the displayed bound.

## Boundary cases

- `rho=0`: the bound is zero and intentionally vacuous.
- `TV=1`: perfect observation separation removes this testing obstruction.
- `Delta=0`: no ordered action conflict is assumed; the theorem does not apply.
- Right censoring: if `b*` is unidentified, the threshold premise cannot be asserted. Interval variants give a bound only where safe-budget intervals are disjoint.
- Endpoint infeasibility: if no safe grid action exists, count fallback explicitly; do not call maximum budget safe.
- Non-monotone loss: replace thresholds by incompatible safe-action sets. The same coupling proof works if every common action is unsafe in one environment or conservative/fallback in the other, but ordered `Delta` language is unavailable.
- Different query laws: the proof must couple the joint `(X,Z)` laws, replacing `TV(Q0,Q1)` by the relevant joint or conditional integrated distance. The theorem above deliberately uses a common `P`.

## Status

The finite-grid, common-query-law statements T-OW1a and T-OW1b are `FORMAL_PROOF_COMPLETE`. General censoring, non-monotone actions and arbitrary hierarchical build laws remain outside this theorem; the documented extensions are `RESTRICTED_PROPOSITION` or `PROOF_SKETCH` only.
