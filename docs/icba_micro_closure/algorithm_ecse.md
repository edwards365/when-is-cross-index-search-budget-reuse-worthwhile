# Environment-Confidence Safe Envelope (ECSE)

## Frozen interface

ECSE is a closed-world finite-environment construction. Its inputs are a finite environment library, one frozen budget response `B_hat_theta(x)` per environment, a preregistered sentinel sequence, target sentinel responses, confidence level `alpha`, query-risk target `delta_q`, a fixed safe endpoint `e_safe`, and deployment workload `N`. The sentinel queries are disjoint from evaluation queries. Target evaluation truth and per-query target Oracle budgets are never inputs.

Given the first `k` sentinel responses, an environment-set constructor returns `C_hat_k`. ECSE requires a proved or exact finite-family guarantee

`Pr_theta(theta in C_hat_k) >= 1-alpha`.

If this guarantee is unavailable, the set is empty, or any candidate lacks a valid budget response, ECSE fails closed to `e_safe`. Otherwise it allocates

`b_hat_k(x)=max_{theta in C_hat_k} B_hat_theta(x)`.

Sentinel search, truth acquisition, confidence construction and controller work are included in amortized total cost. A source per-query Oracle budget may be evaluated only in a separately labeled upper-bound lane.

## T-M4: information monotonicity

If (i) the confidence sets are nested, `C_hat_{k+1} subseteq C_hat_k`; (ii) all environment budget responses are frozen; (iii) the same safe fallback is used; and (iv) both sets are valid and nonempty, then the envelope allocation and its query execution cost are pointwise nonincreasing in `k`. Consequently the execution-only portability tax is nonincreasing. This does **not** imply that total cost is monotone: sentinel and truth-acquisition cost can make the probe-adjusted objective increase.

Without nested sets the claim is false: two valid nonnested sets can exchange a low-budget environment for a high-budget environment and enlarge the envelope. This restriction is part of the theorem rather than repaired after experiments.

## T-M5: finite-sample safety

Assume a fixed target environment in the closed-world library, an independent new evaluation query, confidence-set coverage at least `1-alpha` over sentinel sampling, and a frozen target response satisfying

`Pr_X[B_hat_theta(X) < B*_theta(X)] <= delta_q`.

On the coverage event, the envelope is no smaller than `B_hat_theta`, hence its query risk is at most `delta_q`. Therefore

`Pr_sentinel[R_theta(ECSE_k) <= delta_q] >= 1-alpha`.

The outer probability is over sentinel sampling; the inner risk is over a new query. There is no probability statement over a novel environment unless an explicit hierarchical environment model is supplied. In open-world leave-one-build-out, the result applies only if the confidence constructor proves that the unknown target is safely dominated by a retained representative. Otherwise the lane is an empirical design simulation, not a certified deployment result.

If `e_safe` itself is not safe, fail-closed execution cannot satisfy this theorem. This is why the GloVe boundary from Gate E0 cannot be hidden by the controller.

## T-M6: cost bound

Let normalized budget cost be 1-Lipschitz, let `D` bound the largest response difference across the library, and let `diam(C,x)=max_{theta in C} B_hat_theta(x)-min_{theta in C} B_hat_theta(x)`. Relative to a target-aware response, ECSE's expected execution excess obeys

`T_k-T_oracle <= D Pr(theta notin C_hat_k) + E[diam(C_hat_k,X) 1{theta in C_hat_k}] + fallback_gap Pr(fail_closed)`.

The full objective additionally contains `(A_sentinel+A_truth+A_cert)/N`. For iid sentinel responses and a finite correctly specified library, likelihood confidence sets can have environment-exclusion error bounded by a library factor times `exp(-k C_min)`, where `C_min` is an appropriate pairwise Chernoff-information separation. The precise factor and threshold belong to the chosen finite-family test; this sprint does not claim a distribution-free exponential rate.

## T-M7 matching target

The preregistered matching class is a finite two-environment model with aligned budget responses, binary iid sentinel observations, a nested exact likelihood confidence set and a common safe endpoint. Source-only minimax loss is controlled below by the overlap--separation theorem. ECSE's execution regret is controlled above by the environment-error term plus confidence-set diameter. Synthetic Phase 4 must calculate the exact minimax value and lower/upper ratio; until that calculation succeeds, matching and Gate G2 remain pending.

## Lane labels

- Frozen deployable inputs plus target aggregate sentinels: `DEPLOYABLE_ECSE_LANE`.
- Exact labels on sentinel queries with acquisition charged: `LABELED_TARGET_SENTINEL_LANE`.
- Per-query source stable budget: `NON_DEPLOYABLE_SOURCE_ORACLE_UPPER_BOUND`.
- Per-query target sufficient budget: `NON_DEPLOYABLE_TARGET_ORACLE`.

No design replay from this sprint is confirmatory performance evidence.
