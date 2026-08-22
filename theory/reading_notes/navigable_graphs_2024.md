# Reading card: Navigable Graphs for High-Dimensional NNS

**Source.** Diwan et al., NeurIPS 2024, proceedings paper 6dc63b4063c978cf195bc15178e8152a.

1. **Problem.** How sparse can a graph be while greedy search can route from every database start to every database target?
2. **Graph model.** A graph on a finite metric data set satisfying a formal universal greedy navigability definition.
3. **Distance assumptions.** Main constructions/lower bounds are stated for high-dimensional nearest-neighbor settings with specified metric embeddings.
4. **Algorithm.** Construct sparse navigable graphs rather than analyze the incremental HNSW heuristic.
5. **Theorem.** The paper gives an average-degree \(O(\sqrt{n\log n})\) construction and a near-\(\sqrt n\) lower bound in \(O(\log n)\) dimensions for its universal notion.
6. **Assumptions.** “Any start, any target” pure-greedy navigability; this is stronger and different from expected query performance under a query distribution.
7. **Proof method.** Combinatorial/geometric construction and adversarial lower-bound embedding.
8. **HNSW relation.** Formalizes a property HNSW is often said to approximate, but does not certify a practical HNSW instance.
9. **Directly usable.** Definitions and lower-bound warning; motivates reporting which quantifiers a navigation claim uses.
10. **Not transferable.** Universal database-target routing is not beam search to an external query and does not yield an `efSearch` setting.
11. **Innovation collision.** The project should not claim that constant-degree repaired HNSW becomes universally navigable in this strong sense.
12. **Metrics.** Fraction of start/query pairs with monotone paths, degree, greedy path length, failed starts, and quantifier-specific success rate.
