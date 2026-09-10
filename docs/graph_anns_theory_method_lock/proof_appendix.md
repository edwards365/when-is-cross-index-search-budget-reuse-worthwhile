# Proof appendix

## Proof of Main Theorem I

Introduce an induced binary decision \(\widehat I\): output 0 when the action lies in \(D_0\), output 1 when it lies in \(D_1\), and assign actions outside both sets arbitrarily. Because \(D_0\cap D_1=\varnothing\), an action outside \(D_i\) incurs loss at least \(\Delta\). Hence

\[
\mathbb E_0\ell_0+\mathbb E_1\ell_1
\ge \Delta\{P_0(\widehat I=1)+P_1(\widehat I=0)\}.
\]

The minimum sum of testing errors between \(P_0^T\) and \(P_1^T\) is \(1-\operatorname{TV}(P_0^T,P_1^T)\). Dividing by two and using that the maximum is at least the average proves

\[
\max_i\mathbb E_i\ell_i\ge \frac{\Delta}{2}(1-\operatorname{TV}).
\]

Bretagnolle–Huber gives the error-sum lower bound \(\tfrac12e^{-K_m}\), while Pinsker gives \(1-\sqrt{K_m/2}\). Substitution yields the two KL consequences. For adaptive observations, the KL chain rule gives

\[
K_m=\sum_{t=1}^m\mathbb E_0\!\left[\operatorname{KL}\{P_0(Y_t\mid H_{t-1},A_t)\Vert P_1(Y_t\mid H_{t-1},A_t)\}\right]\le mI_\star.
\]

Finally, data processing through the decision implies \(K_m\ge\operatorname{kl}(1-\beta,\beta)\) when both testing errors are at most \(\beta\). This completes the proof. The testing inequalities are classical; only the Graph-ANNS loss reduction is domain-specific.

## Proof of Main Theorem II

On \(\mathcal G\), every retained action satisfies

\[
r(a)\le \widehat r(a)+\varepsilon_R\le\delta.
\]

If \(r(a^\star)\le\delta-2\varepsilon_R\), then

\[
\widehat r(a^\star)+\varepsilon_R
\le r(a^\star)+2\varepsilon_R\le\delta,
\]

so \(a^\star\) is retained. Because \(\widehat a\) minimizes estimated cost among retained actions,

\[
C(\widehat a)\le\widehat C(\widehat a)+\varepsilon_C
\le\widehat C(a^\star)+\varepsilon_C
\le C(a^\star)+2\varepsilon_C.
\]

If every other safe action has true cost more than \(C(a^\star)+2\varepsilon_C\), these inequalities force exact selection on \(\mathcal G\).

Selection and certification roles are independent and the final candidate is frozen before certification. Therefore a valid one-sided certificate satisfies

\[
\Pr\{U_{\rm cert}<r(\widehat a)\}\le\alpha_{\rm cert}.
\]

The screening event fails with probability at most \(\alpha_{\rm sel}\). A union bound proves the stated \(1-\alpha\) guarantee. If certification rejects, the algorithm executes only an independently valid fallback; without one it abstains. Thus no unverified action is relabeled safe.

For the endpoint obstruction, every policy fails on the endpoint-infeasible subset, so \(r_E(\pi)\ge\eta_E\). The identifiability obstruction is Main Theorem I. The no-margin obstruction follows by considering Bernoulli risks \(\delta-\epsilon\) and \(\delta+\epsilon\); their finite-sample laws converge in total variation as \(\epsilon\downarrow0\). The independence and fallback counterexamples follow respectively from adaptive selection bias and from the absence of any safe action after rejection. These establish necessity as obstruction statements, not an iff characterization.

## Proof of Corollary 1

Applying Hoeffding at radius \(\gamma\) to each of \(M\) frozen actions and union bounding gives error probability at most \(2M e^{-2m\gamma^2}\), which yields the displayed order. With zero failures, the exact upper confidence endpoint is determined by \((1-\delta)^m\le\alpha_\ell\), yielding the ceiling formula. KL lower bounds follow from binary testing. No equality of upper and lower constants is asserted.

## Proof of Corollary 2

For service volume \(N\), subtract the total offline cost from the per-query net saving:

\[
\operatorname{Net}(N)=ND-(C_{\rm build}+C_{\rm operator}+C_{\rm truth}+C_{\rm cert}).
\]

If \(D\le0\), this quantity is never positive. If \(D>0\), it is positive exactly when \(N>N^*\). Quantiles are nonlinear functionals of mixtures, so no conclusion about p95 or p99 follows from this expectation identity.

## Appendix Proposition — Complete reverse-pair symmetry

Suppose every unordered build pair \(\{s,t\}\) appears as both \((s,t)\) and \((t,s)\) with equal weight and both budgets are finite. For each unequal pair, exactly one direction has \(B_s<B_t\) (under-budget transport) and the reverse has \(B_t>B_s\) (over-conservative transport). Equal-budget pairs contribute neither. Therefore

\[
P(\mathrm{under})=P(\mathrm{over})=\tfrac12P(B_s\ne B_t).
\]

This is a combinatorial identity. It explains why a complete symmetric pair design partially decomposes response heterogeneity; asymmetric source-to-held-out-target designs remain necessary for directional portability claims.
