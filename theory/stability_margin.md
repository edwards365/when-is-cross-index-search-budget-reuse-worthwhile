# Selection and leverage stability margins

## Greedy Geometry margin

At greedy step `t`, let the best and runner-up marginal Geometry gains be `g_1` and
`g_2`, with margin `m_t=g_1-g_2`. Suppose a perturbation changes every candidate's
evaluated marginal by at most `delta_t`. The perturbed best remains the same whenever
`m_t>2 delta_t`: its gain can fall by at most `delta_t`, while a competitor can rise
by at most `delta_t`. Applying this condition inductively at every step preserves the
entire greedy sequence, provided the perturbation bound is conditional on the same
previously selected sequence.

This is a deterministic sufficient condition, not a distributional robustness claim.
Near ties have no such certificate; deterministic tie-breaking provides repeatability,
not perturbation stability.

## Frozen leverage ranking

For a connected weighted reference graph with Laplacian `L`, edge incidence `b_e`,
and conductance `w_e`, `tau_e=w_e b_e^T L^+ b_e`. If a perturbation preserves the
nullspace and the nonzero spectrum stays above `lambda_2'>0`, standard inverse
perturbation reasoning on `1^perp` bounds the change in `L^+` in terms of
`||Delta L||`, `lambda_2`, and `lambda_2'`. Consequently

`|Delta tau_e| <= |Delta w_e| R_e
 + w_e ||b_e||^2 ||Delta L^+|| + higher-order cross terms`.

A pairwise leverage order is certified only when its original gap exceeds the sum of
the two score-error bounds. Small algebraic connectivity makes this bound weak, which
is precisely where bridges and near-disconnections can make leverage highly sensitive.
The project currently records this as a partial perturbation bound; a sharp bound for
candidate-dependent augmented graphs is not proved.

## Directed boundary

Even invariant Geometry choices or stable undirected-reference leverage rankings do
not imply stable directed HNSW search. Insertion order changes candidate exposure,
reverse links, pruning, entry paths, and upper layers. Phase II therefore treats
cross-build query cost and Recall as experimental outcomes rather than consequences of
the local margin conditions.
