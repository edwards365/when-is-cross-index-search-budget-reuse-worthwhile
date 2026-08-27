# ICBA theory-to-method interface

## Restriction that a future method must escape

T2 and T3 apply when the action is measurable only with respect to a source-build summary, optionally under a monotonicity restriction. A future method should therefore acquire target-native information during the actual search. Merely adding a richer predictor trained on the same source labels does not escape the information partition and cannot defeat its safe envelope.

## Minimal method contract

1. **State:** use a frozen, read-only statistic of the target search filtration, such as frontier progress or result stability; do not assume it is sufficient.
2. **Execution:** support resumable checkpoints so observation cost is incremental rather than a sequence of full reruns.
3. **Fallback:** retain a fixed safe budget and include its cost in the deployed policy.
4. **Risk unit:** certify the full stopping policy, including checkpoint choice, fallback, and any model selection—not individual checkpoints in isolation.
5. **Accounting:** report native implementation-local work, probe overhead, state extraction, calibration, rebuild, and amortization.
6. **Evidence:** freeze design/calibration/confirmation membership before reading confirmation outcomes; never tune after confirmation.

## Derivation sequence

First test whether a target-native state refines source aliases and changes the conditional budget distribution. Next determine whether prefix execution is exactly equivalent to native search and whether state extraction is non-invasive. Then solve the finite-grid risk allocation on design data, freeze one complete policy, and calculate its exact certification power before confirmation. A method is worth confirmation only if the expected saving remains positive after all online and amortized costs and if the available sample size gives non-negligible power at the chosen multiplicity.

## Current handoff decision

The theory supports method derivation conceptually but does not authorize an implementation run in this sprint. The prior Signal Pilot found good ranking signal but zero certified policies; therefore the next method phase must improve target-native information or reduce policy multiplicity under a fresh preregistration, not retune RCRS on the frozen results.
