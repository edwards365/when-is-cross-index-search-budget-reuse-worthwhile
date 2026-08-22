# Verified lemmas

## Bridge leverage

For a weighted bridge edge `e` with conductance `w_e`, every unit current between its endpoints must cross `e`, so the voltage drop is `1/w_e`; hence `R_eff(e)=1/w_e` and `tau_e=1`.

## Local objective

With fixed nonnegative leverage/locality weights, `F_res` and `F_local` are nonnegative modular functions. `log det(I + sigma^-2 sum_{v in S} z_v z_v^T)` is normalized, monotone, and submodular for `sigma>0`; the row-Gram form in the implementation has the same nonzero determinant by Sylvester's determinant identity. A nonnegative weighted sum is therefore normalized monotone submodular. Cardinality-constrained greedy obtains the standard `1-1/e` approximation to this local frozen-score objective.

This statement provides no global recall, navigability, or HNSW query-complexity guarantee.

## Rank-one insertion and deletion

For connected (L), contrast (b\perp\mathbf1), and conductance (w>0), adding (wbb^\top) preserves the kernel and
\[
(L+wbb^\top)^+=L^+-\frac{wL^+bb^\top L^+}{1+w b^\top L^+b}.
\]
Deleting an existing edge uses the plus sign and denominator (1-wR), provided it is positive. Denominator zero is exactly the bridge/disconnection boundary. Matrix-tree ratios are (Z'/Z=1+wR) for insertion and (1-\tau_e) for deletion. Numerical tests compare these identities with direct pseudoinverses and cofactor enumeration.

## Exact terminal localization

Partition a connected Laplacian into terminals (T) and interior (I), with invertible grounded (L_{II}). The Schur complement (L_{TT}-L_{TI}L_{II}^{-1}L_{IT}) has the same terminal Dirichlet energy and therefore the same pairwise terminal effective resistances. Induced-radius graphs do not enjoy this equality.
