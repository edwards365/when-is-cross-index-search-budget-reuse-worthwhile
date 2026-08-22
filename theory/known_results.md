# Verified and rederived results

Status words are those in `proof_status.yaml`. Every statement below is scoped to a connected undirected graph with positive conductances unless its assumptions say otherwise.

## K1. Weighted cut-space projection and Foster identity

**Statement.** For \(L=BWB^\top\),
\[
P=W^{1/2}B^\top L^+BW^{1/2}
\]
is the orthogonal projector onto \(\operatorname{im}(W^{1/2}B^\top)\). Moreover \(P_{ee}=\tau_e\) and \(\sum_e\tau_e=N-1\).

**Derivation.** Put \(A=BW^{1/2}\), so \(L=AA^\top\) and \(P=A^\top(AA^\top)^+A\). A thin SVD \(A=U_r\Sigma_rV_r^\top\) gives \(P=V_rV_r^\top\), hence \(P=P^\top=P^2\) and its image is the row space of \(A\). Its diagonal is
\(w_e b_e^\top L^+b_e\). Connectivity gives \(r=\operatorname{rank}B=N-1\), so \(\operatorname{tr}P=N-1\), equal to the sum of its diagonal.

**Status/source.** `rederived_verified`; matches Lemma 3 of Spielman--Srivastava (2011). **Use:** identifies a normalized structural nonredundancy score. **Does not imply:** a distance-decreasing step, recall, or HNSW complexity.

## K2. Bounds and bridge equivalence

**Statement.** Each existing edge satisfies \(0<\tau_e\le1\), and \(\tau_e=1\) iff \(e\) is a bridge.

**Proof.** Positivity follows because the endpoints of an edge are distinct and connected. The direct edge is a resistance \(1/w_e\) path, so Thomson's principle gives \(R_e\le1/w_e\). If it is a bridge, every unit flow must send one unit through it and has energy at least \(1/w_e\); equality follows. If it is not a bridge, an alternative finite-resistance path is in parallel with the direct edge, making the equivalent resistance strictly smaller than \(1/w_e\). Multiplication by \(w_e\) proves the claim.

**Status/source.** `rederived_verified`; standard electrical-network consequence. **Use:** certifies local bridge edges. **Does not imply:** the bridge points toward any query or belongs in a degree-limited ANN graph.

## K3. Weighted random spanning-tree marginal

**Statement.** If spanning tree \(T\) has probability proportional to \(\prod_{e\in T}w_e\), then \(\Pr(e\in T)=\tau_e\).

**Proof sketch.** The matrix-tree theorem makes the tree partition function \(Z(w)\) any Laplacian cofactor. Differentiating \(\log Z\) with respect to \(\log w_e\) gives the inclusion probability on the combinatorial side and \(w_e b_e^\top L^+b_e\) on the matrix side.

**Status/source.** `imported_verified`; transfer-current/matrix-tree identity. `test_weighted_spanning_tree_marginals_equal_leverages` checks exact enumeration and sampling. **Does not imply:** a spanning-tree-important edge is useful to deterministic ANN navigation.

## K4. Rayleigh monotonicity and local bias

**Statement.** Increasing a conductance or adding an edge cannot increase any effective resistance. Thus, if a connected local reference graph \(H_u\) is a conductance-preserving subgraph of a connected global undirected graph \(H\), then \(R_{H_u}(a,b)\ge R_H(a,b)\).

**Proof.** By Thomson's principle, resistance is the minimum unit-flow energy \(\sum_e f_e^2/w_e\). Added edges enlarge the feasible flow set; increased conductance weakly lowers every affected energy term.

**Status/source.** `rederived_verified`. **Use:** predicts systematic local overestimation. **Limitation:** it gives no ranking guarantee. A ranking guarantee follows only from simultaneous error intervals narrow enough not to overlap; enlarging to two hops is an empirical mitigation, not a theorem. A sufficient structural condition is a common-kernel spectral approximation between the local terminal Schur complement and the global one.

## K5. Spectral approximation and resistance stability

**Statement.** Suppose \(\ker L=\ker\widetilde L=\operatorname{span}\{\mathbf1\}\) and, on \(\mathbf1^\perp\),
\((1-\varepsilon)L\preceq\widetilde L\preceq(1+\varepsilon)L\) with \(0\le\varepsilon<1\). Then
\[
\frac1{1+\varepsilon}L^+\preceq\widetilde L^+\preceq
\frac1{1-\varepsilon}L^+
\quad\text{on }\mathbf1^\perp,
\]
and the same multiplicative bounds hold for every effective resistance.

**Proof.** Restrict both matrices to \(\mathbf1^\perp\), where they are positive definite; inversion reverses Loewner order. Extend by zero on the common kernel and test against \(b_{uv}\).

If candidate edge weights are unchanged, the order \(\tau_e>\tau_f\) is certified stable whenever \(\tau_e/\tau_f>(1+\varepsilon)/(1-\varepsilon)\). With changed weights, the corresponding weight ratio must be included.

**Status/source.** spectral preservation is `imported_verified` from Spielman--Srivastava; the pseudoinverse and ranking corollaries are `project_proved`. **Does not imply:** preservation of adjacency-based greedy paths, top-k recall, beam width, or query distribution performance.

## K6. Commute time

**Statement.** For the reversible random walk with transition \(p_{uv}=w_{uv}/d_w(u)\),
\(\operatorname{Commute}(u,v)=\operatorname{vol}(H)R_H(u,v)\), where \(\operatorname{vol}(H)=\sum_vd_w(v)=2\sum_e w_e\).

**Status/source.** `imported_verified`; classical electrical-network identity. **Use:** interpretation of diffusion redundancy. **Does not imply:** HNSW NDC, because HNSW uses distance-prioritized deterministic/beam exploration, not this random walk.

## K7. Direction log determinant

Let \(A_S=I+\sigma^{-2}\sum_{v\in S}z_vz_v^\top\), \(\sigma>0\).

**Statement.** \(F_{\rm dir}(S)=\log\det A_S\) is normalized, monotone, and submodular, with
\[
\Delta(v\mid S)=\log\!\left(1+\sigma^{-2}z_v^\top A_S^{-1}z_v\right).
\]

**Proof.** The empty determinant is one. The matrix determinant lemma gives the displayed marginal, which is nonnegative. If \(S\subseteq T\), then \(A_S\preceq A_T\), hence \(A_T^{-1}\preceq A_S^{-1}\), so the marginal decreases. Sylvester's identity gives
\(\det(I_d+\sigma^{-2}Z_S^\top Z_S)=\det(I_{|S|}+\sigma^{-2}Z_SZ_S^\top)\).

**Status/source.** `rederived_verified`; consistent with log-determinant information-gain arguments used by Krause, Singh, and Guestrin (2008). Use Cholesky solves and `log1p`; never form an inverse or raw determinant numerically.

## K8. Frozen combined objective and greedy approximation

**Statement.** With frozen nonnegative \(r_v,\ell_v\), nonnegative coefficients, and \(\sigma>0\), \(F_u\) is normalized monotone submodular. Greedy selection under \(|S|\le M\) returns \(S_M\) satisfying
\[
F_u(S_M)\ge\left(1-(1-1/M)^M\right)F_u(S^*)\ge(1-1/e)F_u(S^*)
\]
for an optimum of size at most \(M\).

**Proof sketch.** The resistance and locality sums are modular; K7 is monotone submodular; nonnegative sums preserve both properties. The standard residual-gap recurrence proves the bound.

**Status/source.** `rederived_verified`; approximation factor from Nemhauser--Wolsey--Fisher (1978). **Scope:** one frozen DLS problem only. Reciprocal insertion, reverse pruning, and globally shared degree caps invalidate direct transfer of this factor.

**Greedy pseudocode.** Start with \(S=\varnothing\) and a Cholesky factor for the regularized Gram matrix. Until \(|S|=M\) or candidates are exhausted, evaluate the three-term marginal for every remaining candidate, choose the deterministic maximum, append it, and perform a rank-one factor update.

## K9. Strictly monotone paths

If \(d_X(x_t,q)-d_X(x_{t+1},q)\ge\delta>0\) until a target threshold \(r_q\) is reached, then
\(T\le\lceil(d_X(x_0,q)-r_q)/\delta\rceil\), and in particular \(T\le\lceil D/\delta\rceil\) when all distances lie in \([0,D]\).

Existence of one such path does not ensure pure greedy follows it. The algorithmic bound holds under the stronger condition that every non-target vertex it can reach has at least one \(\delta\)-improving neighbor: choosing the closest neighbor then improves by at least \(\delta\). Beam search inherits this trajectory only if its queue/termination rules retain and expand it; no universal `efSearch` bound follows from path existence alone.

**Status.** `project_proved` for the stated pure-greedy model; HNSW transfer is `partial`.

## Primary sources checked in this batch

- Malkov and Yashunin, HNSW, DOI: 10.1109/TPAMI.2018.2889473; author preprint arXiv:1603.09320.
- Spielman and Srivastava, *Graph Sparsification by Effective Resistances*, DOI: 10.1137/080734029; arXiv:0803.0929.
- Nemhauser, Wolsey, and Fisher, *An analysis of approximations for maximizing submodular set functions—I*, DOI: 10.1007/BF01588971.
- Krause, Singh, and Guestrin, *Near-Optimal Sensor Placements in Gaussian Processes*, JMLR 9 (2008).
- Indyk and Xu, *Worst-case Performance of Popular ANN Implementations*, NeurIPS 2023.
- Diwan et al., *Navigable Graphs for High-Dimensional Nearest Neighbor Search*, NeurIPS 2024.
