# GSC theory-delta full report

## 1. Unified model

Fix dataset (X), construction parameters \(\theta\), and construction randomness \(\xi\). The build is (G_\xi=A_\theta(X,\xi)). Let \(\mathcal E=\{e_1,\ldots,e_L\}) be a preregistered raw fixed-`ef` grid. For query (q), define

\[
Z_{G,e}(q)=\mathbf 1\{\operatorname{Recall@10}(G,q,e)<\tau\ \lor\ \text{endpoint infeasible}\},
\]
\[
C_{G,e}(q)=\operatorname{NDC}(G,q,e),\qquad E_{G,e}(q)=\operatorname{actual\ expansions}(G,q,e),
\]
and the complete response vector \(\Phi_G(q)=(Z_{G,e}(q),C_{G,e}(q),E_{G,e}(q))_{e\in\mathcal E}\). Risk is \(r(G,e)=\mathbb E_q Z_{G,e}(q)\).

Separate diagnostics are required:

- (D_Z): disagreement or dispersion of failure-event vectors;
- (D_C): cost-response dispersion;
- endpoint-state disagreement;
- rank reversals across builds at each `ef`;
- raw fixed-`ef` response;
- expansion-prefix response.

No one of these quantities controls the others without an explicit assumption. A design objective may be written

\[
\min_{\theta,e}\ \mathbb E_{\xi,q}C_{G_\xi,e}(q)+\lambda_{95}\operatorname{CVaR}_{.95}(C)+\lambda_sD_{\rm resp}(\theta)+\lambda_bC_{\rm build}(\theta)
\]

subject to \(r(A_\theta(X,\xi),e)\le\delta-\gamma\) on a declared environment scope. This is an optimization target, not a solvability or improvement theorem.

## 2. T-GSC1 — adaptive generation with independent certification

**Statement.** Let \(\mathcal F_{\rm gen}\) contain all proposal, operator-validation, and adaptive-search observations. Let \(\widehat{\mathcal A}=g(\mathcal F_{\rm gen})) be a finite final action family, with \(|\widehat{\mathcal A}|\le M\) and (M) fixed before certification. Let the certification sample \(Q_1,\ldots,Q_n\) be independent of \(\mathcal F_{\rm gen}\), and let every final action's failure event be fixed before its certification outcomes are viewed. If for every possible frozen family the chosen one-sided bounds satisfy conditional coverage

\[
\Pr\left(\forall a\in\widehat{\mathcal A}:r(a)\le U_a\mid\mathcal F_{\rm gen}\right)\ge1-\alpha,
\]

then

\[
\Pr\left(\forall a\in\widehat{\mathcal A}:r(a)\le U_a\right)\ge1-\alpha,
\]

and any \(\mathcal F_{\rm gen}\)-measurable or certification-measurable selection from \(\{a:U_a\le\delta\}\) is safe with probability at least \(1-\alpha\).

**Proof.** Condition on \(\mathcal F_{\rm gen}=f). The family is then fixed and independent certification gives the displayed conditional event with probability at least \(1-\alpha). Taking expectation over (f) preserves the bound. On the simultaneous event, every selected certified action has \(r(\widehat a)\le U_{\widehat a}\le\delta). The proof fails if certification outcomes are used to add/drop or alter actions, because the conditional family is no longer fixed; repeated inspection requires a confidence sequence, alpha spending, or a uniform bound over the generation space. Multiple adaptive tracks require their union in (M) or another simultaneous procedure. **Status:** `FORMAL_PROOF_COMPLETE`; **classification:** `CLASSICAL_CONDITIONAL_INFERENCE_APPLICATION`.

## 3. T-GSC2 — baseline inclusion and safe fallback

**Statement.** If a preregistered fixed-safe baseline action (b) is included in every final family and has a valid certificate \(r(b)\le\delta\) on event probability (1-\alpha_b), then the fallback rule “select a certified candidate if one exists, otherwise deploy (b)” is safe with probability at least (1-\alpha_b-\alpha_c), where \(\alpha_c) is the candidate-family certificate error. If (b) is certified jointly with the family, the errors are covered by one simultaneous event.

This proves availability of a safe action, not NDC or p95 non-inferiority. A baseline can be safe but more expensive than every GSC action; a candidate can be selected incorrectly if it was not included in the simultaneous family; and a mixture that improves mean NDC can worsen p95. **Status:** `FORMAL_PROOF_COMPLETE`; **classification:** `CLASSICAL_APPLICATION`.

## 4. T-GSC3 — certifiability margin and acceptance probability

For one candidate with (r(a)\le\delta-\gamma), a Hoeffding upper bound that rejects only when

\[
\widehat r_n+\sqrt{\frac{\log(M/\alpha)}{2n}}\le\delta
\]

is sufficient whenever \(n\ge\log(M/\alpha)/(2\gamma^2)\), up to the chosen finite-sample constant. Exact CP is more conservative near boundaries but retains finite-sample validity. A Bernoulli-KL bound replaces the quadratic radius by the solution (u) of \(n\,\mathrm{kl}(\widehat r_n\|u)=\log(M/\alpha)), giving the same local \(\gamma^{-2}\log(M/\alpha)) order away from 0 and 1.

For zero failures, one-sided CP gives (U=1-(\alpha/M)^{1/n}). Thus \(U\le\delta) requires

\[
n\ge m_{\min}=\left\lceil\frac{\log(\alpha/M)}{\log(1-\delta)}\right\rceil.
\]

At \(\alpha=\delta=.05\), (M=36), the zero-failure threshold is 129; (M=24) gives 121. The probability of rejection decreases as the positive margin \(\gamma) grows, but its exact power depends on the distribution and bound. “Safe but rejected” remains possible and is not a safety violation. **Status:** `FORMAL_PROOF_COMPLETE`; **classification:** `CLASSICAL_APPLICATION`.

## 5. T-GSC4 — positive net-benefit condition

Let (G_{\rm online}) denote the realized mean per-query saving against the registered baseline, (p_R=P(R)) the certification-rejection probability, and \(\Delta C_f\) the fallback gap. Define

\[
D=G_{\rm online}-p_R\Delta C_f-C_{\rm control}.
\]

Offline costs are (C_{\rm build}+C_{\rm operator}+C_{\rm truth}+C_{\rm cert}). Total net improvement over workload (N) is

\[
ND-(C_{\rm build}+C_{\rm operator}+C_{\rm truth}+C_{\rm cert}).
\]

If (D\le0), report `NO_FINITE_BREAK_EVEN_WORKLOAD`. If (D>0),

\[
N^*=\frac{C_{\rm build}+C_{\rm operator}+C_{\rm truth}+C_{\rm cert}}{D}.
\]

This is a cost identity/classical composition, classified `NEW_COMBINATION_OF_CLASSICAL_RESULTS` only as a GSC service-accounting package. Mean algebra does not control p95; tail and workload uncertainty require separate gates.

## 6. T-GSC5 — behavioral stability and transfer-risk relation

### General non-implication

No general implication (D_C\to D_Z) is valid. Two builds may have identical costs for every query but opposite endpoint feasibility; a single query may carry all failure disagreement while average cost dispersion tends to zero; and high edge overlap can coexist with a changed search endpoint. Likewise, low rank reversal does not imply low risk difference when both builds preserve the same ranking but cross \(\tau\) on a rare query.

### Restricted event bound

For any two fixed builds and raw action (e),

\[
r(G',e)=\mathbb E Z_{G',e}\le r(G,e)+\Pr_q[Z_{G,e}(q)\ne Z_{G',e}(q)].
\]

This follows from (Z_{G'}\le Z_G+|Z_{G'}-Z_G|). It is a restricted proposition/identity: to use it operationally, the disagreement probability must itself be estimated on independent data, and the same target query distribution and endpoint semantics must be used.

### Structural layer

An expansion-prefix result may be stated only if the search implementation is fixed, a priority-margin condition ensures the chosen frontier is unchanged, intruders are bounded, repair never removes the critical state, and the trace fields are observable. Under those assumptions a trace disagreement bound may control prefix behavior. Nothing here transfers to raw `ef` unless an independent map from `ef` to expansion prefix is proved. **Status:** `FORMAL_PROOF_RESTRICTED`; **classification:** `IDENTITY_OR_RESTRICTED_PROPOSITION`.

## 7. T-GSC6 — finite adaptive candidate search and generalization

If proposal/validation search runs for at most 24 operator trials and 3 generations, all choices belong to \(\mathcal F_{\rm gen}\). Independent certification absorbs arbitrary finite adaptive selection, provided the final family is frozen and its simultaneous size/control is fixed. Validation estimates may be adaptively reused for design but do not become independent evidence; final evaluation is read once after all action and threshold choices are frozen. Selecting the best of multiple tracks after viewing the same evaluation requires a union adjustment or a fresh holdout.

The result is sample splitting plus finite-family inference, not a new uniform-convergence or Hyperband theorem. **Status:** `FORMAL_PROOF_COMPLETE`; **classification:** `CLASSICAL_CONDITIONAL_INFERENCE_APPLICATION`.

## 8. T-GSC7 — conditional small-closure theorem

Suppose the frozen GSC candidate (a^*) satisfies (r(a^*)\le\delta-\gamma), has mean-online improvement at least (g_0>0), meets all registered non-inferiority tolerances, and is selected by an independent valid certificate. If workload (N>N^*) under T-GSC4, then on the intersection of the certificate, metric-validation, and cost-accounting events the deployed choice is safe and has positive total mean benefit relative to baseline. It is a conditional Pareto improvement only for the registered metrics and track.

The theorem assumes the generator produced (a^*); it does not prove candidate attainability, open-world safety, all-metric SOTA, or generalization beyond the registered target/build scope. **Status:** `FORMAL_PROOF_COMPLETE`; **classification:** `RESTRICTED_DOMAIN_PROPOSITION`.

## 9. T-GSC8 — environment control versus environment inference

Let hidden build environment \(\xi\) induce an observation law (P_\xi). Inference attempts to identify \(\xi\) or the best action from observations. Control chooses \(\theta\) to shrink the attainable response set \(\{\Phi_{A_\theta(X,\xi)}:\xi\in\Xi\}\). If control produces a singleton or a class in which all environments share the same safe action, no latent-environment identification is needed for that closed class. Conversely, if two uncontrolled or controlled environments remain observationally indistinguishable but have different safe actions, Le Cam/Blackwell no-free-lunch reasoning remains in force.

GSC therefore changes the environment class and possibly the observation channel; it does not abolish the lower bound. Calling a narrowed registered family “stable” is a closed-world design statement, not open-world inference. **Status:** `FORMAL_PROOF_RESTRICTED`; **classification:** `RESTRICTED_DOMAIN_PROPOSITION`.

## 10. Scope summary

The mathematical closure supports fixed-target, registered finite-family safety after adaptive generation and a conditional service-cost decision rule. It does not support an unconditional structure-to-raw-`ef` bridge, a guaranteed good candidate generator, open-world rebuild safety, or a new general theory of adaptive testing.

