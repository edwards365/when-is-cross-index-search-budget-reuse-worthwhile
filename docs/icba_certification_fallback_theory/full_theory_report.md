# ICBA certification--fallback positive theory closure

## Decision

The fixed-target theory closes under explicit independence, absolute endpoint-aware safety, a valid safe terminal action, compatible cost units, and positive safety/cost margins. The resulting label is

`POSITIVE_RECOVERY_THEORY_CLOSED_FIXED_TARGET`.

This is not an open-world recovery result and does not authorize a validated algorithm claim. Its highest novelty level is `NEW_COMBINATION_OF_CLASSICAL_RESULTS`.

## T-CF1 -- Certification--Fallback Tax identity

Let `Pi_S` be the candidate selected without certification data, and let `R` be the certification rejection indicator. The actual deployed search mean is

`E[mu_G(Pi_D)]=E[mu_G(Pi_S)]+E[R{mu_G(pi_f)-mu_G(Pi_S)}]`.

With

`Delta C_f=E[mu_G(pi_f)-mu_G(Pi_S)|R=1,G]`,

the total per-business-query deployment cost is exactly

`C_deploy=E[mu_G(Pi_S)]+C_evidence/N+P(R)Delta C_f+C_control`.

The identity remains true under an explicit joint environment law after taking one more expectation over `G`; it is otherwise conditional on the named target. If the fallback gap is deterministic, this reduces to the prompt's displayed form.

Relative to the oracle, define

`R_selection=E[mu_G(Pi_S)-mu_G(pi_star)]`,

`T_certification=C_evidence/N`,

`T_fallback=E[R{mu_G(pi_f)-mu_G(Pi_S)}]`,

and `T_control=C_control`. Then

`C_deploy-C_oracle=R_selection+T_certification+T_fallback+T_control`.

The selection term can be negative if an unsafe candidate is cheaper than the safe oracle; nonnegativity requires restricting the comparison to safe actions. The equality is a bookkeeping identity, classified `IDENTITY_OR_DEFINITION`, not a major new theorem.

Two finite counterexamples are exact:

1. Baseline 10, oracle 8, evidence 300 and `N=100` give positive oracle headroom 2 but deployed cost 11 and net gain -1.
2. Baseline cost is always 10. Recovery cost is 0 on 94% of queries and 11 on 6%. Its mean is 0.66, but its p95 is 11 rather than 10.

## T-CF2 -- When recovery has positive net value

Substituting T-CF1 into `C_B-C_deploy` gives the exact net gain

`G_net=G_oracle-R_selection-C_evidence/N-P(R)Delta C_f-C_control`.

Hence recovery is worth deploying in mean if and only if

`G_oracle>R_selection+C_evidence/N+P(R)Delta C_f+C_control`.

Let

`D=G_oracle-R_selection-P(R)Delta C_f-C_control`.

If `D>0`, strict positive value holds exactly when

`N>N_star=C_evidence/D`.

At equality the rule only breaks even. If `D<=0`, the disposition is

`NO_FINITE_BREAK_EVEN_WORKLOAD`.

For any two actions `a,b`, write total costs as `M_a+K_a/N` and `M_b+K_b/N`, where `M` contains recurrent search, fallback, and control components and `K` contains evidence/training overhead. Target retraining is preferred to reuse or recalibration precisely when it is certified safe, passes the tail gate, and

`M_train+K_train/N < M_j+K_j/N`

for every competing action `j`. In the common case `K_train>K_j` and `M_train<M_j`, the pairwise threshold is

`N>(K_train-K_j)/(M_j-M_train)`.

Direct fixed-safe fallback is optimal when no candidate is certified, no safe candidate passes the tail gate, or every candidate has a nonpositive value denominator relative to fallback.

Increasing budget from rung `l` to `j>l` is economically beneficial despite a search increment `Delta mu>0` whenever

`Delta mu + {p_j Delta_f,j-p_l Delta_f,l} + Delta C_control + Delta C_evidence/N < 0`.

Thus a small conservative search increase can reduce total cost by sharply lowering certification rejection/fallback incidence. Mean positivity and p95 acceptability are separate constraints.

## T-CF3 -- Strictly safe ordered certification

### Bonferroni simultaneous bounds

For each rung construct a one-sided fixed-action upper confidence bound `U_l` satisfying

`P(U_l<r_l)<=alpha/L`.

The union bound gives

`P(for all l, r_l<=U_l)>=1-alpha`.

Choosing

`hat l=min{l:U_l<=delta}`

and otherwise using a valid fixed-safe policy therefore yields

`P(r_G(Pi_D)<=delta)>=1-alpha`.

### Fixed-sequence gatekeeping

Test rungs in the predetermined order `L,L-1,...,1`, each at level `alpha`, and stop at the first rung that is not certified. Deploy the smallest rung certified before that stop. Under nested risk, the unsafe nulls form an initial segment. Rejecting any unsafe null requires rejecting the first unsafe null encountered in the fixed order, whose marginal probability is at most `alpha`. This proves strong unsafe-deployment control without dividing alpha by `L`.

With the same certification queries, pointwise nested failure counts, and a confidence bound monotone in both failure count and confidence level, fixed sequence is samplewise no more conservative than Bonferroni. It is strictly more powerful for configurations such as zero failures, `m=59`, `delta=.05`, `alpha=.05`, `L=10`: the single/fixed-sequence CP bound certifies, while the Bonferroni CP bound does not.

### Nested simultaneous band

Under query-level nesting, `Z_l=1{S>l}`. Let `hat r_l` be the empirical survival function of `S` on `m` independent certification queries. The one-sided Dvoretzky--Kiefer--Wolfowitz inequality gives

`P(for all l, r_l<=hat r_l+epsilon_DKW)>=1-alpha`,

where

`epsilon_DKW=sqrt(log(1/alpha)/(2m))`.

This radius is strictly smaller for `L>1` than the Bonferroni--Hoeffding radius

`sqrt(log(L/alpha)/(2m))`.

The proven advantage is restricted to the locked finite ordered family evaluated on the same iid certification queries. It is not a universal power dominance over exact binomial, closed-testing, or adaptive procedures.

### Data roles and fallback transfer

The candidate family and order may be random functions of `D_sel`. Conditional on `D_sel`, they are fixed, so any simultaneous band valid for that fixed family remains valid on independent `D_cert`; integrating over `D_sel` proves the unconditional fixed-target statement.

Using `D_cert` to select the family or order and then applying a fixed-action certificate can fail. It is legal only when the bound is simultaneous over the complete pre-selection universe or is selection-aware.

Certification rejection of rung `l` does not certify rung `j>l`. Transfer is legal only when `j` is covered by a simultaneous valid event, is separately tested by a valid gatekeeping procedure, or is independently known safe. If no rung is certified, `fixed-safe` means an externally justified safe policy; otherwise the correct action is abstention.

## T-CF4 -- Safety margin and sample complexity

Let `gamma_l=delta-r_l`.

For zero failures, the exact one-sided Clopper--Pearson upper endpoint is

`U(0,m,alpha_l)=1-alpha_l^(1/m)`.

Thus

`m_min=ceil(log(alpha_l)/log(1-delta))`,

where `alpha_l=alpha/L` for Bonferroni and `alpha_l=alpha` for one selected action or a fixed-sequence rung. At `alpha=.05`, a single action requires 29, 59, and 299 zero-failure queries for `delta=.10,.05,.01`.

The Bonferroni--Hoeffding bound is

`U_l=hat r_l+sqrt(log(L/alpha)/(2m))`.

If `r_l=delta-gamma_l` and a false-rejection probability at most `beta` is requested, a sufficient condition is

`m >= {sqrt(log(L/alpha))+sqrt(log(1/beta))}^2/(2 gamma_l^2)`.

This implies the requested rate

`m=O(log(L/alpha)/gamma_l^2)`

when `beta` is fixed. The unsafe-accepted probability is at most `alpha` simultaneously. The safe-but-rejected probability is bounded by

`exp[-2m{gamma_l-sqrt(log(L/alpha)/(2m))}_+^2]`,

with the convention that the bound is one when the bracket is nonpositive.

For Bernoulli-KL inversion, certify rung `l` when the binomial lower-tail p-value under `p=delta` is at most `alpha_l`, equivalently by a KL/Chernoff approximation

`m kl(hat r_l||delta)>=log(1/alpha_l)` with `hat r_l<delta`.

Its leading sample requirement at risk `delta-gamma_l` is

`log(1/alpha_l)/kl(delta-gamma_l||delta)`.

Exact deployment uses binomial/Clopper--Pearson inversion, not only the asymptotic expression.

The query count `m`, candidate-policy count `L`, historical-build count, and number of budget levels are different objects. This theorem has no historical-build sample-complexity conclusion.

For truth cost `C_truth` and fallback gap `Delta C_f>=0`, an exact finite-grid design is

`m_star=argmin_{m in M}{m C_truth/N+p_reject(m,gamma)Delta C_f}`.

For a design risk `r=delta-gamma`, compute the largest accepted failure count `k_m` by exact binomial inversion and use

`p_reject(m,gamma)=1-BinCDF(k_m;m,r)`.

The grid is finite, so a minimizer exists. One more label is worthwhile only when its reduction in expected fallback tax exceeds `C_truth/N`.

## T-CF5 -- Ordered fallback ladder

Let `S_cert` be the set of rungs certified by a simultaneous or valid gatekeeping rule, and define

`J=min S_cert`,

with `J=fixed` when `S_cert` is empty. On the simultaneous-validity event every selected candidate is safe; the terminal fixed policy is assumed separately safe. Hence the ladder inherits the `1-alpha` fixed-target safety guarantee.

Relative to direct fixed-safe deployment with mean cost `c_f`, the ladder's expected search saving is

`E[(c_f-c_J)1{S_cert nonempty}]`.

Including incremental evidence/control costs, the ladder is strictly better precisely when

`sum_j P(J=j)(c_f-c_j) > C_evidence/N+Delta C_control`.

If every `c_j<=c_f`, the left side is nonnegative; strict value still requires positive acceptance probability, a positive gap on an accepted rung, and enough workload. Safety margin raises acceptance probability, while fallback gap determines the value of acceptance.

For random query cost, the tail identity is

`P(C_D>t)=sum_j P(J=j)P(C_j>t|J=j)+P(J=fixed)P(C_f>t|J=fixed)`.

The p95 is the quantile of this mixture, not the weighted average of component p95 values. A ladder can remain safe yet fail economically: if a cost-9 rung is accepted with probability .5, fixed-safe costs 10, and evidence tax is 1.5 per business query, ladder total cost is 11 rather than 10.

## T-CF6 -- Stable-by-construction interface

Assume, but do not infer from current metadata, that

`|r_Gs(pi)-r_Gt(pi)|<=L_d d(G_s,G_t)`.

If source risk satisfies `r_Gs(pi)<=delta-gamma` and

`L_d d(G_s,G_t)<gamma`,

then

`r_Gt(pi)<=delta-{gamma-L_d d(G_s,G_t)}<delta`.

The target margin is at least `gamma_t=gamma-L_d d`. Substitution into T-CF4 lowers the sufficient certification count from a bound proportional to `1/gamma_0^2` to one proportional to `1/gamma_t^2` whenever the stability construction produces a strictly larger certified lower bound on margin. For a fixed nontrivial binomial acceptance cutoff, a smaller target risk strictly increases acceptance probability and lowers fallback probability by stochastic ordering.

No deployable `d(G_s,G_t)` is validated. Z0 and existing Z1 recovery channels failed their gates. T-CF6 is therefore a conditional interface, not evidence that open-world positive recovery is solved.

## Closure summary

All six results have complete proofs at their stated scope. T-CF1 and much of T-CF2 are cost accounting; T-CF3--T-CF5 combine classical certification, ordered testing, and fallback economics; T-CF6 is conditional. Fourteen finite counterexamples pass deterministic verification. The method template is authorized only as a theoretical/pre-registration interface for future nonsealed experiments.
