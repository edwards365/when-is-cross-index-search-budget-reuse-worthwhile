# TCP certified graded fallback: formal scope

## Setting

Fix a target graph build and a finite ordered family of policies
`Pi=(pi_1,...,pi_K)` before reading the target certification sample. A policy
may depend on source-build data, but not on target certification or evaluation
outcomes. Let `R_j=P(Z(pi_j)=1)` be its target query failure probability, where
`Z` is the frozen failure event, and let `U_j` be a valid one-sided
`(1-alpha/K)` upper confidence bound computed from the common target
certification sample. Define

`J = min {j : U_j <= delta}`,

and refuse deployment if this set is empty.

## Proposition TCP-CF1: simultaneous selected-policy safety

With probability at least `1-alpha` over the target certification sample,
every reported bound covers simultaneously and therefore, whenever deployment
occurs, `R_J <= delta`.

### Proof

For each fixed policy, validity gives
`P(R_j > U_j) <= alpha/K`. By the union bound,

`P(exists j: R_j > U_j) <= sum_j alpha/K = alpha`.

On the complementary event, all risks are bounded by their reported upper
bounds. The selected index satisfies `U_J <= delta`, hence
`R_J <= U_J <= delta`. This argument permits arbitrary dependence among the
bounds caused by reuse of the same certification queries. It requires only
that the policy family and ordering be fixed independently of those queries.

Status: **FORMAL_PROOF_COMPLETE** for fixed-target query risk and a finite,
pre-specified policy family.

## Corollary TCP-CF2: canonical three-rung deployment

Set `K=3` and order the policies as canonical TCP-HM9-TC, source-only global
fixed budget, and fixed-safe endpoint. Using one-sided Clopper--Pearson bounds
at confidence `1-alpha/3` gives a familywise `1-alpha` certificate for the
deployed action on each target build.

Status: **CLASSICAL_APPLICATION** of exact binomial bounds and Bonferroni's
union bound. This is not presented as a new statistical theorem.

## Proposition TCP-CF3: fallback cost decomposition

Let `C_j` denote query cost under rung `j`. Conditional on a completed and
valid certification procedure,

`E[C_J] = sum_j P(J=j) E[C_j | J=j]`.

Thus replacing a binary `pi_1 -> pi_K` fallback with an intermediate certified
policy can reduce mean and tail cost without changing the risk threshold. The
claim is an accounting identity; an efficiency improvement requires empirical
evidence about selection probabilities and conditional cost distributions.

Status: **FORMAL_PROOF_COMPLETE** as an identity; efficiency is empirical.

## Power and scope boundaries

Bonferroni validity is purchased with lower per-policy power. Adding rungs is
not automatically beneficial: it can increase fallback options while making
each certificate more conservative. The three-rung family is therefore frozen
before evaluation rather than selected from a larger ladder after seeing
results.

The propositions certify query risk for one fixed target build. They do not
certify transfer to a random future build, do not convert the nine source
builds into a 5% build-level conformal claim, and do not prove p95 or p99 cost
bounds. Cross-build robustness, tail behavior, and lifecycle economics remain
separate empirical Gates.

## Assumption-to-implementation map

| Formal condition | Implementation evidence |
|---|---|
| Policies fixed before target certification | Phase 3b preregistration and commit `7eba48b` |
| Target evaluation excluded from selection | Frozen query-role split; evaluator reads it only after certification |
| Common certification sample allowed | TCP, ef80 and ef200 all use qid 0--499 |
| Simultaneous per-build confidence | CP confidence `1-0.05/3`; all selected UCBs <=0.05 |
| No action if all bounds fail | Implementation raises an invalid-protocol error |
| No build-distribution claim | Decision outputs set `formal_build_certificate=false` |
