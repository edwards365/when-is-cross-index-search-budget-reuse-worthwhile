# Positive recovery theory

All guarantees below fix one target build. They are not outer-build, arbitrary-OOD, or new-query confirmation guarantees. Order statistics, conformal ranks, binomial tolerance bounds, and monotone cost arguments are classical tools; the project contribution is their restricted Graph-ANNS rebuild interpretation.

## Definitions

Let the frozen ordered budget grid be \(\mathcal B=\{0,\ldots,M-1\}\). For query \(q\), \(B_t(q)\) is the smallest certified-safe target budget and \(\hat b_s^{raw}(q)\) is the frozen deployable raw source prediction. Define \(D_t(q)=B_t(q)-\hat b_s^{raw}(q)\). Clipping to \(M-1\) is permitted only when the endpoint itself is certified; otherwise the method falls back or records failure.

## P1 — Fixed-target residual recovery

Status: `FORMAL_PROOF_COMPLETE_SUPPORTING_THEOREM`.

Assume the target build is fixed; the \(k\) sentinel residuals and the next-query residual are exchangeable; safety is monotone in budget; and the endpoint is certified. Before observing evaluation outcomes choose rank

\[
r=\lceil (k+1)(1-\delta_q)\rceil.
\]

When \(r\le k\), let \(\hat d_t=D_{(r)}\); when \(r=k+1\), use the certified endpoint/fallback (equivalently an infinite residual before clipping). Then

\[
\Pr\{B_t(q)>\hat b_s^{raw}(q)+\hat d_t\}\le\delta_q.
\]

**Proof.** Failure is \(D_t(q)>D_{(r)}\). Under exchangeability and conservative tie handling, the rank of the next residual among the \(k+1\) residuals is uniform or stochastically smaller than uniform. Hence the probability of rank greater than \(r\) is at most \((k+1-r)/(k+1)\le\delta_q\). Endpoint fallback covers the unavailable-rank case. Monotonicity turns a residual upper bound into query safety. ∎

This is a finite-sample marginal statement averaging over the random sentinel set and future query. It is not conditional-on-the-realized-calibration-set PAC control.

## P2 — PAC fixed-target risk certificate

Status: `FORMAL_PROOF_COMPLETE_SUPPORTING_THEOREM`.

Let \(p=\Pr\{D_t(q)>\max_iD_t(q_i)\}\). If the \(k\) exchangeable calibration observations contain zero exceedances above the selected maximum, the probability of observing that event when \(p>\delta_q\) is at most \((1-\delta_q)^k\). Thus, whenever

\[
(1-\delta_q)^k\le\alpha,
\]

the maximum-residual rule certifies \(p\le\delta_q\) with confidence at least \(1-\alpha\). For \(\alpha=\delta_q=0.05\),

\[
k_{min}=\left\lceil\log(0.05)/\log(0.95)\right\rceil=59.
\]

Therefore \(k=32\) is not PAC-eligible, whereas \(k=64,128,256\) are sample-size eligible subject to exchangeability and endpoint correctness. A later 744-query Clopper–Pearson evaluation is `EX_POST_EVALUATION_PASS`, not a deployment certificate obtained from 32 sentinels.

## P3 — Safe deconservatization

Status: `FORMAL_PROOF_COMPLETE_RESTRICTED_PROPOSITION`.

Let source-robust B1 use shift \(d_s\), and true target-only B2 use a P1- or P2-valid shift \(\hat d_t<d_s\). If search NDC \(C_t(b,q)\) is nondecreasing in budget, then pointwise

\[
C_t(\hat b_s^{raw}(q)+\hat d_t,q)\le C_t(\hat b_s^{raw}(q)+d_s,q),
\]

and therefore

\[
\Delta C_t=\mathbb E_t[C_t(\hat b_s^{raw}+d_s)-C_t(\hat b_s^{raw}+\hat d_t)]\ge0.
\]

**Proof.** The B2 budget does not exceed the B1 budget before or after monotone clipping. Apply NDC monotonicity pointwise and take expectations. B2 safety is inherited separately from P1 or P2, not from the cost inequality. ∎

The useful mechanism is that target information can safely remove the source-robust portability tax; it need not only increase an already conservative budget.

## P4 — Boundary of history value

### P4a: no cross-environment structure

Status: `COUNTEREXAMPLE_VERIFIED`.

Fix any target sentinel transcript and any history-assisted rule that outputs a smaller envelope than the target-only worst-case envelope. Construct two target residual distributions agreeing on every observed sentinel value: one puts all remaining mass below the smaller envelope, while the other puts more than \(\delta_q\) mass just above it. Historical residuals may be identical in both worlds because no relation to the target was assumed. The rule acts identically on both worlds and is unsafe in the second. Hence history alone cannot improve the worst-case fixed-target guarantee without a verifiable cross-environment restriction.

### P4b: structured residual domination

Status: `CONDITIONAL_RECOVERY_PROPOSITION_NOT_IDENTIFIED`.

If a preregistered, evaluation-independent condition establishes

\[
Q_{1-\delta}(D_t)\le Q_{1-\delta}(D_{hist})+\varepsilon_{stab},
\]

then the historical quantile plus \(\varepsilon_{stab}\), combined with a valid target-sentinel certificate and certified fallback outside support, yields the corresponding conditional fixed-target envelope. However, \(\varepsilon_{stab}\) cannot be chosen from target evaluation outcomes, and nine builds per dataset do not certify general outer stability. The present study therefore treats P4b as conditional and does not use it as the main positive conclusion unless B3 independently passes the History Value Gate.

## Evidence labels

- P1 configurations satisfying their rank rule: `MARGINAL_CONFORMAL_ELIGIBLE`.
- P2 configurations with \(k\ge59\): `PAC_FIXED_TARGET_ELIGIBLE`.
- Independent 744-query CP success: `EX_POST_EVALUATION_PASS`.
- Every configuration in this sprint: `OUTER_BUILD_NOT_CERTIFIED` and `PAIRED_QUERY_REPLAY_NOT_NEW_QUERY_GENERALIZATION`.
