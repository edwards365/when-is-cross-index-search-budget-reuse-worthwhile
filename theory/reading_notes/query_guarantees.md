# Reading card: conditional ANN graph and beam-search guarantees

**Sources.** Shrivastava, Song, and Xu, arXiv:2303.06210; Al-Jazzazi et al., *Distance Adaptive Beam Search*, NeurIPS 2025 proceedings paper 904fe070f484231aa26dbdb37816cd40.

1. **Problem.** Prove graph ANN query behavior under structural/geometric assumptions, and terminate beam search adaptively while retaining accuracy guarantees.
2. **Graph model.** Approximate-neighbor graphs in a specified data regime; DABS assumes a declared navigability property of the supplied graph.
3. **Distance assumptions.** The hypotheses are essential and are not satisfied automatically by arbitrary embeddings or HNSW outputs.
4. **Algorithm.** Analyze greedy graph search; DABS modifies query stopping based on observed distances rather than modifying graph construction.
5. **Theorem.** Both lines provide conditional guarantees, not a theorem that popular finite-degree graphs are always navigable.
6. **Assumptions.** Low-dimensional/dense sampling or an explicit graph-navigability premise, plus algorithm-specific queue and stopping rules.
7. **Proof method.** Geometric progress/concentration for graph paths; DABS composes a navigability condition with a distance-based termination certificate.
8. **HNSW relation.** Supplies possible downstream lemmas only after the repaired graph is shown to meet the corresponding premise.
9. **Directly usable.** Vocabulary for path progress and a query-layer baseline orthogonal to rewiring.
10. **Not transferable.** A conditional query theorem cannot prove the premise created by the proposed selector; existence of one path is weaker than beam retention.
11. **Innovation collision.** Separate construction-side contribution from adaptive search-side contribution and compare their combination experimentally.
12. **Metrics.** Progress per expansion, frontier/queue width, stopping threshold, visited nodes, distance computations, and approximation/recall.
