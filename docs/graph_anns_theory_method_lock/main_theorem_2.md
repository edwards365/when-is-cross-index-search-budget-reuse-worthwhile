# Main Theorem II — Finite-class conditional recoverability

## Statement

Fix a named target environment \(E_t\), a frozen finite action family \(\mathcal A=\{a_1,\ldots,a_M\}\), a declared query distribution \(P_Q\), and endpoint-aware losses. Suppose:

1. **Endpoint feasibility:** at least one action has risk at most \(\delta-2\gamma\) for some \(\gamma>0\).
2. **Identifiable registered conflict:** the selection transcript contains enough information to distinguish action-relevant alternatives in the registered class; equivalently, the Main-I lower bound is below the allowed decision loss for this class.
3. **Positive margin:** a useful action is separated from the risk boundary by at least \(2\gamma\).
4. **Independent target evidence:** candidate generation/selection and final certification use independent query roles; all candidates and multiplicity corrections are frozen before certification.
5. **Valid fallback or abstention:** rejection invokes an independently justified action under the same failure semantics, or emits `ABSTAIN_NO_SAFE_ACTION`.

Let selection data produce estimates \(\widehat r(a)\), \(\widehat C(a)\) and a simultaneous event

\[
\mathcal G=\left\{\sup_{a\in\mathcal A}|\widehat r(a)-r(a)|\le\varepsilon_R,
\ \sup_{a\in\mathcal A}|\widehat C(a)-C(a)|\le\varepsilon_C\right\}
\]

with \(\Pr(\mathcal G)\ge 1-\alpha_{\rm sel}\). Screen actions by \(\widehat r(a)+\varepsilon_R\le\delta\), select the minimum estimated-cost retained action, and certify only the final frozen action on independent data with a valid one-sided upper bound \(U_{\rm cert}\) at level \(\alpha_{\rm cert}\). Deploy the selected action only when \(U_{\rm cert}\le\delta\); otherwise use the valid fallback or abstain.

Then, with \(\alpha_{\rm sel}+\alpha_{\rm cert}\le\alpha\),

\[
\Pr\!\left(r_{E_t}(\widehat a)\le\delta\ \text{or a valid fallback/abstention is invoked}\right)\ge 1-\alpha.
\]

On \(\mathcal G\), every screened action is safe. If the minimum-cost safe action \(a^\star\) satisfies \(r(a^\star)\le\delta-2\varepsilon_R\), it is retained and the selected action obeys

\[
C(\widehat a)\le C(a^\star)+2\varepsilon_C.
\]

If the safe optimum is unique and its cost gap exceeds \(2\varepsilon_C\), the selection stage recovers it exactly on \(\mathcal G\).

## Necessary obstructions, not an iff characterization

The theorem deliberately does **not** claim an if-and-only-if result. The five items combine distinct obstruction statements with one sufficient protocol:

- If the registered endpoint mass \(\eta_{E_t}>\delta\), every policy confined to the action family has risk at least \(\eta_{E_t}\).
- If action-relevant environments are transcript-indistinguishable, Main Theorem I forces nonzero decision loss.
- Without a positive margin, arbitrarily close Bernoulli risks on opposite sides of \(\delta\) preclude uniform finite-sample power.
- Reusing selection evidence for an adaptively chosen candidate invalidates a nominal single-candidate certificate unless selection is included in simultaneous control.
- Without a separately safe fallback, rejection cannot be reinterpreted as safe deployment and must remain abstention.

These counterexamples show why the premises matter; they do not prove that every conceivable recovery method must literally take this form.

## Corollary 1 — Certification scale

For a frozen family of \(M\) actions and margin \(\gamma\), classical uniform concentration gives the sufficient order

\[
m=O\!\left(\frac{\log(M/\alpha)}{\gamma^2}\right).
\]

For zero observed failures and per-action level \(\alpha_\ell\), the exact one-sided Clopper–Pearson requirement is

\[
m_{\min}=\left\lceil\frac{\log\alpha_\ell}{\log(1-\delta)}\right\rceil.
\]

Hoeffding/Bonferroni and Clopper–Pearson are classical sufficient tools; Bernoulli-KL testing supplies lower bounds. No exact universal matching rate is claimed. Query count \(m\), environment count, action count \(M\), sentinel resolution, and workload size control different errors and are not interchangeable.

## Corollary 2 — Economic feasibility

Let

\[
D=G_{\rm online}-R_{\rm selection}-\Pr(R)\Delta C_f-C_{\rm control}.
\]

If \(D\le0\), the method reports `NO_FINITE_BREAK_EVEN_WORKLOAD`. If \(D>0\), the service-volume threshold is

\[
N^*=\frac{C_{\rm build}+C_{\rm operator}+C_{\rm truth}+C_{\rm cert}}{D}.
\]

This is an accounting identity, not an efficiency theorem. Mean gain does not imply p95 or p99 improvement; tail latency is a separate gate. If truth, retraining, control, or fallback costs are missing, deployment economics are `NOT_ESTIMABLE`.
