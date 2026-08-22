# Reading card: Worst-case Performance of Popular ANN Implementations

**Source.** Indyk and Xu, NeurIPS 2023, proceedings paper d0ac28b79816b51124fcc804b2496a36.

1. **Problem.** Establish limitations and conditional guarantees for popular graph ANN implementations.
2. **Graph model.** Implemented HNSW, NSG, and DiskANN variants, plus a slower analyzable DiskANN construction.
3. **Distance assumptions.** Includes explicit low-dimensional/adversarial metric instances; positive results impose bounded intrinsic/doubling-style structure and pruning parameters.
4. **Algorithm.** Builds hard data sets and analyzes greedy/beam-like graph search and robust pruning.
5. **Theorem.** Practical variants admit instances with linear-scale query behavior; the slow DiskANN variant gets conditional approximation/query guarantees. The paper notes its proof does not transfer to HNSW/NSG at pruning parameter \(\alpha=1\).
6. **Assumptions.** Algorithm version, starting vertex, pruning parameter, aspect ratio, and intrinsic-dimension conditions are theorem-critical.
7. **Proof method.** Construct graph geometry that forces the queue to scan a large distractor region before a useful connector.
8. **HNSW relation.** Directly falsifies universal performance extrapolation from standard benchmarks.
9. **Directly usable.** Counterexample methodology and separation between implementation evidence and conditional theory.
10. **Not transferable.** DiskANN's slow-preprocessing upper bound is not an HNSW theorem and says nothing about resistance selection.
11. **Innovation collision.** A valid project claim must be mechanism- or distribution-conditional; no blanket logarithmic claim is defensible.
12. **Metrics.** Scanned vertices, queue length, approximation ratio, recall, graph degree, aspect ratio, and hard-instance size.
