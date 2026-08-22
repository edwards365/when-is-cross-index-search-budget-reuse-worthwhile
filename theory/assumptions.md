# Assumptions

1. The resistance graph is explicitly symmetrized and nonnegative.
2. Standard resistance is evaluated only within connected components; cross-component pairs have infinite resistance.
3. Candidate leverage is computed before greedy selection and is not recomputed after each choice in the v0.1 objective.
4. Candidate directions are nonzero and coefficients `alpha`, `beta`, `gamma` are nonnegative.
5. Any navigation statement additionally requires candidate coverage and metric progress assumptions; spectral importance alone is insufficient.
6. Candidate-edge semantics are one of schemes A/B/C in `candidate_edge_models.md`; results are not moved between schemes silently.
7. Euclidean and angular/cosine experiments use genuine metrics after normalization where stated. Raw cosine similarity, MIPS, and arbitrary dissimilarities do not inherit metric navigation theorems without a declared reduction.
8. Exact Kron reduction is distinguished from induced one-hop/two-hop subgraphs. Only the exact terminal Schur complement preserves terminal resistances unconditionally.
9. Pure greedy, fixed-width HNSW beam search, and DABS are different algorithms with different queues and stopping rules.
10. Any statistical claim about navigation utility names the query and entry distributions; topology alone supplies no expected-query guarantee.
