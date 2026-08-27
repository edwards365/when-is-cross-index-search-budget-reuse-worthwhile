# Theory draft: information-constrained budget adaptation

## Problem formulation

Let a search environment be `I`, an ordered budget set be `E`, and let `R_I(q,e)` and `C_I(q,e)` denote quality and cost. For target quality tau, define stable demand `B_I(q;tau)` as the least budget whose entire upper tail attains tau. This tail definition handles non-monotone measured recall without pretending the observed curve is monotone. A demand absent from the observed grid is right-censored.

For an information sigma-field G and risk delta, define `V_delta(G)` as the infimum expected cost over G-measurable policies whose under-budget probability is at most delta. This formulation separates the search mechanism from the information supplied to its controller.

## Information order and safe envelopes

If one admissible policy class contains another, optimization over the larger class cannot increase value. No total order is asserted between static target features and sequential target state without an explicit containment relationship.

For a source summary X, zero-risk feasibility requires an allocation no smaller than target demand almost surely within each information cell. Hence the pointwise-minimal allocation is the conditional essential supremum. It is exact when demand is constant within every cell; otherwise, under strictly increasing cost and positive mass on overallocated queries, the information-coarsening tax is positive.

When X is the ordered source demand and the allocation must be nondecreasing, the minimum safe function is obtained by taking the maximum target demand for every tied source level and then the prefix maximum over levels. This differs from isotonic regression because no average-loss projection is performed: every observation imposes a hard lower constraint.

## Inversions and risk relaxation

Source and target demands may reverse rank. Under a finite uncensored grid and additive/linear budget-gap cost, disjoint incompatible pairs cannot all be served at their target Oracle actions by one monotone mapping. A maximum-weight vertex-disjoint inversion matching therefore gives a computable lower bound. The current proof is incomplete outside these narrowed assumptions, and inversion frequency alone says nothing about cost scale.

Under marginal failure allowance delta, the controller can select under-budget actions for a limited number of queries. On a finite grid this is a resource-allocation dynamic program over information cells, last monotone action, and failures used. Global allocation can dominate applying the same conditional quantile independently to each cell. Censored demands are mandatory failures unless an action above the grid is modeled.

## Certification

For n independent calibration examples and M prespecified policies, let `U_(alpha/M)(k,n)` be the one-sided exact binomial upper bound after k failures. The largest certifiable count is the greatest k with `U<=delta`, and a policy with true failure p is certified with probability `P[Binomial(n,p)<=k]`. This distinguishes population safety from the power to establish it. At n=256, alpha=delta=0.05, the allowable counts for M=1,4,16 are 6,5,3.

Ranking signal is insufficient for certification. Strictly monotone score transformations preserve AUROC and AUPRC but can change the set selected by a fixed numeric threshold and hence its conditional failure rate. A certificate therefore attaches to a complete operating rule, not to a score's ranking quality.

## Sequential target information

A resumable search exposes a growing filtration of target-native states. Stopping rules adapted to this filtration are outside the source-summary-only policy class, so source-envelope and source-monotonicity lower bounds do not rule them out. More information weakly improves the attainable value only when the earlier policies remain feasible and all observation costs are included. Certification must cover the complete checkpoint, stopping, and fallback policy.

## Empirical contact

The frozen 81-build Graph-ANNS matrix shows measurable budget changes, rank inversions, and positive safe-monotone tax across hnswlib, Faiss HNSW, and Vamana on three datasets. However, direct deployable evidence remains hnswlib-specific, and the independent Signal Pilot certified zero of 16 candidate stopping policies. The empirical conclusion is therefore narrower than the mathematical scope: ICBA explains the boundary and identifies the information a future method must obtain, but does not itself establish a deployable adaptive search algorithm.
