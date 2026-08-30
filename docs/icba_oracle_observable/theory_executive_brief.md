# Oracle-observable theory closure: executive brief

## Decision

`NEGATIVE_POSITIVE_THEORY_CHAIN_CLOSED_RESTRICTED_GRAPH_ANNS`

The negative half is complete: T-OO2 shows positive oracle headroom can coexist with zero observable value, and T-OO3/T-OO8 give an observability-limited decision-loss lower bound and an adaptive transcript information requirement. The mathematics is an honest application of classical decision/testing theory, not a new Le Cam technique.

The positive half is conditional but formal: T-OO5 gives safe `2 epsilon_C` near-oracle selection under uniform risk/cost estimates and explicit margins; T-OO6 certifies only the independently selected action and falls back safely. Their combination yields RACS-P1–P3. It does not show that the current Graph-ANNS sentinel channel satisfies the assumptions.

## Main-paper allocation

1. **Main I:** T-OO3 plus the T-OO8 adaptive-transcript consequence.
2. **Main II:** T-OO5 plus T-OO6, including RACS.

T-OO1 is an identity, T-OO2 a decisive counterexample, T-OO4 appendix-only, and T-OO7 an evaluation principle. No third main theorem is justified.

## Gate summary

- Gate N, negative theory: **PASS**.
- Gate P, positive theory: **PASS_CONDITIONAL_FIXED_TARGET**.
- Gate M, lower/upper connection: **PASS_PARTIAL** only for a known binary finite-alphabet channel.
- Gate A, method derivation: **PASS_THEORETICAL_TEMPLATE**.
- Gate G, abstraction: **PASS_FORMAL_ABSTRACTION_ONLY**; no cross-domain empirical claim.

## Non-negotiable boundary

Do not claim a deployable recovery signal, open-world safety, matched general sample complexity, a new information-theoretic lower-bound method, or the first rebuild-portable ANNS method. The current defensible contribution is the unified safe recovery decision object, its oracle-observable gap, the ordered-budget/fallback instantiation, and a conditional certify-select-fallback closure.
