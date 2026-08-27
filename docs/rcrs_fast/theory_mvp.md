# RCRS Fast Sprint theory MVP

## Optimal safe monotone transfer

For observed pairs `x_i=B_s(q_i)` and `y_i=B_t(q_i)`, first merge equal source budgets and assign each source level the maximum target budget in its tie class. Sort the distinct source levels. The pointwise smallest nondecreasing map satisfying `f(x_i)>=y_i` is the prefix maximum of these tie-class maxima. Feasibility follows immediately. Any feasible nondecreasing map at level `j` must dominate every target requirement at levels `k<=j`, hence must dominate their maximum; the prefix construction attains that lower bound at every level and therefore minimizes every coordinatewise nondecreasing cost objective, including the observed target NDC evaluated at the allocated frozen budget. Budget differences are not reported as NDC taxes.

If `x_i<=x_j` but `y_i>y_j`, monotonicity and safety imply `f(x_j)>=f(x_i)>=y_i`, hence `f(x_j)-y_j>=y_i-y_j`. Summing over query-disjoint inversion pairs yields a valid budget-gap lower bound. The implementation computes the exact maximum-weight disjoint matching as a binary linear optimization. This matching bound can be loose; the exact empirical monotone tax is obtained from the prefix-majorant allocation and the target graph's measured NDC curve.

This result constrains only nondecreasing policies whose online input is the scalar source budget. It does not constrain target-native search-state policies such as the proposed RCRS. A raw inversion rate is not a cost bound: inversion gaps and target NDC curves determine cost.

## Zero-failure certification lower bound

For `n` independent sentinel queries with no observed failure, a true failure probability greater than `delta` produces zero failures with probability at most `(1-delta)^n`. Requiring this probability to be at most `alpha` gives `n>=ceil(log(alpha)/log(1-delta))`: 59, 299 and 2995 for `(delta,alpha)=(.05,.05),(.01,.05),(.001,.05)`. With calibration cost `A(n)`, fixed cost `C_fixed` and online cost `C_online`, break-even is `N*=A(n)/(C_fixed-C_online)` when the denominator is positive; otherwise it is `NO_FINITE_BREAK_EVEN_WORKLOAD`.

No complete RCRS risk theorem is claimed in this sprint. A later theorem must calibrate an entire finite sequential stopping policy end-to-end under exchangeability and distinguish marginal under-target risk from per-query deterministic safety.

