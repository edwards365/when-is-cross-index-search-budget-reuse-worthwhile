# Theory repair and recovery boundary

All claims are fixed-target applications. They are not an outer-build theorem, a general confidence sequence, or a matching recovery phase transition.

## P1 — maximum-residual calibration-size monotonicity

**Status: CLASSICAL_ORDER_STATISTIC_APPLICATION.** Couple the samples by using one infinite i.i.d. residual sequence. For
\(S_n=\max(R_1,\ldots,R_n)\), \(S_{n+1}=\max(S_n,R_{n+1})\ge S_n\) almost surely, hence \(E S_{n+1}\ge E S_n\) whenever the expectations exist. If the residual CDF is \(F\), then \(P(S_n\le x)=F(x)^n\). Thus a larger maximum-residual calibration set is structurally more conservative; unequal sample sizes cannot be interpreted as a pure method contrast.

## P2 — unified-event ASRC fixed-target anytime safety

**Status: FORMAL_APPLICATION_THEOREM.** Freeze the ordered candidates and stages before observing sentinel outcomes. At stage \(j\), test the shared absolute event \(Z_{abs}\) with a valid one-sided Clopper–Pearson bound at level \(\alpha_j\). Fixed-sequence testing controls the first true-null rejection within a stage by \(\alpha_j\). For any sentinel-measurable stopping rule, the probability of any erroneous certification is at most \(\sum_j\alpha_j\le\alpha\) by the union bound. This is a structured application of classical CP, fixed-sequence testing and alpha spending; exchangeability/valid sampling for the fixed target is an explicit assumption.

## P3 — label complexity under a risk margin

**Status: FORMAL_APPLICATION_PROPOSITION.** Suppose the most aggressive safe candidate has risk at most \(\delta-\gamma\) and its adjacent unsafe candidate has risk at least \(\delta+\gamma\). Applying Hoeffding to each of \(J\) fixed candidates and a union bound gives sufficient label count
\[m\ge (2\gamma^2)^{-1}\log(2J/\alpha),\]
up to constants and possible improvement from exact binomial/KL bounds. Hence \(m=O(\log(J/\alpha)/\gamma^2)\). When \(\gamma\to0\), label demand diverges; without a margin, no finite uniform identification guarantee follows.

## P4 — cost-recovery sufficient condition

**Status: FORMAL_SYMBOLIC_PROPOSITION.** Let fixed overhead be \(A=C_{truth}+C_{sentinel}+C_{certificate}\), and let online costs be \(c_A,c_B\). ASRC beats baseline B at deployment volume \(N\) if \(A+Nc_A<Nc_B\). If \(c_B>c_A\), \(N^*=A/(c_B-c_A)\); otherwise `NO_FINITE_BREAK_EVEN`. Equivalently the maximum tolerable unmeasured truth cost at volume N is \(N(c_B-c_A)-C_{sentinel}-C_{certificate}\). Because truth timing is absent, only symbolic thresholds are valid.

## P5 — impossibility to conditional-recovery boundary

**Status: RESTRICTED_PROPOSITION / SYNTHESIS.** With no environment-identifying information, indistinguishable builds retain the inherited worst-case risk/conservative-cost lower bound. Valid target labels change the information model and can identify a fixed-target safe candidate under P2 and a positive margin under P3. Efficiency depends on \(\gamma,J\), label/truth cost, and across-build variation. No new outer build was sampled, and upper/lower rates are not matched; therefore the result is `FIXED_TARGET_ONLY_NOT_OPEN_WORLD_CERTIFIED`.
