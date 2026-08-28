# T-OW1: information-constrained safety–conservatism bounds

## T-OW1a (two-environment Z0 theorem)

Let `B` be a finite ordered budget set and let a randomized policy observe `(x,Z0)` before choosing a budget or fallback. Suppose two environments have the same query law `P` and observation laws `Q0,Q1`. Let `A` have `P(A)>=rho`. For every `x in A`, assume monotone loss, finite minimal safe budgets, and

`b*_1(x) >= b*_0(x)+Delta`, with `Delta>0` in the chosen budget metric.

Classify an action on `A` as:

- high-environment under-budget if it is below `b*_1(x)` and is not a separately certified-safe fallback;
- low-environment conservative/fallback if it is at least `b*_1(x)` or invokes fallback.

Then every randomized policy satisfies

`U_1(pi;A) + CF_0(pi;A) >= rho * (1-TV(Q0,Q1))`,

where both terms are unconditional probabilities over queries, observations and policy randomization. If every conservative/fallback action on `A` costs at least `gamma(x)>0` above the low-environment safe action, then

`U_1(pi;A) + E_0[excess_cost * 1_A]/gamma >= rho*(1-TV(Q0,Q1))`

for any valid uniform lower cost gap `gamma`; equivalently use the dimensionless conservative-event form above when no uniform monetary gap exists.

For Z0-identical environments, TV is zero. The result is not “novel because it uses TV”: its project-specific content is the ordered one-sided action conflict, explicit fallback branch, and conversion of testing error into an under-budget versus conservative-cost tradeoff.

## T-OW1b (finite target probes)

With `k` target probes having joint observation laws `Q0^(k),Q1^(k)`, the same bound holds with `TV(Q0^(k),Q1^(k))`. Under iid probes this is the TV of product measures. Pinsker gives the weaker but explicit form

`U_1 + CF_0 >= rho * max(0, 1-sqrt(k*KL(Q0||Q1)/2))`.

Thus increasing `k` can reduce environment-testing ambiguity. It cannot repair an omitted environment, an incorrect observation-to-budget relation, a missing safe endpoint, or an unavailable source policy. Labeled probes (`Z2`) and unlabeled probes (`Z1`) induce different `Q` and must never be exchanged. Probe acquisition and runtime cost are added to total cost.

## Multi-environment conclusion

A two-environment witness already proves the requested arbitrary-open-world impossibility because any larger class containing the witness inherits its minimax lower bound. Fano/Assouad are unnecessary for that conclusion. A K-environment packing would only sharpen dependence on identification among many candidates and is therefore deferred rather than presented as artificial generality.

## Matching upper-bound assessment

Closed-world ECSE is not a matching upper bound to the arbitrary-open-world lower bound. It assumes candidate support, labeled target sentinels, a per-query source Oracle, finite-grid rounding and fallback conventions. The remaining gap is structural, not merely a loose constant. Under a correctly specified finite candidate set, environment testing plus conservative envelopes may approach the two-point rate; that restricted statement is not established here as a general theorem.
