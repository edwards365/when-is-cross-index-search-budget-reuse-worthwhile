# Proofs

## Proof of T-OO1

If `I subseteq J`, every `I`-measurable admissible rule is `J`-measurable. Taking an infimum of the same objective over the larger feasible class cannot increase value. Apply this twice. Expanding definitions gives

`R_0-R_theta=(R_0-R_m)+(R_m-R_theta)`.

Adjoin a common independent uniform variable to all sigma-fields to represent randomization; inclusion is preserved. Acquisition cost must already be included in each rule's `C_N`; otherwise the conclusion concerns only decision cost.

## Proof of T-OO2

Take equiprobable environments `theta_0,theta_1`, actions `a_0,a_1,f`, threshold zero, costs

`C_0=(0,2,1)`, `C_1=(2,0,1)`,

and risks

`rho_0=(0,1,0)`, `rho_1=(1,0,0)`.

All observable transcripts have the same degenerate law. Under hard safety across the unresolved environments, neither `a_0` nor `a_1` is admissible, so every observable safe rule uses `f` and has cost one. The oracle uses `a_i` in environment `i` at cost zero. Thus `R_0=R_m=1`, `R_theta=0`, proving the claims. The construction persists for every finite or infinite number of uninformative sentinels.

## Proof of T-OO3

Given output action `A`, define a randomized test `phi=0` on `D_0` and `phi=1` otherwise. Because `D_0` and `D_1` are disjoint, under environment zero `ell_0>=Delta` on `{phi=1}`, while under environment one `ell_1>=Delta` on `{phi=0}`. Therefore

`(E_0 ell_0+E_1 ell_1)/2 >= Delta/2[P_0(phi=1)+P_1(phi=0)]`.

The minimum error sum of any randomized test is `1-TV(P_0^m,P_1^m)`, proving the equal-prior result. The maximum risk dominates the average. With prior `p`, the same integral proof gives the Bayes testing error `int min{p dP_0,(1-p)dP_1}`.

Bretagnolle–Huber gives `P_0(phi=1)+P_1(phi=0)>=exp(-K_m)/2`; Pinsker gives `TV<=sqrt(K_m/2)`. Substitution proves both corollaries. Randomized policies are Markov kernels and cannot increase total variation. For `L_lambda=C+lambda rho`, `Delta` is the smallest positive separation of environment-specific optimal decision regions under that scalar loss. `lambda` prices one unit of failure probability and does not assert hard safety.

For adaptive probes, factor each transcript likelihood into policy kernels and conditional observation kernels. The policy kernels cancel in the likelihood ratio because the same algorithm is run under both environments. Taking `P_0` expectation of the log likelihood yields the conditional KL chain rule. Bounding every summand by `I*` gives `K_m<=mI*`.

## Qualification for T-OO4

Map a terminal action to an environment label whenever the near-optimal action sets are disjoint. Fano bounds its error by `1-(I(theta;Z)+log2)/log K`. Multiplying by a uniform loss separation yields a decision lower bound. Without disjoint action regions, a many-to-one environment-to-action map can eliminate the `log K` difficulty; environment identification is then the wrong objective. Because no matching positive result uses a packing complexity, this extension is not promoted.

## Proof of T-OO5

On `E`, if `a` is retained then `rho(a)<=hat rho(a)+epsilon_R<=delta`, so all retained actions are safe. For the optimum,

`hat rho(a*)+epsilon_R<=rho(a*)+2epsilon_R<=delta`,

so it is retained. Estimated optimality gives `hat C(hat a)<=hat C(a*)`. Twice applying the cost error bound yields

`C(hat a)<=hat C(hat a)+epsilon_C<=hat C(a*)+epsilon_C<=C(a*)+2epsilon_C`.

If `hat a!=a*`, uniqueness implies `C(hat a)-C(a*)>=Gamma_C`, contradicting `Gamma_C>2epsilon_C`. With ties, the conclusion is recovery of the optimal set. Endpoint-infeasible actions have absolute risk one or are excluded. A fallback handles an empty retained set.

## Proof of T-OO6

Condition on `D_sel`. Then `hat a` is fixed and independent certification validity gives

`P{U_alpha(hat a)<rho(hat a)|D_sel}<=alpha`.

If `hat a` is accepted and unsafe, this failure event occurs. Otherwise the safe fallback is deployed. Integrating over `D_sel` proves the fixed-target statement. The proof certifies one conditionally fixed action, so there is no familywise multiplicity. If certification observations influence `hat a`, it is no longer fixed under the conditioning and the proof fails.

For zero Bernoulli failures, `P_rho(X=0)=(1-rho)^n`. Setting the upper endpoint by `(1-U)^n=alpha` gives `U=1-alpha^(1/n)` and solving `U<=delta` gives the displayed ceiling. This is exactly the classical Clopper–Pearson special case.

Let `A` denote acceptance and `K` fixed evidence/offline cost. Total expected cost is

`P(A)E[C(hat a)|A]+P(A^c)C(f)+K/N+C_control`.

Comparing the mixture term with baseline `C_B` gives the break-even formula in `cost_model.md`.

## Proof of T-OO7

Condition on `(a*,hat a)=(i,j)` and sum the cost difference over all cells; this is the law of total expectation and yields `sum W_ij`. The finite constructions in `counterexamples.md` prove all separations. Exact accuracy uses only diagonal mass, whereas regret weights every off-diagonal cell by its decision consequence.

## Proof of T-OO8

The adaptive KL identity follows from the transcript factorization used in T-OO3. If both terminal errors are at most `beta`, data processing through the terminal decision gives

`KL(P_0^m||P_1^m)>=kl(1-beta,beta)`.

The chain rule and one-step bound give the necessary sample inequality. For a stopping time, truncate at `T`, apply the chain rule, and pass to the limit under finite expected stopping and integrability.

For the restricted upper bound, repeatedly use a known experiment with two-sided KL at least `I_min>0`. Standard likelihood-ratio concentration on a finite alphabet gives error at most `exp(-c m I_min)` for a channel-dependent constant; an SPRT has expected sample `O(log(1/beta)/I_min)` under bounded increments. This does not prove that Graph-ANNS exposes such an experiment.
