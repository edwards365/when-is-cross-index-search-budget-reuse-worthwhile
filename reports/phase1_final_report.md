# Phase I final report: local resistance in HNSW

Status: closed on 2026-08-22. Result-code commit: `ba90eda`. Closure tag: `phase1-local-resistance-null-v1`.

> Phase I成功建立了数学与工程可行性，但当前性能算法没有通过电阻特异性收益门槛。

## Research question

Phase I asked whether local effective-resistance leverage could directly identify navigation-useful HNSW edges and whether small degree-preserving interventions could improve search. The answer must be split into mathematical, engineering, and performance claims.

## What was established

On explicitly connected, undirected, positive-weight reference graphs, the Moore--Penrose effective-resistance identities, edge-leverage bounds, Foster identity, random-spanning-tree marginals, Rayleigh monotonicity, and rank-one add/delete formulas are valid. The frozen local leverage plus direction log-det plus locality objective is normalized, monotone, and submodular under nonnegative coefficients, so cardinality-constrained greedy has the classical local `1-1/e` guarantee.

The implementation exactly replays HNSW insertion levels, construction search, Algorithm 4 selection, reciprocal changes, upper-layer query descent, and layer-0 beam search. It logs real insertion candidates without changing the final graph, reconstructs all 5,487 directed layer-0 edges, computes Scheme A/B/C scores, attributes rejected candidates to exact search states, and applies degree-preserving directed swaps. Python ordered search matches C++ hnswlib labels and exact distance-call counts for all 3,072 formal Original holdout searches.

## What was refuted or unsupported

Counterexamples refute the implication from high resistance to useful directed navigation, from low leverage to safe deletion, from spectral closeness to path stability, and from dynamically recomputed leverage to the frozen submodular theorem.

In the valid independent holdout, Trace+Resistance minus Original at `ef=10` has Recall@10 difference `-0.000390625`, with descriptive paired 95% bootstrap interval `[-0.00107421875, 0.00029296875]`. It reduces mean NDC by `0.4296875`, but Geometry reduces NDC by `0.54296875` in point estimate and no resistance method improves recall. Therefore the observed cost change is not resistance-specific.

An earlier apparent Recall gain of `0.001855` used noisy copies of base points whose identities overlapped the selection workload. It is formally invalid, excluded from all formal summary CSVs, and retained only as a leakage incident.

## Phase I decision

The local mathematics is valid and the integration is reproducible. The tested performance algorithm is not an improved HNSW and must not be described as one. Phase I closes as a successful boundary-and-feasibility study with a valid negative algorithmic result. The Phase I fixture and thresholds are frozen; no further tuning is allowed.

Phase II, if pursued, changes the hypothesis to query-independent **Geometry first + Resistance second** and evaluates resistance primarily as a structural-stability guard across construction seeds, insertion orders, datasets, and later perturbations.
