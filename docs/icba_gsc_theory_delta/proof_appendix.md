# GSC proof appendix and counterexample proofs

## A. Sigma-field proof for T-GSC1

Let \(\mathcal H=\sigma(\mathcal F_{\rm gen})\). Conditional on \(\mathcal H\), the random final family is a constant finite set and the certification sample remains independent. For each fixed family, Bonferroni/CP gives \(P(E_{\rm cert}\mid\mathcal H)\ge1-\alpha). The tower property gives

\[
P(E_{\rm cert})=E[P(E_{\rm cert}\mid\mathcal H)]\ge1-\alpha.
\]

If a certification observation changes \(\widehat{\mathcal A}\), then \(\widehat{\mathcal A}\) is not \(\mathcal H\)-measurable and the conditioning argument no longer applies. Replacing CP by an anytime-valid confidence sequence repairs optional stopping only when the filtration and predictable sampling rule are explicitly defined.

## B. Risk disagreement inequality

Since (Z_{G',e}\le Z_{G,e}+|Z_{G',e}-Z_{G,e}|), taking expectations gives

\[
r(G',e)\le r(G,e)+P(Z_{G',e}\ne Z_{G,e}).
\]

The symmetric absolute difference also yields \(|r(G',e)-r(G,e)|\le P(Z_{G',e}\ne Z_{G,e})). The bound is tautological unless the disagreement probability is independently estimable or structurally upper-bounded.

## C. CP zero-failure acceptance

For (X=0) failures among (n) independent Bernoulli observations, the exact upper endpoint satisfies \((1-U)^n=\alpha_a\). Hence (U=1-\alpha_a^{1/n}), and (U\le\delta) iff \(n\ge\log(\alpha_a)/\log(1-\delta)). The ceiling is necessary because (n) is integer.

## D. Net-benefit identity

Writing (C_{\rm GSC}=C_{\rm online}+C_{\rm control}+C_{\rm offline}/N+p_R\Delta C_f), subtraction from baseline gives exactly (G_{\rm online}-C_{\rm control}-p_R\Delta C_f-C_{\rm offline}/N). Multiplying by (N) yields the break-even expressions. No distributional assumption is used; the identity does not certify estimates.

## E. Structural counterexample constructions

1. **Same cost, different endpoint:** for every query set (C_{G,e}=C_{G',e}=10), but (Z_{G,e}=0) and (Z_{G',e}=1) on one query. Then (D_C=0) and (D_Z>0).
2. **High edge overlap, changed endpoint:** let two graphs share 99% of edges but alter the unique entry bridge used by one query; the changed bridge makes the target unreachable. Jaccard similarity alone gives no endpoint guarantee.
3. **Rare high-risk query:** with (n) query points, let only one point disagree in (Z); average disagreement is (1/n), while the worst-query event changes from 0 to 1.
4. **Cost rank stable, safety different:** preserve the cost ordering of all builds but change one endpoint event at the target threshold. Rank-reversal rate is zero while risk differs.
5. **Raw `ef` nonmonotonicity:** use fixed runs with recall 1 at (e=40) and .9 at (e=80); no raw envelope follows from an expansion-prefix theorem.

## F. Baseline and candidate counterexamples

- A baseline can have (r\le\delta) and large mean NDC, while a GSC candidate has lower mean NDC but is rejected or fails a p95 gate.
- If the baseline is not in the simultaneous family, a post-certification candidate change can be unsafe despite baseline safety.
- A mean-improving mixture can put a small mass of expensive fallback queries in the upper tail and worsen p95.

## G. Adaptive-certificate counterexample

Generate 20 candidate actions independently, compute unadjusted 95% certificates, and retain the one with the smallest observed risk. Even with independent candidate errors, post-selection family error is (1-.95^{20}>.05). Repeatedly viewing certification and modifying the family creates the same failure without an alpha-spending/anytime correction.

## H. Candidate attainability and cost counterexamples

- A selector can be mathematically correct conditional on its set while every generated candidate is unsafe; correctness is not attainability.
- Let stabilization reduce (D_C) but add operator cost exceeding all service savings. Then the stability objective improves while (D\le0) and no finite break-even exists.
- A track can pass on one dataset and violate the recall/p95 tolerance on another; a multi-dataset claim requires an intersection gate, not a pooled average.

