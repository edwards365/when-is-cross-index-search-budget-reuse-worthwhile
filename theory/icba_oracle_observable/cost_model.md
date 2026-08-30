# Cost model

Online search cost is

`C_search(theta,a)=E_{Q~P_theta}[NDC_theta(Q,pi_a)]`.

Evidence and offline costs are

`C_evidence(a)=m_a c_truth+c_probe+c_certificate`,

and `C_offline(a)`. For workload `N`,

`C_N(theta,a)=C_search(theta,a)+(C_evidence(a)+C_offline(a))/N+C_control(a)`.

Unknown truth, training, and control costs remain symbolic and are never set to zero. Costs must use compatible units; raw NDC is implementation-local.

For a Lagrangian analysis, `L_lambda(theta,a)=C_N(theta,a)+lambda rho_theta(a)`, where `lambda>=0` has units of cost per unit failure probability. This is a soft-risk decision loss, not a replacement for a hard safety constraint. Hard-safety theorems restrict actions to `A_delta(theta)={a:rho_theta(a)<=delta}`.

Relative to a baseline per-query total cost `C_B`, a recovery rule with fixed overhead `K=C_evidence+C_offline` and online/fallback mixture cost `C_mix` has positive amortized value only if `C_mix<C_B` and

`N>K/(C_B-C_mix)`.

If `C_mix>=C_B`, no finite workload breaks even.
