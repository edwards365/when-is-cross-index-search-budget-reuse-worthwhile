# Assumption audit

| Assumption | Used by | Necessity/failure mode | Graph-ANNS status |
|---|---|---|---|
| one fixed action class and safety semantics | T-OO1 | changing the feasible class invalidates value comparison | locked in formulation |
| explicit environment pair/class | T-OO2/3/4/8 | minimax claim is otherwise undefined | finite witness only |
| disjoint decision regions with loss gap `Delta` | T-OO3 | shared near-optimal action can remove testing difficulty | constructible; not globally estimated |
| valid transcript law | T-OO3/8 | wrong adaptive likelihood invalidates KL calculation | theoretical only |
| per-step KL cap or positive KL query | T-OO8 | `I*=0` blocks recovery; unknown channel blocks rate | positive deployable value not established |
| finite action set | T-OO5/RACS | uniform finite selection statement otherwise changes | satisfied by candidate template |
| joint uniform risk/cost event | T-OO5 | marginal intervals alone need not hold simultaneously | not verified |
| optimal-action risk slack `>=2 epsilon_R` | T-OO5 | zero margin prevents stable safe inclusion | not verified |
| unique cost margin `>2 epsilon_C` | exact T-OO5 recovery | ties invalidate exact-label claim | not verified; decision regret preferred |
| safe fallback | T-OO2/5/6/RACS | maximum budget may be endpoint-infeasible | must be separately justified |
| independent selection/certification | T-OO6/RACS | reuse invalidates conditional fixed-action proof | required future protocol |
| iid/exchangeable certification unit | Clopper-Pearson part of T-OO6 | wrong unit changes coverage | fixed-target query unit only |
| complete total-cost units | T-OO5/6/RACS | unknown truth/training costs can reverse gain | unknown; retained symbolically |
| explicit meta-law `Pi` | meta-average/build claim | fixed builds do not define environment probability | absent |
| support/regularity for unseen builds | open-world upper bound | current-target evidence does not cover new support | absent |

## Safety semantics audit

Fixed-target, meta-average, and open-world uniform safety are never substituted. Counterexamples C5 and C6 prove the non-implications. Query resampling does not create independent builds. Endpoint infeasibility is part of absolute failure and cannot be hidden by calling the maximum observed budget a fallback.

## Stop conditions

Positive deployment claims stop if no separately safe fallback exists, the certification split influences selection, cost units are incompatible, or the target observation channel lacks a valid sampling law. Open-world claims stop until a support/regularity or exchangeable-build model is supplied.
