# ICBA oracle-observable recovery theory closure

## 1. Audit outcome

This stage closes the requested mathematical chain without accessing either sealed split and without running new Graph-ANNS experiments. Formal statements and proofs are in `theory/icba_oracle_observable/`; exact finite enumeration is in `tests/icba_oracle_observable/`.

The final label is `NEGATIVE_POSITIVE_THEORY_CHAIN_CLOSED_RESTRICTED_GRAPH_ANNS`. “Closed” means that the same fixed-target finite-action model contains (i) an information lower bound, (ii) a margin-based conditional upper bound, and (iii) a simple certified fallback consequence. It does **not** mean the current Graph-ANNS observations satisfy the recovery assumptions.

## 2. Unified decision object

An environment `theta` fixes a query law, ordered budget response, absolute safety event, and action costs. The outer action is reuse, recalibrate, retrain, or fallback; the inner action chooses a query budget. Information is nested as

`I_0 subseteq I_m subseteq I_theta`.

For one unchanged action class and safety semantics, `R_0`, `R_m`, and `R_theta` are optimal total costs. The decomposition

`H_oracle = R_0-R_theta = (R_0-R_m)+(R_m-R_theta) = H_obs+G_id`

separates opportunity from recoverability. Evidence and offline cost are included as symbolic amortized terms, so information refinement lowers the decision component but need not lower total acquisition-adjusted cost.

## 3. Negative chain

### T-OO2

Two indistinguishable environments have mutually unsafe cheap actions and one safe fallback. The oracle costs zero, while every observable pointwise-safe rule costs one. This proves `H_oracle=1`, `H_obs=0`, and `G_id=1` for every evidence count.

### T-OO3

Any rule whose environment-specific good decision regions are disjoint induces a binary test. For equal prior and loss separation `Delta`, the average and hence maximum loss is at least

`Delta/2 [1-TV(P_0^m,P_1^m)]`.

The prior-weighted form is the Bayes testing integral. Bretagnolle-Huber and Pinsker give the stated KL forms. Randomization is covered by Markov-kernel contraction. Adaptive probes are covered by the conditional KL chain rule; iid tensorization is not assumed.

### T-OO8 lower side

If both terminal errors are at most `beta`, data processing requires transcript KL at least `kl(1-beta,beta)`. A per-step information cap `I*` therefore implies `m I*` exceeds that quantity. With `I*=0`, no sentinel count helps. This remains a lower bound for the current Graph-ANNS instantiation because positive deployable decision information has not been established.

## 4. Positive chain

### T-OO5

On a joint event with uniform cost error `epsilon_C` and risk error `epsilon_R`, upper-confidence safe screening never includes an unsafe action. If the optimal safe action has slack at least `2 epsilon_R`, it remains available and selected cost is within `2 epsilon_C`. Exact action recovery additionally requires a unique cost optimum with margin exceeding `2 epsilon_C`.

The statement handles ties by set recovery, treats endpoint-infeasible actions as excluded or absolutely unsafe, and permits correlated estimates only when the joint event is valid. Adaptive data require time-uniform or design-valid bounds.

### T-OO6

Condition on the selection split. The chosen action is then fixed, so an independent fixed-action UCB certifies it without Bonferroni correction when no other action is tested on that certification split. Unsafe acceptance is at most `alpha`; rejection uses a separately justified safe fallback. Zero-failure Clopper-Pearson thresholds are 29, 59, and 299 at 95% confidence for 10%, 5%, and 1% risk.

### T-OO8 upper side

A matching logarithmic rate is available only for a known binary finite-alphabet channel with a query having positive two-sided KL and bounded log-likelihood. Fixed allocation or SPRT then uses order `log(1/beta)/I_min`. No general active, ordered-action, support-robust upper bound is claimed.

## 5. RACS consequence

RACS screens finite actions on a selection split, chooses the least estimated total-cost survivor, certifies that one action on an independent split, and otherwise falls back. It has:

- fixed-target safety with probability at least `1-alpha` over certification data;
- conditional near-oracle cost under T-OO5's margins and estimation event;
- no finite break-even if its mixture online cost is no lower than baseline; otherwise strict break-even above `K/(C_B-C_M)`.

RACS is `THEORETICAL_METHOD_TEMPLATE`. Its truth and retraining costs remain symbolic.

## 6. Theorem disposition

| Result | Status | Paper role |
|---|---|---|
| T-OO1 | `FORMAL_PROOF_COMPLETE`; identity | definition |
| T-OO2 | `FORMAL_PROOF_COMPLETE`; classical application | counterexample |
| T-OO3 | `FORMAL_PROOF_COMPLETE`; classical application | Main I |
| T-OO4 | `RESTRICTED_PROPOSITION` | appendix |
| T-OO5 | `FORMAL_PROOF_COMPLETE`; restricted domain | Main II |
| T-OO6 | `FORMAL_PROOF_COMPLETE`; new combination | Main II |
| T-OO7 | `FORMAL_PROOF_COMPLETE`; restricted domain | evaluation principle |
| T-OO8 | lower complete; upper restricted; partially matched | Main I consequence |

## 7. Exact validation

The verifier enumerates nested experiments with 2–6 environments, up to 8 actions, and up to 6 observable symbols; binary testing rules; all selected perturbation corners for safe screening; certification thresholds; accuracy/regret examples; a small binary-channel label problem; RACS outcomes; and break-even instances. Nine validation rows pass, all 12 requested counterexamples are registered, and eight tightness rows are emitted. Fractions are used except for logarithms, where the tolerance is below `1e-12`.

## 8. Graph-ANNS contact

Frozen oracle headroom motivates `H_oracle`; weak deployable action identification motivates `G_id`. Neither empirical fact proves a theorem premise. Current data instantiate a negative collision/headroom witness and the lower-bound problem shape, but not a positive observation channel, risk margin, or total-cost model. Therefore there is a theory-to-method design closure, not a validated Graph-ANNS method closure.

## 9. Remaining gap

The central open task is a non-circular deployable observation channel with empirically positive decision information and valid fixed-target uncertainty. A general joint `m/n/k/M` rate, a hard-safety Pareto frontier, censored endpoints, and a meta-environment guarantee remain open.
