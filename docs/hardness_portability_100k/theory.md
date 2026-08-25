# Theory: query hardness across HNSW construction histories

Let `D(q;G,A,r)` be the smallest frozen grid budget whose Recall is at least `r` at that budget and every larger measured budget. Let `G=B(X,pi,s,theta)` denote the graph produced from fixed data `X`, insertion history `pi`, graph seed `s`, and parameters `theta`.

## Proposition 1 — query-only non-identifiability

Assume the same query `q`, search procedure `A`, target `r`, and two legal indexes satisfy `D(q;G1,A,r)=a<b=D(q;G2,A,r)`. Any deterministic index-blind allocation `f(q)` has the following dichotomy: if `f(q)<b`, it is insufficient for `G2` under the definition of `D`; if `f(q)>=b`, it allocates at least a factor `b/a` relative to the minimum sufficient budget on `G1`. This is a conditional finite-instance statement. It assumes the grid values represent comparable cost and does not claim that every HNSW pair has unequal difficulty.

## Proposition 2 — limitation of a global multiplier

Suppose `e1(q1)<e1(q2)` on a source graph while `e2(q1)>e2(q2)` on a target graph. Multiplication by any positive scalar preserves the source ordering, so it cannot reproduce the reversed target ordering. After rounding to a monotone grid, ties can replace but cannot correctly express the strict reversal. Consequently, a scalar chosen to make the smaller target requirement safe can over-allocate the other query, while a smaller scalar can under-allocate at least one query. The amount of loss requires empirical costs and is not implied by the ordering argument alone.

## Proposition 3 — Oracle–realizability upper bound

Write fixed cost as `C_fixed`, target-index Oracle saving as `H_oracle*C_fixed`, and all deployment penalties as nonnegative `C_probe+C_error+C_control`. Then the realized fractional gain obeys

`G_real <= H_oracle - (C_probe+C_error+C_control)/C_fixed`.

This is accounting when all terms use the same expected-cost population and baseline. A positive deployable gain additionally assumes that probes can be reused, prediction errors are measured on held-out queries, and control overhead is fully charged. The measured Oracle headroom is an experimental estimate, not a universal bound for other data or graphs.

## Proposition 4 — Omega and transfer regret are not equivalent

`Omega` is a variance ratio for the query-by-graph interaction after query and graph main effects are removed. Transfer regret is a decision loss after a source-derived allocation and its globally calibrated multiplier are applied to a target graph. A large interaction variance can occur where the decision grid or cost curve makes transferred decisions cheap; conversely, modest interaction variance near a Recall threshold can cause large regret. Therefore neither quantity is a monotone function of the other without assumptions on the allocation rule, grid, censoring, and cost curvature.

## Empirical correspondence, not theorem

At 100K, Arxiv and SIFT have both Omega above 0.27 and history-regret differences above 0.11, whereas GloVe has Omega about 0.10 and a smaller core history-regret difference near 0.034. All three nevertheless show significant residual regret for natural and cluster-block histories after global calibration. These observations support the stated mechanism on the frozen fixtures but do not turn the variance/regret relationship into a general theorem.
