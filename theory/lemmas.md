# Verified lemmas

## Bridge leverage

For a weighted bridge edge `e` with conductance `w_e`, every unit current between its endpoints must cross `e`, so the voltage drop is `1/w_e`; hence `R_eff(e)=1/w_e` and `tau_e=1`.

## Local objective

With fixed nonnegative leverage/locality weights, `F_res` and `F_local` are nonnegative modular functions. `log det(I + sigma^-2 sum_{v in S} z_v z_v^T)` is normalized, monotone, and submodular for `sigma>0`; the row-Gram form in the implementation has the same nonzero determinant by Sylvester's determinant identity. A nonnegative weighted sum is therefore normalized monotone submodular. Cardinality-constrained greedy obtains the standard `1-1/e` approximation to this local frozen-score objective.

This statement provides no global recall, navigability, or HNSW query-complexity guarantee.

