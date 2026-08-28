# Proof appendix

## T-OW0

Let `E` be the allowed finite action set and suppose `R_theta(e)>delta_q` for
every `e` in `E`. Any policy constrained to select a single constant action in
`E` has risk above `delta_q`. More generally, for a query-adaptive policy the
same conclusion requires the stronger pointwise or mixture condition; the
constant-action statement is the formally claimed endpoint proposition.

## T-OW1

Consider two environments with permitted probe laws `P0` and `P1`. Couple the
probe observations so they agree with probability at least `1-TV(P0,P1)`. On a
query set of mass `rho`, the smaller action is unsafe in environment 1 while
the larger action incurs conservatism cost at least `c` in environment 0. On
the coupled indistinguishable event a randomized rule cannot condition its
choice on the true environment. Summing the unsafe-choice probability and a
cost-weighted conservative-choice probability yields a positive lower bound
proportional to `rho*(1-TV(P0,P1))*min(1,lambda*c)`. The statement degenerates
correctly when TV is one, rho is zero, or the action separation cost is zero.
This proof is restricted to two environments and the finite action grid.

## T-OW2

Take any finite observed build set on which policy `pi` has zero risk. Define a
meta-environment distribution assigning mass `epsilon>delta_b` to a distinct
unobserved build where `pi` fails every query and the remaining mass to the
observed builds. Every observed query certificate remains true, while
`Pr_theta[R_theta(pi)>delta_q] >= epsilon > delta_b`. Therefore a build-level
claim needs a build-sampling or relatedness assumption.

## T-OW3--T-OW5

T-OW3 follows as an event union bound after endpoint, base, support and probe
failure events are fixed, but the frozen design does not identify all numerical
terms. T-OW4 is not retained for Z0/Z1 because the empirical recovery Gate
fails. T-OW5 remains a proof sketch: query count, independent build count,
target probes and policy-family size enter different concentration or testing
terms and cannot be collapsed into the 648 directed-pair count.
