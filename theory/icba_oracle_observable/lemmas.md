# Supporting lemmas

## L1 — Markov-kernel contraction

For transcript laws `P,Q` and any randomized decision kernel `K`, `TV(PK,QK)<=TV(P,Q)`. Hence policy randomization cannot defeat T-OO3.

## L2 — adaptive transcript KL

When the same predictable experiment-selection policy is run under two environments, its action-selection kernels cancel in the likelihood ratio and transcript KL is the expected sum of conditional observation KL terms.

## L3 — independent selected-action certification

If `A=S(D_sel)` and `D_cert` is independent, a marginally valid certificate for each fixed action remains valid for the randomly selected action conditional on `D_sel`. This fails without independence or simultaneous validity.

## L4 — robust safe-set screening

On `|hat rho(a)-rho(a)|<=epsilon_R`, the rule `hat rho(a)+epsilon_R<=delta` has no false-safe inclusions. It includes every action with `rho(a)<=delta-2epsilon_R`.

## L5 — amortized break-even

For overhead `K>=0`, baseline cost `C_B`, and recovery mixture cost `C_M`, `C_M+K/N<C_B` has a finite solution iff `C_M<C_B`; then it is equivalent to `N>K/(C_B-C_M)`.
