# Main theorems and propositions

All expectations and feasibility constraints use the same action class, prior (when present), and declared safety semantics.

## Quantifier order lock

- T-OO1: for every declared environment law (or fixed target), every workload `N`, threshold `delta`, and nested information triple with one common admissible action class, the inequalities hold.
- T-OO2: there exists one finite two-environment problem such that, for every evidence count `m` and every observable randomized safe rule, the displayed gap holds.
- T-OO3: for every pair of transcript laws, every randomized terminal Markov kernel, and every pair of disjoint decision regions satisfying the stated separation, the lower bound holds. The adversarial environment is selected after the rule is fixed.
- T-OO4: for every finite packing satisfying disjoint near-optimal regions and the stated mutual-information bound, the Fano consequence holds; no claim is made when those premises fail.
- T-OO5: for every fixed target, finite action set, and realized estimation event `E` satisfying the two uniform inequalities, the selector has the stated properties. Probability enters only through a separately supplied lower bound on `P(E)`.
- T-OO6: for every fixed target and every possibly data-dependent selector measurable with respect to `D_sel`, if `D_cert` is independent and its fixed-action UCB is level `alpha`, then the probability over `(D_sel,D_cert)` of deploying an unsafe action is at most `alpha`.
- T-OO7: for every finite joint law of oracle and chosen actions with integrable costs, the identity holds; the separations are existential finite counterexamples.
- T-OO8: for every adaptive predictable probe rule and every terminal test with both errors at most `beta`, the necessary information inequality holds. The upper rate exists only for channels satisfying the additional known-query, positive two-sided KL, finite-alphabet, bounded-log-likelihood assumptions.

## T-OO1 — information monotonicity and decomposition

**Status:** `FORMAL_PROOF_COMPLETE`; `IDENTITY_OR_DEFINITION`.

For any `I_0 subseteq I_m subseteq I_theta`, if the corresponding admissible randomized rule classes are nested and share the same safety constraint, then

`R_theta <= R_m <= R_0`.

Consequently `H_oracle>=H_obs(m)>=0` and

`H_oracle=H_obs(m)+G_id(m)`.

If `I_{m1} subseteq I_{m2}`, then `R_{m2}<=R_{m1}`. The statement remains true for randomized rules after adjoining the same independent randomizer to every information class.

## T-OO2 — oracle headroom does not imply observable recovery

**Status:** `FORMAL_PROOF_COMPLETE`; `CLASSICAL_APPLICATION`.

There exists a two-environment, three-action fixed-target problem with identical observable transcript laws for every `m` such that `H_oracle=1`, `H_obs(m)=0`, and `G_id(m)=1`. Thus positive oracle headroom alone neither proves a deployable selector exists nor that more sentinels help.

## T-OO3 — observability-limited safe recovery lower bound

**Status:** `FORMAL_PROOF_COMPLETE`; `CLASSICAL_APPLICATION` with Graph-ANNS safe-action structure.

Let `theta in {0,1}`, transcript laws be `P_0^m,P_1^m`, and let a randomized terminal rule output `A`. Suppose disjoint decision regions `D_0,D_1` satisfy, for `i=0,1`,

`ell_i(a)>=Delta` whenever `a notin D_i`,

where `ell_i` may be cost regret, fallback excess, or the soft loss regret induced by `C+lambda rho`. Then under equal prior,

`(E_0 ell_0(A)+E_1 ell_1(A))/2 >= Delta/2 * (1-TV(P_0^m,P_1^m))`.

The same expression lower-bounds the maximum of the two risks. Under prior `p`, replace the final testing factor by

`int min{p dP_0^m,(1-p)dP_1^m}`.

For adaptive probes with transcript KL `K_m`,

`max_i E_i ell_i(A) >= Delta/4 exp(-K_m)`

and also

`max_i E_i ell_i(A) >= Delta/2 max{0,1-sqrt(K_m/2)}`.

If every conditional probe KL is at most `I*`, then `K_m<=m I*`. These bounds do not create safety when no safe action exists; fallback must be explicit.

## T-OO4 — multi-environment qualification

**Status:** `RESTRICTED_PROPOSITION`; disposition `TWO_ENVIRONMENT_WITNESS_SUFFICIENT`.

A finite `K`-environment packing with disjoint near-optimal action sets and transcript mutual information at most `I` yields a Fano error term of order `1-(I+log 2)/log K`, hence a corresponding decision-loss bound. In the current framework this adds no matched `log K` term to T-OO5 or RACS and no design rule supported by frozen evidence. It is therefore appendix context, not a main theorem.

## T-OO5 — margin-based positive recovery

**Status:** `FORMAL_PROOF_COMPLETE`; `RESTRICTED_DOMAIN_PROPOSITION` and classical uniform-convergence application.

Fix target `theta`, finite actions, hard threshold `delta`, and a safe fallback. Let `a*` minimize `C_N(theta,a)` over `A_delta(theta)`. On an event `E` where simultaneously

`sup_a |hat C(a)-C_N(theta,a)|<=epsilon_C`

and

`sup_a |hat rho(a)-rho_theta(a)|<=epsilon_R`,

retain `hat A={a:hat rho(a)+epsilon_R<=delta}` and choose a minimum estimated-cost retained action, falling back if the set is empty. If

`delta-rho_theta(a*)>=2 epsilon_R`,

then `a*` is retained, every retained action is safe, and

`C_N(theta,hat a)-C_N(theta,a*)<=2 epsilon_C`.

If the safe optimum is unique with cost margin `Gamma_C>2 epsilon_C`, then `hat a=a*`. Ties yield set recovery, not a unique-label claim. Correlated estimates are allowed when `E` is a valid joint event; adaptive estimates require time-uniform or design-valid bounds.

## T-OO6 — independent certification and fallback

**Status:** `FORMAL_PROOF_COMPLETE`; `NEW_COMBINATION_OF_CLASSICAL_RESULTS` in a restricted deployment protocol.

Let `hat a=S(D_sel)` and let independent `D_cert` produce a one-sided level-alpha UCB `U_alpha(hat a)`. Deploy `hat a` only when `U_alpha<=delta`; otherwise deploy a known-safe fallback. Then for a fixed target,

`P_D{rho_theta(pi_D)<=delta}>=1-alpha`.

No multiplicity correction is required when only the independently selected action is evaluated on `D_cert`. Reusing `D_cert` for selection invalidates this conditional argument unless simultaneous or selection-aware control is used.

With zero failures among `n` iid certification queries, Clopper–Pearson gives `U=1-alpha^(1/n)` and

`n_min=ceil(log(alpha)/log(1-delta))`,

equal to 29, 59, and 299 for `delta=0.10,0.05,0.01` at `alpha=0.05`.

## T-OO7 — accuracy and decision regret separate

**Status:** `FORMAL_PROOF_COMPLETE`; `RESTRICTED_DOMAIN_PROPOSITION` with strong cost-sensitive-classification overlap.

For oracle action `i`, chosen action `j`, and cost `C_i(j)`, define

`W_ij=P(a*=i,hat a=j)[C_i(j)-C_i(i)]`.

Then decision regret is exactly `sum_ij W_ij`. Equal exact-action accuracy can have unequal regret; lower accuracy can have lower regret; and nonunique/near-tied optima can make exact accuracy arbitrarily uninformative. Method gates must therefore use safety, total cost, decision regret, observable gain, and epsilon-optimal rate.

## T-OO8 — adaptive target-evidence complexity

**Status:** lower bound `FORMAL_PROOF_COMPLETE`; upper bound `RESTRICTED_PROPOSITION`; overall `PARTIALLY_MATCHED_RATE` only for known binary finite-alphabet channels.

For an adaptive transcript,

`KL(P_0^m||P_1^m)=sum_t E_0 KL(P_0(Y_t|H_{t-1},Q_t)||P_1(Y_t|H_{t-1},Q_t))`.

If the maximum conditional one-step KL is `I*` and a terminal test has both errors at most `beta<1/2`, then

`m I* >= kl(1-beta,beta)`.

For a sequential stopping time, the analogous bound uses `E_0 tau I*`. If one known query/action has positive KL in both directions and bounded finite-alphabet log likelihood, fixed allocation plus a likelihood-ratio test, or an SPRT, achieves `O(log(1/beta)/I_min)`. Thus the logarithmic error rate is matched only under this explicit channel model. Frozen Graph-ANNS evidence has not established a deployable `I*>0`; its applied status remains `LOWER_BOUND_ONLY`.

## Selected main results

1. Main I: T-OO3 plus T-OO8 transcript consequence—observability-limited safe recovery lower bound.
2. Main II: T-OO5 plus T-OO6—margin-based certified recovery upper bound.

T-OO1 is a definition/identity and is not a main theorem. T-OO2 and T-OO7 are counterexample/evaluation propositions. T-OO4 is appendix-only.
