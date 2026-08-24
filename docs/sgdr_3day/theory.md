# SGDR three-day theory notes

## Scope

The statements below concern query-time selection and finite-beam graph search. They do
not turn resistance, geometry, or delta-edge scores into a navigation guarantee. The
far/near-field separation is a testable hypothesis, not a theorem.

## Proposition 1: perfect complete-policy selector

Fix a query–`efSearch` pair and let policy `O` have recall and cost `(R_O,C_O)` and
policy `R` have `(R_R,C_R)`. A selector that may execute exactly one complete policy
and must satisfy pointwise recall `R >= R_O` has feasible set

`F={O}` when `R_R<R_O`, and `F={O,R}` otherwise. Therefore its cost lower bound is

`C_oracle = C_O` if `R_R<R_O`, and `min(C_O,C_R)` otherwise.

Proof: the recall constraint excludes `R` in the first case; in the second case both
policies are feasible, so minimizing over the two gives the expression. Summing this
pointwise minimum proves the lower bound for any selector restricted to the two
complete policies. No realizable predictor can beat it without using a third policy
or sharing work between policies.

The prompt's specified rule, `C*=C_R` whenever `R_R>=R_O`, equals this lower bound
only if `C_R<=C_O` on every safe pair. Otherwise it is the cost of an always-aggressive-
when-safe oracle and is a conservative (higher-cost) oracle, not the mathematical
minimum. Gate O reports the specified rule so the preregistered test is unchanged;
the distinction prevents an invalid theorem claim.

## Proposition 2: fallback break-even

Normalize expected Original cost to one. If aggressive search costs `alpha`, an
independent Original rerun is required with probability `p`, and gating/management
cost is `h`, linearity of expectation gives total normalized cost

`E[C]/E[C_O] = alpha + p + h`.

It improves on Original exactly when `alpha+p+h<1`, equivalently
`p<1-alpha-h`. This is optimistic when failed aggressive work cannot be reused. If a
fraction `s` of Original rerun cost is saved by a shared prefix or reusable candidate
state, the expression becomes `alpha+p(1-s)+h`; for `s<1`, break-even requires
`p<(1-alpha-h)/(1-s)`. A literal double run has `s=0`. If maintaining reusable state
adds overhead, that cost belongs in `h`. The frozen 216-cell sensitivity audit shows
that full rerun is impossible in all 18 GloVe seed×ef cells, and only 12/18 Arxiv and
9/18 SIFT cells pass even for each tested overhead slice; it is not a cross-dataset
solution.

## Counterexample 1: local progress does not imply finite-beam recall

Use directed nodes `s,a,b,t,z`, query distances
`d(s,q)=10, d(a,q)=6, d(b,q)=5, d(z,q)=1, d(t,q)=0`, and beam `ef=1`.
Original edges are `s->a, a->t`; the modified graph uses `s->b, b->z`. The replacement
looks better by one-step progress because `5<6` (and can also be assigned greater
angular/local coverage).

Original trace: start heap `{s:10}`; expand `s`, enqueue `a:6`; expand `a`, enqueue
`t:0`; expand `t`; result is `t`. Modified trace: start `{s:10}`; expand `s`, enqueue
`b:5`; expand `b`, enqueue `z:1`; expand `z`; the queue empties and `t` was never
reachable. Thus strictly better local progress is compatible with worse finite-beam
recall.

## Counterexample 2: retaining Original edges is not Recall-monotone

Keep the Original graph `s->a, a->t` and add only delta edge `s->b`; let `b` have no
useful outgoing edge. Use the same distances and `ef=1`. Expanding `s` first inserts
`a:6`; processing the additive neighbor inserts `b:5`, which replaces `a` in the
bounded top-candidate heap although `a` remains in the candidate queue. Search expands
`b`. Its lower bound is now 5; the next queued candidate `a:6` exceeds the lower bound,
so standard HNSW early termination fires before `a` is expanded. Original reaches
`t`; Original-plus-delta does not. Hence edge-set inclusion alone cannot guarantee
finite-`ef` Recall monotonicity. This is precisely why zero-delta and never-expand
equivalence tests are necessary but not sufficient for nonzero delta budgets.

## Far/near-field separation hypothesis

For Original neighbors `E_O(u)`, define local scale
`ell(u)=median_{v in E_O(u)} d(u,v)` and relative query scale
`rho(q,u)=d(q,u)/(ell(u)+epsilon)`. SGDR would inspect additive delta edges only when
`rho(q,u)>tau`, while always retaining and inspecting Original edges.

The unproved hypothesis is that delta utility equals far-field progress gain minus
near-field queue/interference cost, with positive expectation only at large `rho`.
Support requires paired measurements of delta distance calls, enqueue/expansion events,
first delta phase, switch position, candidate-set changes, Recall and NDC. It is
refuted for the current signal if no preregistered scale/depth region simultaneously
meets Recall noninferiority and cost improvement across the required datasets/seeds.

Existing Original-versus-R4 traces identify replacement damage but do not identify
the result of additive, selectively expanded edges: the visited set and queue state
would change. Consequently, phase labels derived from those traces are descriptive
proxies only and cannot satisfy Gate O. An exact diagnostic counterfactual search or
equivalent identifiable replay is required before implementation authorization.
