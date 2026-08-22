# Phase I theorem boundary

## Proved domain

The standard resistance object is a connected undirected graph with finite positive conductances and Laplacian `L`. Effective resistance is the Moore--Penrose quadratic form on zero-sum contrasts. Existing-edge leverage lies in `(0,1]`, sums to `n-1`, equals a weighted spanning-tree marginal, and obeys the recorded rank-one identities. Exact terminal Kron reduction preserves terminal resistances.

For one frozen candidate ground set, frozen nonnegative leverage and locality are modular. Direction log-det is normalized, monotone, and submodular. Their nonnegative sum is therefore normalized monotone submodular, and exact cardinality greedy obtains `1-1/e` relative to that local frozen objective.

## Non-transferable conclusions

The theorem does not cover directed HNSW adjacency, reciprocal insertion, reverse pruning, candidate-set drift, global degree coupling, dynamically recomputed leverage, insertion-order randomness, beam retention, Recall@k, NDC, latency, or structural stability across builds.

Counterexamples disprove the missing generic implications from resistance to query progress, low leverage to safe deletion, spectral approximation to adjacency navigation, and dynamic leverage to submodularity. No proof of HNSW benefit may cite the local theorem without separately establishing candidate coverage, direction/query alignment, and search-policy retention.

## Phase II boundary

GGR will be a lexicographic or constrained construction: Geometry defines a protected feasible region; frozen resistance may optimize only inside it. By construction this can prove a numerical geometry constraint on the selected local set. It still cannot prove final recall, cost, directed connectivity, or cross-build stability. Those remain preregistered empirical questions.
