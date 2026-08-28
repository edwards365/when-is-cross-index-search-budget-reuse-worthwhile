# T-OW3 revised risk decomposition

The previous expression `R_deploy <= R_endpoint + R_base + R_support + R_probe` is valid only after each term is defined as the probability of a failure event whose union contains deployment failure. Names alone do not establish that containment, and overlapping events make the sum descriptive rather than an identity.

## Formal union-bound proposition

Let `E` be endpoint infeasibility, `S` support/model misspecification, `P` probe/fingerprint identification failure conditional on `E^c∩S^c`, and `B` base-policy allocation failure conditional on `E^c∩S^c∩P^c`. If deployment failure `F` satisfies

`F subset E union S union P union B`,

then

`Pr(F) <= Pr(E)+Pr(S∩E^c)+Pr(P∩E^c∩S^c)+Pr(B∩E^c∩S^c∩P^c)`.

This disjoint sequential form is sharper and semantically clearer than summing four marginal probabilities. It is `FORMAL_PROOF_COMPLETE` by partition and monotonicity of probability, conditional on the event-containment premise.

## Excess-risk and regret forms

For a comparator policy `pi*`, excess risk can be telescoped through intermediate policies that successively replace endpoint, support, probe and base components. The signed increments may interact and need not be nonnegative. A regret decomposition similarly requires a scalar loss combining safety and cost. Neither form justifies a universal additive nonnegative four-factor bound without additional assumptions.

## Empirical attribution

Shapley values average marginal contrasts over factor orderings. Paired build contrasts compare observed cells. Both are descriptive under the frozen design; they are not causal effects because factors were not independently randomized and interactions remain. The empirical table must therefore use `DESCRIPTIVE_ATTRIBUTION`, never `CAUSAL_COMPONENT`.

## Status

T-OW3 is retained as a `RESTRICTED_PROPOSITION`: the event theorem is formal, but the frozen data do not identify every conditional component or verify the containment premise for all implementations. The old unconditional linear display is withdrawn as a general claim.
