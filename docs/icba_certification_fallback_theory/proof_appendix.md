# Proof appendix

## Common conventions

All statements in T-CF1--T-CF5 condition on one named build `G` unless an outer expectation is explicitly written. Business-query cost is integrable. Certification queries are iid from `P_G` or satisfy the exact exchangeability/concentration premise of the named confidence procedure. The absolute failure event includes endpoint censoring. A fallback is safe only through an independent premise.

## Proof of T-CF1

Let `H=sigma(D_sel,D_cert,U)` and let `Pi_S` and `R` be `H`-measurable. For a fresh business query and fresh search randomization, conditional expectation gives

`E[C_G(Q,Pi_D(Q),V)|H]=(1-R)mu_G(Pi_S)+R mu_G(pi_f)`.

Taking expectations and adding/subtracting `E[mu_G(Pi_S)]` yields

`E[C_G(Q,Pi_D(Q),V)]`

`=E[mu_G(Pi_S)]+E[R{mu_G(pi_f)-mu_G(Pi_S)}]`.

If `P(R)>0`, the second term equals

`P(R)E[mu_G(pi_f)-mu_G(Pi_S)|R=1]`.

If `P(R)=0`, define the product `P(R)Delta C_f` as zero. Adding the amortized evidence and control components proves the first identity. Subtracting `mu_G(pi_star)` and inserting the four definitions proves the oracle decomposition.

If `G~Pi` is explicitly part of the probability space, apply the conditional identity for `Pi`-almost every `G` and use the tower property. Without such a law, there is no outer-build probability statement.

The quantile limitation follows because quantiles are nonlinear functionals. The exact finite distribution in CE02 has lower mean and higher p95 than its baseline, so no implication can be added to the identity.

**Status:** `FORMAL_PROOF_COMPLETE`; `IDENTITY_OR_DEFINITION`.

## Proof of T-CF2

By T-CF1,

`C_B-C_deploy`

`=C_B-mu_G(pi_star)-R_selection-C_evidence/N-P(R)Delta C_f-C_control`.

The first difference is `G_oracle`, proving the exact net-gain formula and the strict necessary-and-sufficient inequality.

Let

`D=G_oracle-R_selection-P(R)Delta C_f-C_control`.

When `D>0`, `D-C_evidence/N>0` is equivalent to `N>C_evidence/D`. When `D<=0`, nonnegative evidence cost makes the net gain nonpositive for every finite positive `N`. This proves `NO_FINITE_BREAK_EVEN_WORKLOAD`.

For two actions with total costs `M_a+K_a/N` and `M_b+K_b/N`, subtracting gives

`C_a-C_b=(M_a-M_b)+(K_a-K_b)/N`.

If `K_a>K_b` and `M_a<M_b`, the difference is negative exactly above the displayed pairwise workload threshold. The other sign cases follow directly: an action weakly worse in both terms never dominates; an action weakly better in both terms always dominates, subject to identical safety and tail feasibility.

For two ordered budgets, subtract their T-CF1 costs. The conservative budget is cheaper in total exactly when the increase in recurrent search cost is smaller than the reduction in fallback, evidence, and control taxes, proving the budget-increase condition.

**Status:** `FORMAL_PROOF_COMPLETE`; `RESTRICTED_DOMAIN_PROPOSITION`.

## Proof of T-CF3

### Bonferroni selector

For each rung let `E_l={r_l<=U_l}`. Fixed-action validity gives `P(E_l^c)<=alpha/L`. Therefore

`P(intersection_l E_l)>=1-sum_l P(E_l^c)>=1-alpha`.

On the intersection, any rung satisfying `U_l<=delta` has `r_l<=delta`. Thus the minimum such rung is safe. If the set is empty, the external fixed-safe premise establishes safety. Hence the probability of unsafe deployment is at most `alpha`.

### Fixed-sequence selector

Because `r_1>=...>=r_L`, the unsafe indices are either empty or an initial segment `{1,...,h}`. Tests are performed in the fixed order `L,L-1,...,1`, stopping at the first non-rejection. If the procedure ever certifies and deploys an unsafe rung, it must reject the null at index `h`, the first unsafe index encountered in that order. Consequently

`{unsafe deployment} subseteq {test h rejects}`.

The local test at `h` has size at most `alpha`, so the probability of unsafe deployment is at most `alpha`. This argument does not condition on earlier rejections and requires no independence among test statistics.

### Samplewise comparison with Bonferroni

Assume all rungs use the same queries, observed failure counts satisfy

`X_L<=X_{L-1}<=...<=X_1`,

and the upper endpoint `U(x,m,a)` is nondecreasing in `x` and nonincreasing in the error budget `a`. Suppose Bonferroni certifies rung `b`. Then

`U(X_b,m,alpha/L)<=delta`.

For every `j>=b`,

`U(X_j,m,alpha)<=U(X_j,m,alpha/L)<=U(X_b,m,alpha/L)<=delta`.

Thus fixed sequence reaches at least `b` without stopping and selects a rung no larger than `b`. The containment can be strict. CE08 supplies a finite strict witness. This proves a locked-procedure power advantage, not universal dominance over every simultaneous method.

### Nested DKW band

Pointwise nesting defines the ordinal variable `S`. Let `F(l)=P(S<=l)` and `F_m(l)` be its empirical CDF. Since `r_l=1-F(l)` and `hat r_l=1-F_m(l)`, the event

`sup_l {F_m(l)-F(l)}<=epsilon`

implies `r_l<=hat r_l+epsilon` for every rung. The one-sided DKW inequality bounds the complement by `exp(-2m epsilon^2)`. Substitution of

`epsilon=sqrt(log(1/alpha)/(2m))`

proves simultaneous coverage. For `L>1`, `log(1/alpha)<log(L/alpha)`, so the DKW radius is strictly smaller than the Bonferroni--Hoeffding radius.

### Random candidate families chosen on selection data

Condition on `D_sel`. The candidate family and order are then deterministic, while `D_cert` retains its assumed law by independence. Each preceding proof applies conditionally with failure probability at most `alpha`. Integrating the conditional probability over `D_sel` preserves the bound.

If `D_cert` affects selection and only fixed-action bounds are used, the conditioning step is unavailable. CE07 exhibits a false-acceptance probability far above `alpha`. Simultaneous validity over the complete pre-selection universe or valid selective inference is therefore necessary.

Finally, population monotonicity does not turn a failed certificate into a successful one. A more conservative rung can be used only after its own valid certification, coverage by the same simultaneous event, or an independent safe premise.

**Status:** `FORMAL_PROOF_COMPLETE`; `NEW_COMBINATION_OF_CLASSICAL_RESULTS`.

## Proof of T-CF4

### Zero failures

For `X~Binomial(m,p)`, `P_p(X=0)=(1-p)^m`. The one-sided exact upper endpoint `U` solves

`(1-U)^m=alpha_l`,

so `U=1-alpha_l^(1/m)`. The condition `U<=delta` is equivalent to

`m>=log(alpha_l)/log(1-delta)`.

Taking the ceiling proves the exact integer threshold.

### Hoeffding safety and power

Set

`epsilon_m=sqrt(log(L/alpha)/(2m))`

and `U_l=hat r_l+epsilon_m`. Hoeffding's inequality gives

`P(r_l>U_l)<=exp(-2m epsilon_m^2)=alpha/L`.

The T-CF3 union argument therefore controls unsafe acceptance simultaneously by `alpha`.

For a safe rung `r_l=delta-gamma_l`, rejection implies

`hat r_l+epsilon_m>delta`,

hence

`hat r_l-r_l>gamma_l-epsilon_m`.

When the right side is positive, Hoeffding gives

`P(reject)<=exp[-2m(gamma_l-epsilon_m)^2]`; otherwise the trivial bound one applies. Requiring

`epsilon_m+sqrt(log(1/beta)/(2m))<=gamma_l`

makes the preceding probability at most `beta`. Multiplying by `sqrt(2m)` and squaring proves the sufficient sample formula.

### Bernoulli-KL inversion

For `hat r<delta`, the binomial lower-tail test of the composite unsafe null `p>=delta` has worst case at `p=delta` by stochastic monotonicity. Rejecting the null when that exact tail probability is at most `alpha_l` is therefore a valid fixed-action certificate. Chernoff's inequality upper-bounds the tail by

`exp{-m kl(hat r||delta)}`,

yielding the displayed sufficient KL rule. At a true risk `delta-gamma`, the leading exponent is `kl(delta-gamma||delta)`, proving the stated rate. Exact finite-sample use remains binomial inversion.

### Cost-optimal finite grid

For each integer `m` in a finite allowed set, exact binomial inversion determines `k_m`. At a design risk `r`, acceptance probability is `BinCDF(k_m;m,r)` and rejection probability is its complement. Therefore the displayed objective is an explicitly computable finite list and attains a minimum. Comparing adjacent objectives gives the marginal rule: purchase another label only when expected fallback-tax reduction exceeds its amortized truth cost.

**Status:** `FORMAL_PROOF_COMPLETE`; `CLASSICAL_APPLICATION`.

## Proof of T-CF5

On the T-CF3 simultaneous-validity event, every certified rung has risk at most `delta`. Selecting the smallest certified rung preserves that property. If none exists, the separate fixed-safe premise completes the pointwise statement. Therefore unsafe deployment is contained in the complement of the simultaneous event and has probability at most `alpha`.

Let `J` be the deployed rung when the certified set is nonempty. Direct fixed-safe search cost is `c_f`. The ladder search-cost difference is

`E[c_J 1{S_cert nonempty}+c_f 1{S_cert empty}]-c_f`

`=-E[(c_f-c_J)1{S_cert nonempty}]`.

Adding incremental evidence and control costs proves the exact economic condition. Expanding the expectation over disjoint events `{J=j}` gives the sum form.

For random query costs, apply the law of total probability to the events `{J=j}` and `{J=fixed}` to obtain the tail identity. Since inversion of a mixture CDF is nonlinear, no mean-cost inequality proves a p95 inequality. CE13 proves that a valid ladder can be economically worse than direct fixed-safe fallback.

No oracle label appears in the deployed definition of `J`; only certification outcomes and the external fixed-safe premise are used.

**Status:** `FORMAL_PROOF_COMPLETE`; `NEW_COMBINATION_OF_CLASSICAL_RESULTS`.

## Proof of T-CF6

The assumed Lipschitz inequality and the source margin give

`r_Gt(pi)<=r_Gs(pi)+L_d d(G_s,G_t)`

`<=delta-gamma+L_d d(G_s,G_t)`.

If `L_d d<gamma`, the final expression is strictly below `delta` and the target margin is at least `gamma-L_d d`.

Every T-CF4 sufficient Hoeffding count is decreasing in positive `gamma`. Thus any stable construction that strictly increases a valid lower bound on the target margin strictly decreases that sufficient bound. For exact binomial certification with a nontrivial cutoff, the acceptance event is decreasing in the number of failures. Binomial failure counts are stochastically increasing in risk, so strictly lower risk strictly raises acceptance probability whenever the acceptance event has probability strictly between zero and one. Fallback probability is one minus acceptance probability and therefore falls.

The result is conditional because neither `d` nor `L_d` has a validated deployable estimator in the frozen project.

**Status:** `FORMAL_PROOF_COMPLETE_CONDITIONAL`; `RESTRICTED_DOMAIN_PROPOSITION`.

## Finite verification map

The deterministic test module verifies:

- exact zero-failure CP formulas and thresholds;
- exact binomial inversion at nonzero failures;
- 14 required finite counterexamples;
- mean/quantile separation;
- Bonferroni versus fixed-sequence strict finite witness;
- small-margin sample growth;
- Bernoulli-KL positivity;
- finite-grid certification optimization;
- the eight fixed theory--experiment contract assumptions.
