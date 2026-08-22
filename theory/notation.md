# Notation contract

This file is normative. A symbol must not be reused with a different meaning in another theory file.

## Data, distance, and truth

- \(X=\{x_1,\ldots,x_n\}\subseteq\mathbb R^d\): indexed data set; \(n\) is its size and \(d\) its ambient dimension.
- \(q\): a query, not necessarily in \(X\).
- \(d_X(x,y)\): the nonnegative distance or dissimilarity used by construction and search. We write \(\|x-y\|_2\) only when Euclidean structure is assumed.
- \(k\): requested number of neighbors; \(N_k(q)\): exact top-\(k\) set under a declared deterministic tie rule.
- \(Q\): query distribution or a fixed held-out query set, stated in context.

## HNSW and local selection

- \(G_s^\pi=(G_{s,0}^\pi,\ldots,G_{s,L}^\pi)\): HNSW built with insertion permutation \(\pi\) and random seed \(s\).
- \(G_{s,\ell}^\pi=(V_\ell,E_\ell)\): directed layer \(\ell\); \(G_{s,0}^\pi\) is the bottom layer.
- \(N_G^+(u)\), \(N_G^-(u)\): outgoing and incoming search neighbors. \(N_G(u)\) is used only for an explicitly undirected graph.
- \(M\): local selection budget. \(M_{\max}\) and \(M_{\max,0}\): stored degree caps above and at layer zero.
- \(C_u\): frozen candidate ground set for base vertex \(u\); \(c=|C_u|\).
- \(S_u\subseteq C_u\): selected outgoing neighbors, \(|S_u|\le M\).
- \(H_u=(V_u,E_u,w_u)\): connected, undirected, positive-conductance local reference graph used only to score candidates. It is not an HNSW search layer.
- \(\bar G_0\): an explicitly declared symmetrization of the directed bottom layer. Parallel edges and weight aggregation must be specified.
- \(G^{\mathrm{repair}}\): graph after a declared repair operation.

The following models are distinct: **DLS**, directed local selection with independent budgets; **SLR**, symmetric local repair with reciprocal insertion and pruning; **GDCR**, global degree-constrained rewiring. A DLS guarantee is not a guarantee for SLR or GDCR.

## Query process

- \(V(q;G)\): set of vertices visited by the declared search algorithm.
- \(C_{\mathrm{search}}(q;G)\): generic cost; it must name the counted operation.
- \(\operatorname{NDC}(q;G)\): exact number of calls to the distance function, including the bottom layer.
- \(\operatorname{Rec}@k(q;G)=|\widehat N_k(q;G)\cap N_k(q)|/k\).
- \(ef^*(q;G,R)=\min\{ef:\operatorname{Rec}@k(q;G,ef)\ge R\}\), or \(+\infty\) if the tested grid never reaches \(R\). This is an offline oracle statistic.
- \(x_0,\ldots,x_T\): a pure-greedy trajectory; \(\mathcal T(q)\subseteq X\): declared target region.

## Graph linear algebra

Unless stated otherwise, \(H=(V,E,w)\) is a connected undirected multigraph with \(N=|V|\), \(m=|E|\), and conductances \(w_e>0\). An arbitrary orientation fixes:

- \(b_e=\mathbf e_u-\mathbf e_v\in\mathbb R^N\): incidence column for \(e=(u,v)\).
- \(B=[b_e]_{e\in E}\in\mathbb R^{N\times m}\): vertex-by-edge incidence matrix.
- \(W=\operatorname{diag}(w_e)\); \(L=BWB^\top\); \(L^+\): Moore--Penrose pseudoinverse.
- \(R_H(a,b)=b_{ab}^\top L^+b_{ab}\): effective resistance.
- \(\tau_e^H=w_e b_e^\top L^+b_e\): leverage of an existing edge.
- \(P_H=W^{1/2}B^\top L^+BW^{1/2}\): weighted cut-space projector.
- \(\lambda_i(L)\): nondecreasing Laplacian eigenvalues.
- \(\Phi_H(A)=w(A,V\setminus A)/\min\{\operatorname{vol}(A),\operatorname{vol}(V\setminus A)\}\): conductance of a nontrivial vertex set; \(\Phi(H)=\min_A\Phi_H(A)\).
- \(\operatorname{vol}(H)=\sum_v d_w(v)=2\sum_e w_e\).

## Frozen local objective

- \(z_v=(x_v-x_u)/\|x_v-x_u\|_2\), requiring \(x_v\ne x_u\).
- \(\sigma>0\): direction regularizer; \(A_S=I_d+\sigma^{-2}\sum_{v\in S}z_vz_v^\top\).
- \(F_{\mathrm{dir}}(S)=\log\det A_S\).
- \(r_v=\tau_{(u,v)}^{H_u}\): frozen before selection.
- \(\rho_u>0\); \(\ell_v=\exp[-d_X(u,v)^2/\rho_u^2]\).
- \(F_u(S)=\alpha\sum_{v\in S}r_v+\beta F_{\mathrm{dir}}(S)+\gamma\sum_{v\in S}\ell_v\), with \(\alpha,\beta,\gamma\ge0\).
- \(\Delta_F(v\mid S)=F(S\cup\{v\})-F(S)\); \(g_t\): winner-minus-runner-up margin at greedy step \(t\).

## Stability and hardness

- \(D_E(G,G')=1-|E\cap E'|/|E\cup E'|\), with \(0/0:=0\).
- \(D_\tau(G,G';H)=\sum_{e\in E\triangle E'}\tau_e^H/\sum_{e\in E\cup E'}\tau_e^H\). Scores come from one frozen reference \(H\); otherwise the quantity is not comparable.
- \(S_C(q)=\operatorname{Var}_{\pi,s}[\operatorname{NDC}(q;G_s^\pi)]\), \(S_R(q)=\operatorname{Var}_{\pi,s}[\operatorname{Rec}@k(q;G_s^\pi)]\), and \(S_{ef}(q)=\operatorname{Var}_{\pi,s}[ef^*(q;G_s^\pi,R)]\).
- \(H_{\mathrm{geom}}(q)\): a preregistered vector of geometric covariates such as LID, relative contrast, and neighbor gap.
- \(H_{\mathrm{nav}}(q;G)\): graph-dependent diagnostic vector such as failed monotone steps, bottleneck crossings, and frontier growth. It is not identified with \(H_{\mathrm{geom}}\).
