# Notation

Let `Theta` be a finite or measurable family of target build environments and let `theta ~ Pi` only when an explicit meta-distribution is assumed. Conditional on `theta`, a query `Q ~ P_theta`. The finite ordered budget grid is `B={b_1<...<b_L}`.

For target recall `tau`,

`b_theta^*(q)=min{b in B: Recall_theta(q,b)>=tau}`

when the set is nonempty. If the maximum budget fails, the query is endpoint-infeasible. A right-censored record only proves `b_theta^*(q)>b_L`; it does not prove feasibility or safety at `b_L`.

Recovery actions are `A={reuse,recalibrate,retrain,fallback}` plus an explicitly nondeployable oracle comparator. Action `a` induces a query-budget policy `pi_a(q;theta_s,Z_m)`.

Information is ordered as

`I_0 subseteq I_m subseteq I_theta`,

where `I_0` contains frozen source information and deployable metadata, `I_m=I_0 join sigma(Z_m)` contains purchased target evidence, and `I_theta` contains the complete target response. Randomized rules may also use an independent `U~Unif(0,1)`; this common randomizer is not target information.

`C_N(theta,a)` is total amortized cost, `rho_theta(a)` is query-level absolute failure risk, `delta` is the selected safety threshold, and `R_{delta,N}(I)` is the best expected total cost among `I`-measurable rules satisfying one fixed safety semantics.

The baseline action class is fixed throughout as the preregistered source-only/H2 class augmented by the same safe fallback used by richer classes. Comparisons never silently change the baseline class, loss, or safety semantics.
