# Theory for the Rebuild Tax study

## Definitions and assumptions

**ASSUMPTION A1.** The history set `H` is finite and declared before analysis. A conclusion on `H` does not cover all future HNSW rebuilds.

**ASSUMPTION A2.** For query `q` and history `h`, `B(q,h)` is the smallest frozen grid value whose measured quality reaches the declared target at that and every larger grid value. A value beyond the largest grid is right-censored.

**ASSUMPTION A3.** Cost `C_h(q,e)` is nondecreasing in allocated budget for the deterministic allocation the theorem discusses. Measured NDC need not be pointwise monotone, so empirical cost calculations use observed NDC and report this distinction.

## Theorem 1 — strictly safe history-blind allocation

**THEOREM.** If a history-blind allocation must satisfy `b(q) >= B(q,h)` for every `h in H`, every feasible allocation obeys `b(q) >= max_h B(q,h)`. The pointwise minimum feasible allocation is therefore `b*_blind,0(q)=max_h B(q,h)`. Under A3 it also minimizes cost among strictly safe history-blind allocations.

**PROOF.** Each history contributes one lower-bound constraint. Their conjunction is equivalent to the maximum lower bound. The maximum itself satisfies every constraint, so it is feasible and pointwise minimal. Monotone cost then makes any larger allocation no cheaper. This is deterministic only on the declared finite history set. ∎

## Theorem 2 — chance-constrained allocation

**THEOREM.** For a predeclared distribution on history `H`, the minimum allocation satisfying `Pr_H[b(q)<B(q,H)] <= delta` is the lower `(1-delta)` quantile of `B(q,H)` under the convention `inf{b:F_B(b)>=1-delta}`.

**PROOF.** Feasibility is `F_B(b)>=1-delta`. By definition, the generalized inverse is the smallest value satisfying this inequality. On a discrete ef grid it is a grid point and can be nonunique only as an interval before adopting the generalized-inverse convention. Right-censored observations identify only a lower bound on this quantile. Uniform and realistic-history weighting define different distributions and must not be pooled silently. Finite histories provide empirical rather than population coverage. ∎

## Theorem 3 — tight limitation of a global multiplier

**THEOREM.** For source budget `B_s(q)>0`, target budget `B_t(q)`, and ratios `rho_q=B_t(q)/B_s(q)`, a multiplier safe for a finite query set must satisfy `a>=max_q rho_q`; this bound is sufficient before grid rounding. If `rho_1<rho_2`, any safe multiplier over-allocates query 1 in budget ratio by at least `rho_2/rho_1` relative to its exact target ratio.

**PROOF.** Safety for each query is `a B_s(q)>=B_t(q)`, equivalent to `a>=rho_q`; intersecting constraints gives their maximum. Choosing the maximum satisfies all constraints. For query 1, `a/rho_1>=rho_2/rho_1`. Upward rounding preserves safety but can increase over-allocation. This is a budget statement; nonlinear NDC and latency prevent interpreting it directly as a cost or latency multiplier. ∎

## Theorem 4 — query-only non-identifiability

**COUNTEREXAMPLE.** Consider finite-beam graph search with one query and node distances `d(s)=10,d(a)=5,d(b)=4,d(t)=0`. In graph `G1`, the entry `s` connects only to `a`, and `a` connects to true neighbor `t`; beam width 1 succeeds. In graph `G2`, `s` connects to both `a` and misleading dead-end `b`. Width 1 retains `b` and fails, while width 2 retains `a`, expands it, and reaches `t`. Thus the same query has budgets 1 and 2 on two legal directed search graphs.

**THEOREM.** Any deterministic predictor observing only that query outputs the same budget on both graphs; it therefore either allocates below 2 and is unsafe on `G2`, or allocates at least 2 and over-allocates on `G1`.

**BOUNDARY.** The counterexample is for finite-beam directed graph search. It is not claimed to be HNSW-realizable without a separate insertion-history enumeration. That realizability remains an **OPEN QUESTION**.

## Theorem 5 — split-conformal rebuild calibration

**THEOREM.** Let sentinel ratios `rho_i=B(q_i,t)/b_s(q_i)` and a future ratio be exchangeable, with no ties broken using outcomes. For `k=ceil((n+1)(1-delta)) <= n`, choose the kth order statistic `a_hat=rho_(k)` and round `a_hat b_s(Q)` upward to the ef grid. Then marginally `Pr[B(Q,t)<=ceil_E(a_hat b_s(Q))] >= 1-delta`.

**PROOF.** Under exchangeability, the future ratio's rank among `n+1` ratios is uniform. It exceeds the kth sentinel order statistic with probability at most `(n+1-k)/(n+1)<=delta`. Upward grid rounding cannot turn a sufficient continuous allocation into an insufficient one. ∎

**PROPOSITION.** When `k>n`, the requested finite-sample quantile is infeasible; substituting the sample maximum is conservative but is not the stated nontrivial conformal quantile. In particular, delta 0.001 generally requires about 1000 sentinels before `k<=n`.

**BOUNDARY.** The guarantee is marginal coverage, not conditional per-query safety, zero mean Recall loss, or positive net NDC. It additionally assumes sentinel/future exchangeability and fully charges the cost of discovering sentinel target budgets.

## Empirical claims to test

**EMPIRICAL CLAIM E1.** On at least two datasets with realistic histories, strict history blindness costs more than 5% of history-aware NDC or destroys more than 25% of Oracle headroom.

**EMPIRICAL CLAIM E2.** Median-centering and a global multiplier do not remove rank inversions or most transfer regret.

**EMPIRICAL CLAIM E3.** Frozen query geometry explains only part of cross-history budget dispersion; unavailable topology/trace evidence limits stronger mechanism attribution.
