# Theory report, batch 1

## 1. Problem and HNSW model

We study degree-limited graph ANN construction on \(X\subseteq\mathbb R^d\). HNSW is modeled as a random, insertion-order-dependent directed multilayer graph \(G_s^\pi\); effective resistance is computed only on a separately declared connected undirected local reference graph \(H_u\). This separation prevents an invalid direct use of undirected electrical identities on HNSW's directed adjacency.

The original HNSW algorithms were checked from the paper. Algorithm 4 performs relative-neighborhood-style geometric diversification, not topological bridge detection. Its exact rule and flags are in `theory/hnsw_algorithm4.md`. The paper's logarithmic discussion is conditional on exact/approximate Delaunay behavior and empirical bottom-layer backtracking; it is not a universal practical-HNSW theorem.

## 2. Verified classical mathematics

For \(L=BWB^\top\), the matrix \(P=W^{1/2}B^\top L^+BW^{1/2}\) is the orthogonal weighted cut-space projector. Consequently \(P_{ee}=\tau_e\), \(0<\tau_e\le1\), and \(\sum_e\tau_e=N-1\). An edge has leverage one exactly when it is a bridge. Its leverage is also its weighted-random-spanning-tree inclusion probability. Rayleigh monotonicity proves local subgraphs overestimate effective resistance, but not that their candidate rankings are accurate.

A common-kernel \((1\pm\varepsilon)\) spectral approximation yields reciprocal multiplicative bounds on pseudoinverses and resistances. It does not preserve greedy ANN navigation. The commute-time identity applies to a reversible random walk and is not an HNSW query-time equation.

## 3. Frozen local objective

The regularized direction score
\(F_{\rm dir}(S)=\log\det(I+\sigma^{-2}\sum_{v\in S}z_vz_v^\top)\) has marginal
\(\log(1+\sigma^{-2}z_v^\top A_S^{-1}z_v)\). Loewner inversion proves diminishing returns. Frozen leverage and locality sums are modular, so their nonnegative combination with direction log-det is normalized monotone submodular. Exact greedy therefore has the classic \(1-1/e\) guarantee for one Directed Local Selection problem.

This guarantee does not extend to reciprocal HNSW insertion, reverse pruning, or global degree caps. Those are distinct SLR/GDCR models. Recomputing leverage changes the mathematical object: for the explicit dynamic objective \(F_{\rm dyn}(S)=\sum_{e\in S}\tau_e^{H_0+S}\), exhaustive enumeration finds a five-vertex submodularity violation.

## 4. Navigation model and project results

We define strict and \(\delta\)-monotone paths. Concatenating an internal path, a \(\delta\)-improving cross edge, and a second internal path proves existence of a cross-cut monotone route. A unique cross-cut edge is necessary for graph connectivity. Neither statement makes pure greedy or beam search choose that edge.

Project-proved results in this batch are: a score-gap sufficient condition for selecting a bridge; the cross-cut concatenation lemma; a \(2\varepsilon\)-margin stability theorem for greedy sequences on the same ground set; the spectral-pseudoinverse resistance bound; and a pure-greedy \(\lceil(d(x_0,q)-r_q)/\delta\rceil\) step bound under global reachable-state progress. HNSW/beam transfer remains partial.

## 5. Counterexamples

Six counterexample classes are recorded. Most importantly: leverage-one edges can point away from a query; leverage can approach zero for the only usable greedy shortcut; spectral error can approach zero while adjacency navigation changes discontinuously; local resistance can overestimate global importance arbitrarily; direction diversity can expel accurate near edges; and a natural recomputed-leverage objective is not submodular. These prohibit “resistance implies navigation,” “spectral approximation implies recall,” and “dynamic is still covered by greedy theory.”

## 6. Stability and difficulty

Edge Jaccard difference, frozen-reference leverage-weighted difference, NDC variance, recall variance, and oracle \(ef^*\) variance are now defined. Geometric hardness is kept separate from graph-navigation hardness. The latter may use trace-derived bottlenecks or missing high-score candidates only as preregistered offline diagnostics unless an online leakage-free estimator is specified.

## 7. Complexity

Dense exact local resistance costs \(O(c^3)\) time and \(O(c^2)\) storage; all-node use costs \(O(nc^3)\) and is only a mechanism oracle. Gram-based direction scoring avoids \(d\times d\) determinants; with precomputed direction Gram entries, total local work is summarized in `theory/complexity.md`. The next scalable paths are gated scoring, Schur complements, approximate solves/embeddings, and periodic repair.

## 8. Theory-to-experiment contract

`theory/theory_experiment_map.md` maps each premise and conclusion to code or a pending instrument. Exact NDC must use the corrected wrapper because the upstream counter omits bottom-layer work. Tests now cover path/tree/cycle/complete/double-clique graphs, projector identities, Rayleigh monotonicity, spanning-tree marginals, log-det/frozen submodularity, and counterexamples.

## 9. Safe paper claims

- Leverage is a rigorously normalized measure of edge nonredundancy in the declared undirected reference graph.
- Frozen resistance plus regularized direction log-det plus locality is a monotone submodular local objective with the standard greedy factor.
- Additional navigation assumptions can connect bridge retention to existence of monotone routes.
- The method currently has a local objective guarantee and empirical ANN evaluation, not a global HNSW recall or complexity guarantee.

## 10. Claims prohibited at this stage

- High resistance guarantees a useful ANN edge.
- Spectral preservation guarantees greedy/beam path or recall preservation.
- Commute time equals HNSW query time.
- Local one-hop resistance accurately ranks global importance without an approximation premise.
- The local \(1-1/e\) factor applies to the complete HNSW construction.
- Existence of a monotone path guarantees HNSW finds it.
- Current repair results establish an improvement; the first controlled repair smoke test was negative and remains part of the record.

## 11. Open proof and experiment queue

Priority gaps are: characterize when the terminal Schur complement of \(H_u\) approximates the global graph; quantify reverse-pruning survival; derive a beam-retention lemma with explicit queue rules; complete remaining reading cards; enumerate the direction/locality counterexample; and measure theorem-premise prevalence on synthetic and real data. No recall theorem will be attempted before those premises are observable.
