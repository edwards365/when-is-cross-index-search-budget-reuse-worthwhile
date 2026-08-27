# Four locked ICBA results

## I. Information-Constrained Adaptation and Zero-Tax Characterization

The least zero-risk action measurable from source summary X is the conditional essential supremum of target demand. Under integrable strictly increasing cost, its information tax is zero exactly when target demand is measurable from X almost surely. Refining information weakly lowers optimal value by feasible-class inclusion. Status: `FORMALLY_PROVED UNDER EXPLICIT CONDITIONS`.

## II. Exact Safe Monotone Portability Tax and Barrier Decomposition

The least safe nondecreasing mapping is the tied-level maximum followed by prefix maxima. Under strict cost its tax is zero exactly when target demand is almost surely a nondecreasing function of source demand. For query-specific discrete costs, monotone-minus-target cost equals the sum of incremental costs of every forced crossed barrier. Status: barrier theorem `FORMALLY_PROVED`; matching lower bound `PROVED_UNDER_EXPLICIT_CONDITIONS_RESTRICTED_PROPOSITION`.

## III. Risk-Matched and Certification-Aware Adaptation

Population risk-matched value and finite-sample certification are distinct. For a frozen policy, exact binomial certification yields a random deployment event; fail-closed expected cost is `Pcert*C_online+(1-Pcert)*C_fixed+A/N`. Certification tax is nonnegative only under policy containment and cost conditions stated in the detailed proof. Status: `FORMALLY_PROVED UNDER EXPLICIT CONDITIONS`.

## IV. Cost-Adjusted Value of Target-Side Sequential Information

Nested target information weakly reduces the decision component, but acquisition cost increases with checkpoints, so total cost need not be monotone. The finite-state Bellman interface is valid only for finite Markov/known-transition Lagrangian problems. Status: information result `FORMALLY_PROVED`; dynamic-programming interface `PROVED_UNDER EXPLICIT CONDITIONS`; frozen trace contact `EMPIRICAL_ONLY NON_DEPLOYABLE_ORACLE`.

Complete proofs, assumptions, empirical protocols, and boundaries are in `main_result_1.md` through `main_result_4.md` and `counterexamples_and_boundaries.md`.
