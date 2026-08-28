# Fast theorem status

## T-OW0 — endpoint feasibility (`FORMAL_PROOF_COMPLETE`)

If every allowed constant budget has population risk strictly above
`delta_q`, then a policy restricted to that action set cannot satisfy the
risk requirement when it always selects one of those budgets. This population
statement is distinct from failure to certify an endpoint from finite data.

## T-OW1 — two-environment open-world lower bound (`RESTRICTED_PROPOSITION`)

For two environments on a finite budget grid, suppose their permitted probe
laws have total variation `v<1` and a positive-mass query set requires
different safe actions. Any randomized rule must either take an action unsafe
in at least one environment or conservatively choose the larger action. A
Le-Cam coupling yields a positive safety-plus-weighted-conservatism lower bound
scaled by `(1-v)` and the separated query mass. The fast version remains
restricted to two environments and finite grids; right censoring is represented
only by fallback and no universal multi-environment theorem is claimed.

## T-OW2 — query certificates do not imply build reliability (`FORMAL_PROOF_COMPLETE`)

Counterexample: let the observed builds all have zero risk under a policy and
let the meta-environment assign positive mass greater than `delta_b` to an
unobserved build on which the same policy has risk one. With no sampling or
relatedness assumption on builds, all observed query-level certificates hold
while the build-level deployment statement fails.

## Deferred results

T-OW3 is `PROOF_SKETCH`; T-OW4 is `CONJECTURE`; T-OW5 is
`NOT_ESTIMABLE` until build-level power is completed in Full Seal.
