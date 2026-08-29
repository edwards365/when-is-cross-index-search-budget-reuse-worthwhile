# ASRC theory

Evidence ceiling: `CROSS_FITTED_DESIGN_EVIDENCE`. Every guarantee fixes one target build and assumes future queries and the relevant target fold are i.i.d./exchangeable from the same target query law. Nothing here certifies outer-build or arbitrary-OOD risk, and the statistical ingredients are classical.

## A1 — Cross-fitted residual validity

Status: `FORMAL_PROOF_COMPLETE_SUPPORTING_THEOREM`.

In each cycle, source train, source calibration, target sentinel and target evaluation are disjoint query-ID sets. Condition on the source-training fold and fitted raw predictor. If target sentinel and future target queries are exchangeable under the fixed target law, the induced residuals \(D_t(q)=B_t(q)-\hat b_s^{raw}(q)\) are exchangeable, so fixed-target order-statistic/binomial certificates apply. Source calibration is disjoint and affects B1 only. Target evaluation affects neither model, shift, stopping, cost threshold nor method selection.

**Proof.** Conditioning fixes the predictor as a measurable function trained without sentinel/evaluation queries. Applying that fixed function to exchangeable target queries preserves exchangeability of residuals. The role partition removes direct reuse dependencies. Query-ID disjointness is not itself a proof of exchangeability; the common target-query-law assumption remains necessary. ∎

## A2 — Fixed-sequence shift certification

Status: `FORMAL_PROOF_COMPLETE`.

For a stage \(j\), let \(p_d=\Pr\{B_t(q)>clip(\hat b_s^{raw}(q)+d)\}\). Monotonicity gives \(p_{11}\le\cdots\le p_0\). Test the ordered nulls \(H_d:p_d>\delta_q\) from \(d=11\) down to 0 using a one-sided exact binomial/Clopper–Pearson level-\(\alpha_j\) test; continue while the null is rejected (candidate certified) and stop at the first non-rejection. Deploy the smallest rejected shift before that stop.

The probability of certifying any unsafe candidate is at most \(\alpha_j\), without a factor 12.

**Proof.** If unsafe candidates exist, monotonicity makes them a terminal block in the tested order. Reaching and rejecting any unsafe candidate requires rejecting the first true null in that block. The test of that first true null has type-I error at most \(\alpha_j\), irrespective of preceding false-null rejections. If no unsafe candidate exists there is no error. This is the standard fixed-sequence argument for a nested ordered family. ∎

The implementation must use candidate order 11→0 and stop at the first non-certified candidate. Result-dependent switching to Bonferroni is forbidden.

## A3 — Anytime safety

Status: `FORMAL_PROOF_COMPLETE`.

Let stages be \(k=(80,128,250)\) with \(\alpha_j=0.05/3\). At each stage deploy only a candidate from the A2-certified set, or a certified fallback. For any stopping rule measurable with respect to the accumulated sentinel transcript and cost calculations,

\[
\Pr\{\exists j:\text{unsafe deployment at stage }j\}\le\sum_j\alpha_j=0.05.
\]

**Proof.** A2 bounds each stage's unsafe-certification event by \(\alpha_j\). The stop rule can choose among certified actions but cannot enlarge these events. A union bound across stages yields the result; independence across stages is unnecessary. ∎

This proves safety-valid stopping, not cost-optimal stopping. Evaluation success is an ex-post diagnostic, not part of the certificate.

## A4 — Safe fallback

Status: `FORMAL_PROOF_COMPLETE_RESTRICTED_PROPOSITION`.

An ASRC candidate inherits its A2/A3 certificate. If no candidate is certified, B6 inherits the independently certified endpoint guarantee. If an already-certified B1 is retained under the frozen rule, it must separately pass the target-stage certificate; otherwise B6 is used. None of these choices reads target evaluation. Safety therefore does not depend on the cost model being correct. ∎

## A5 — Cost-aware stopping

Status: `FORMAL_PROOF_COMPLETE_RESTRICTED_PROPOSITION`.

For certified shifts \(d'<d\), monotone search effort gives \(C(d')\le C(d)\) per query, while calibration cost is nondecreasing with acquired labels \(k\). Against B1, a fixed certified ASRC action with positive online saving has search-side break-even

\[
N^*=C_{cal}/(C(B1)-C(ASRC)).
\]

If the denominator is nonpositive, no finite break-even exists. Thus the preregistered N0=100000 stopping check can be computed from sentinel-only NDC and calibration cost. This proposition does not give an oracle inequality against the best fixed k, and truth-generation cost remains external when unmeasured.

## A6 — Information lower bound

Status: `FORMAL_PROOF_COMPLETE_SUPPORTING_RESULT`.

With zero observed failures, excluding risk greater than \(\delta_q\) at confidence \(1-\alpha\) requires \((1-\delta_q)^k\le\alpha\), hence \(k=\Omega(\delta_q^{-1}\log(1/\alpha))\). Under equal three-stage alpha spending, \(\alpha_j=0.05/3\), the first eligible integer is

\[
\lceil\log(0.05/3)/\log(0.95)\rceil=80.
\]

This is classical binomial/testing logic, not a new universal lower bound.

## Theory–implementation constants

- seed 991; folds 4×250;
- stages 80,128,250, nested within each repetition;
- alpha 0.05, delta 0.05, alpha per stage 1/60;
- shift order 11 down to 0;
- stop testing after the first non-certified more-aggressive candidate;
- B6 fallback when no permitted candidate/B1 is certified;
- no history, fingerprint, source-shift lower bound, Oracle input or evaluation-driven choice.
