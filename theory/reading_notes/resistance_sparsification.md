# Reading card: Graph Sparsification by Effective Resistances

**Source.** Spielman and Srivastava, SIAM Journal on Computing 2011, DOI 10.1137/080734029; arXiv:0803.0929.

1. **Problem.** Construct a sparse weighted graph whose Laplacian quadratic form approximates that of an input graph.
2. **Graph model.** Connected undirected positive-weight graph.
3. **Distance assumptions.** None on embedded vectors; effective resistance is induced by graph conductances.
4. **Algorithm.** Sample and reweight edges according to probabilities controlled by \(w_eR_e\), using approximate resistances for speed.
5. **Theorem.** With the paper's sample size and probability, all Laplacian quadratic forms are within \(1\pm\varepsilon\); it also gives simultaneous resistance estimation.
6. **Assumptions.** Common vertex set, undirected Laplacian, positive weights, and the stated random-sampling/sample-size conditions.
7. **Proof method.** The weighted cut-space projection \(P\), concentration of random matrices, Laplacian solvers, and Johnson--Lindenstrauss projection.
8. **HNSW relation.** Supplies leverage mathematics for an undirected local reference graph, not for the directed search graph itself.
9. **Directly usable.** \(P_{ee}=\tau_e\), projection rank, Foster sum, and spectral-to-resistance preservation.
10. **Not transferable.** Spectral preservation does not preserve greedy ANN paths or query recall; the paper samples existing edges rather than selecting new geometric candidates under per-node degree caps.
11. **Innovation collision.** Effective-resistance edge importance is classical. The project contribution must reside in the reference-graph construction, combined objective, HNSW integration, and validated navigation mechanism.
12. **Metrics.** Resistance approximation error, leverage ranking, spectral error, cut distortion, and runtime.
