# Definitions

For a finite undirected nonnegative weighted graph, `L = D - W`. Within a connected component, the effective resistance is `R_eff(a,b) = (e_a-e_b)^T L^+ (e_a-e_b)`. A present edge has leverage `tau_e = w_e R_eff(e)`.

For center `u`, candidate direction `z_uv = (x_v-x_u)/||x_v-x_u||`. For selected rows `Z_S`, define `F_dir(S)=log det(I + sigma^-2 Z_S Z_S^T)`. Define `F_local(S)=sum exp(-d(u,v)^2/rho_u^2)` and `F_res(S)=sum tau_uv`, with leverages frozen on the pre-selection candidate graph. The local objective is `alpha F_res + beta F_dir + gamma F_local` under a cardinality budget.

