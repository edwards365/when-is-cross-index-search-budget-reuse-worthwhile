# Candidate-edge models and rank-one identities

Let \(H\) be connected, undirected, and positive-weight, with Laplacian \(L\). All pseudoinverse formulas below are ordinary Sherman--Morrison formulas on \(\mathbf1^\perp\), extended by zero on \(\operatorname{span}\{\mathbf1\}\). Thus they require the updated graph to have the same one-dimensional kernel.

## Scheme A: frozen reference-edge leverage

Construct a reference graph \(H_u^A\) containing every selectable center--candidate edge, compute each existing-edge leverage, and freeze it. This is what the current `_local_candidate_leverage` implementation does: it union-symmetrizes candidate-to-candidate edges and adds the complete center star before scoring. It gives \(0<r_e^A\le1\) and supports the local submodularity proof, but the score refers to the augmented reference, not the current HNSW graph. Adding many candidate star edges can make individually useful missing edges appear redundant.

## Scheme B: score before adding a missing edge

For missing \(e=(a,b)\) with proposed conductance \(w>0\), put \(b_e=\mathbf e_a-\mathbf e_b\), \(R_e=b_e^\top L^+b_e\), and \(g_e=wR_e\). Then
\[
L'=L+w b_eb_e^\top,
\qquad
(L')^+=L^+-\frac{wL^+b_eb_e^\top L^+}{1+wR_e}.
\]
For any terminal contrast \(c\perp\mathbf1\),
\[
c^\top(L')^+c=c^\top L^+c-
\frac{w(c^\top L^+b_e)^2}{1+g_e}.
\]
The weighted spanning-tree partition obeys \(Z(H+e)/Z(H)=1+g_e\), so the log-tree gain is \(\log(1+g_e)\). The new edge's post-addition leverage is
\[
w b_e^\top(L')^+b_e=\frac{g_e}{1+g_e}<1.
\]
Unlike existing-edge leverage, \(g_e\) need not be at most one. This scheme directly measures topology before addition, but recomputing it after each choice does not yield the frozen modular term analyzed in the first selector.

For the insertion-log experiment, "before addition" has one further frozen convention: first apply the unmodified HNSW insertion and its reverse-neighbor pruning, induce the layer-0 graph on the new center plus the logged `efConstruction` result queue, and only then evaluate each rejected center--candidate edge. Evaluating before the standard insertion would leave the new center isolated, making every such resistance infinite. All three schemes share a per-insertion Gaussian scale equal to the median edge length in the union of this induced graph and the dense center star. This convention is an offline diagnostic, not an online selector.

## Scheme C: deletion sensitivity of an existing edge

For existing edge \(e\) with \(\tau_e=wR_e\), delete it:
\[
L'=L-wb_eb_e^\top.
\]
The graph stays connected iff \(1-\tau_e>0\), equivalently iff \(e\) is not a bridge. In that case
\[
(L')^+=L^++\frac{wL^+b_eb_e^\top L^+}{1-\tau_e},
\qquad
\frac{Z(H-e)}{Z(H)}=1-\tau_e.
\]
As \(\tau_e\uparrow1\), deletion sensitivity diverges; at \(\tau_e=1\), the formula is singular because deletion disconnects the graph. Scheme C is the mathematically appropriate score for pruning an existing undirected reference edge, but it still does not measure query direction.

## Consequence for swaps

A remove/add swap cannot be scored by subtracting one frozen number from another unless both are defined in the same frozen reference. Exact sequential swap gain is order-dependent through the two rank-one denominators. The controlled prototype should either (i) use Scheme A consistently and call the score a frozen surrogate, or (ii) specify an add-first/delete-second state and recompute Scheme B/C quantities, forfeiting the modular/submodular theorem.
