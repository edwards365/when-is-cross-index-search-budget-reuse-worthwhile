# Reading card: HNSW

**Source.** Malkov and Yashunin, *Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs*, TPAMI 2020, DOI 10.1109/TPAMI.2018.2889473; arXiv:1603.09320.

1. **Problem.** Approximate \(k\)-nearest-neighbor search in general metric spaces.
2. **Graph model.** Incrementally built nested proximity graphs; a point's maximum layer is sampled from an exponentially decaying distribution. Links at upper layers represent longer scales.
3. **Distance assumptions.** Algorithms need pairwise dissimilarity evaluations; the Delaunay-based complexity discussion is substantially stronger than arbitrary dissimilarity.
4. **Algorithm.** SearchLayer maintains candidate and result priority queues; insertion searches layers, selects up to \(M\) neighbors, adds reciprocal connections, and reprunes overflowing lists. Query search uses `ef=1` above layer zero and a beam-like SearchLayer at layer zero.
5. **Theory.** The paper motivates logarithmic layer count and analyzes per-layer progress under exact Delaunay replacement. Approximate-Delaunay resilience and bottom-layer `ef` saturation are empirical/conditional.
6. **Assumptions.** Exact nearest element on a layer is guaranteed in the strict argument by exact Delaunay structure; fixed-degree and scale separation are also used.
7. **Proof method.** Skip-list analogy, geometric layer distribution, and expected distance-scale progress; empirical scaling for the implemented approximation.
8. **Relation to HNSW.** Primary algorithm source. Exact Algorithm 4 semantics are recorded in `theory/hnsw_algorithm4.md`.
9. **Directly usable.** Candidate generation, degree-control process, and the relative-neighborhood-style diversity rule are implementation baselines.
10. **Not transferable.** The paper does not prove distribution-free logarithmic query time, recall, or that its diversity rule preserves low-conductance bridges.
11. **Innovation collision.** It already addresses clustered-data connectivity through geometric diversification. Novelty must be specifically topology-aware frozen leverage plus navigation diagnostics, not generic “diverse neighbors.”
12. **Metrics.** Recall/time, distance computations, degree, layer, candidate extension, reverse-pruning survival, and clustered versus nonclustered behavior.
