# Localization, truncation bias, and Kron reduction

## Rayleigh comparison

If \(H_u\) is a conductance-preserving connected subgraph of global undirected \(G\), and terminals \(a,b\) remain connected, then \(R_{H_u}(a,b)\ge R_G(a,b)\). This comparison fails if local Gaussian weights are renormalized through a different \(\rho_u\), if symmetrization changes conductances, or if a regularizer adds nonphysical edges.

For a nested sequence \(H_1\subseteq H_2\subseteq\cdots\subseteq G\) with fixed weights and connected terminals, \(R_{H_j}(a,b)\) is nonincreasing and reaches \(R_G(a,b)\) when the finite sequence exhausts \(G\). Individual candidate rankings need not converge monotonically: different pairs can decrease at different rates and cross.

One-hop, two-hop, and insertion-candidate references are not generally nested. Therefore none is uniformly “closer” to global resistance without a spectral or terminal-response comparison. Increasing hop radius reduces deletion bias only when old edges and weights are retained.

## Boundary truncation

An induced local subgraph deletes all paths that leave and re-enter its boundary, which can turn an ordinary edge into an apparent bridge. This is not numerical error; it is a different electrical network. The counterexample family in `counterexamples.md` makes the multiplicative overestimate unbounded.

## Exact Kron remedy

Partition vertices into retained boundary/terminals \(K\) and eliminated interior \(I\). When \(L_{II}\) is invertible, the Kron-reduced Laplacian is
\[
S_K=L_{KK}-L_{KI}L_{II}^{-1}L_{IK}.
\]
It is the Dirichlet-to-Neumann map on \(K\) and exactly preserves effective resistance between every pair in \(K\). It generally creates a dense clique on boundary nodes. Exact Kron reduction of the *global* graph would eliminate truncation bias but already requires access to global connectivity; applying Kron only inside a truncated local graph cannot recover omitted exterior paths.

Approximate Schur complements offer a scalable research route. Durfee et al. (2017), Theorems 2.2--2.3 and Fact 5.4, give spectral approximation and terminal-resistance guarantees under connected undirected positive-weight assumptions. For this project the missing step is an efficient way to obtain a boundary response that includes the relevant exterior of an HNSW neighborhood without processing the full graph.

## Testable localization diagnostics

For sampled terminals, compare local scores to a wider symmetrized reference using absolute error, multiplicative error away from zero, Spearman/Kendall rank correlation, top-\(M\) overlap, and score-margin reversals. Keep \(\rho\) fixed across radii in the primary Rayleigh check; a separate experiment may study re-estimated weights. Measure whether high local scores concentrate on boundary vertices and whether exact small-graph Kron elimination removes the apparent bridge.
