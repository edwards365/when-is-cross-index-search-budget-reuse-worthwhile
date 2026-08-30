# Safety semantics

For action `a`,

`rho_theta(a)=P_{Q~P_theta}{Z_abs(Q,pi_a(Q),theta)=1}`.

The analysis uses one of three noninterchangeable semantics:

1. Fixed target: `rho_theta(a)<=delta` for a named target.
2. Meta average: `E_{theta~Pi} rho_theta(a)<=delta` under an explicit `Pi`.
3. Open-world uniform: `sup_{theta in Theta_new} rho_theta(a)<=delta`.

Fixed-target certification does not imply open-world safety. Meta-average safety does not imply pointwise safety. Query resampling does not create independent builds, and target evidence for one target does not certify an unseen build.

The fallback is assumed safe only when its own risk statement is explicitly supplied. A maximum observed budget is not automatically a safe fallback under endpoint infeasibility.

For selection and certification, `D_sel` and `D_cert` are disjoint. Conditional on `D_sel`, the selected action is fixed; a level-alpha one-sided bound computed solely from independent `D_cert` therefore needs no Bonferroni correction when only that action is certified. If certification data influence selection, simultaneous or selection-aware control is required.
