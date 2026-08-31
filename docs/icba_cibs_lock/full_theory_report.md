# CIBS-Fixed theory report

## 1. Model and estimand

On one fixed dataset and target query distribution (P_Q), preregister (K) builds \(\mathcal G=\{G_1,\ldots,G_K\}\) and (L) raw fixed-budget values \(\mathcal E=\{e_1<\cdots<e_L\}\). The finite deployment family is

\[
\mathcal A=\mathcal G\times\mathcal E,\qquad M=KL.
\]

Each action (a=(G_k,e_\ell)) means deploying exactly one serialized build with exactly one global fixed-`ef`. For independent target queries (q_i\sim P_Q), the shared full-information observation is

\[
O_i=\{Z_i(a),C_i(a):a\in\mathcal A\},
\]

where

\[
Z_i(a)=\mathbf 1\{\operatorname{Recall@10}(G_k,q_i,e_\ell)<\tau\}.
\]

Endpoint-infeasible or right-censored observations are failures unless a separate abstention action was preregistered. Risk and primary cost are

\[
r(a)=\Pr_{q\sim P_Q}\{Z(a)=1\},\qquad C(a)=\mathbb E[\operatorname{NDC}(a)].
\]

Mean NDC is the primary objective. p95/p99 NDC are separate constraints/descriptive endpoints, never inferred from a mean bound. One exact truth may be shared across actions, while every action-specific search is still charged.

## 2. T-CIBS1 — fixed-family simultaneous safe selection

**Statement.** Suppose random upper bounds (U_r(a)) satisfy

\[
\Pr\{\forall a\in\mathcal A:r(a)\le U_r(a)\}\ge 1-\alpha.
\]

Let \(\widehat{\mathcal S}=\{a:U_r(a)\le\delta\}\). If nonempty, let \(\widehat a\) be any sentinel-data-measurable element of \(\widehat{\mathcal S}\). Then

\[
\Pr\{r(\widehat a)\le\delta\}\ge1-\alpha.
\]

**Proof.** On the simultaneous coverage event, \(r(\widehat a)\le U_r(\widehat a)\le\delta\). Its probability is at least \(1-\alpha\). No independence across actions is used. Data-dependent minimization of observed cost inside \(\widehat{\mathcal S}\) therefore preserves safety. Query units must satisfy the sampling assumptions of the bounds, and the candidate family must be frozen before seeing responses. If the set is empty, the procedure returns a separately justified fixed-safe fallback; it does not label any candidate safe. **Status:** `FORMAL_PROOF_COMPLETE`; **novelty:** `CLASSICAL_APPLICATION`.

## 3. T-CIBS2 — Bonferroni exact-binomial instance

For action (a), let (X_a=\sum_{i=1}^n Z_i(a)). Assign \(\alpha_a=\alpha/M\) and use the one-sided exact Clopper–Pearson endpoint

\[
U_a=\operatorname{Beta}^{-1}(1-\alpha/M;X_a+1,n-X_a),
\]

with (U_a=1) at (X_a=n). Each marginal noncoverage probability is at most \(\alpha/M\), hence the union bound supplies T-CIBS1 without assuming action independence.

At \(\alpha=\delta=.05\):

| K | L | n | M | maximum failures with (U_a\le.05) | zero-failure UCB | minimum n for zero-failure certification |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 12 | 256 | 36 | 3 | 0.0253727610 | 129 |
| 2 | 12 | 128 | 24 | 0 | 0.0470879851 | 121 |
| 3 | 12 | 250 | 36 | 3 | 0.0259737304 | 129 |

The exact zero-failure threshold is

\[
n_{\min}=\left\lceil\frac{\log(\alpha/M)}{\log(1-\delta)}\right\rceil.
\]

**Status:** `FORMAL_PROOF_COMPLETE`; **novelty:** `CLASSICAL_APPLICATION`.

## 4. T-CIBS3 — restricted cost near-optimality

Let \(\widehat C(a)\) estimate mean NDC and suppose the simultaneous event

\[
\mathcal E_C=\{\forall a:|\widehat C(a)-C(a)|\le\eta_a\}
\]

holds. Define \(a^*_{\widehat S}\in\arg\min_{a\in\widehat{\mathcal S}}C(a)\) and let \(\widehat a\in\arg\min_{a\in\widehat{\mathcal S}}\widehat C(a)\). On \(\mathcal E_C\),

\[
C(\widehat a)\le C(a^*_{\widehat S})+\eta_{\widehat a}+\eta_{a^*_{\widehat S}}\le C(a^*_{\widehat S})+2\eta_{\max}.
\]

Comparison with the ideal \(a^*=\arg\min_{r(a)\le\delta}C(a)\) additionally requires the power event \(a^*\in\widehat{\mathcal S}\). True safety alone does not ensure certification, especially near the boundary. Safety of \(\widehat a\) does not require any cost interval. Evaluation queries remain independent and never affect selection. p95 needs its own inference. **Status:** `FORMAL_PROOF_RESTRICTED`; **novelty:** `CLASSICAL_APPLICATION`.

## 5. T-CIBS4 — paired full-information variance

For two actions on the same query, \(D_i(a,b)=C_i(a)-C_i(b)\), and

\[
\operatorname{Var}D=\operatorname{Var}C(a)+\operatorname{Var}C(b)-2\operatorname{Cov}(C(a),C(b)).
\]

Positive covariance can reduce comparison variance relative to independent samples; negative covariance can increase it. Shared truth is not free search: each evaluated action incurs search cost. Action correlation is irrelevant to Bonferroni validity but material to power and cost estimation. **Status:** `CLASSICAL_APPLICATION`; **novelty:** `CLASSICAL_APPLICATION`.

## 6. T-CIBS5 — build-service break-even

Let

\[
\Delta C_{\rm offline}=(K-1)C_{\rm build}+C_{\rm truth}+C_{\rm candidate\ search}+C_{\rm selection}+C_{\rm certification}
\]

and per-query mean saving \(g=C_{\rm single}-C_{\rm CIBS}\). The cumulative difference after (N) served queries is \(\Delta C_{\rm offline}-Ng\). Therefore if (g>0), break-even is

\[
N^*=\Delta C_{\rm offline}/g,
\]

with integer deployment requiring \(\lceil N^*\rceil\). If (g\le0), report `NO_FINITE_BREAK_EVEN_WORKLOAD`.

When exact truth already exists and is legitimately reusable, its incremental cost is zero; otherwise generation is charged. Reusable builds are amortized over the declared services; one-shot builds are charged in full. The identity is about the chosen cost unit and does not imply p95 improvement. **Status:** `FORMAL_PROOF_COMPLETE`; **novelty:** `CLASSICAL_APPLICATION`.

## 7. T-CIBS6 — fixed-candidate identification lower bound

Consider two actions whose per-query joint observation law is (P_0) in one instance and (P_1) in a swapped instance, with risk means \(\delta-\gamma\) and \(\delta+\gamma\). Any procedure choosing the correct safe action with error at most \(\beta\) induces a test between (P_0^n) and (P_1^n). Bretagnolle–Huber yields

\[
2\beta\ge\tfrac12\exp[-n\operatorname{KL}(P_0\|P_1)],
\quad
n\ge\frac{\log(1/(4\beta))}{\operatorname{KL}(P_0\|P_1)}.
\]

For Bernoulli risks separated by (2\gamma), the denominator is \(\Theta(\gamma^2/[\delta(1-\delta)])\) away from 0 and 1, giving \(\Omega(\gamma^{-2}\log(1/\beta))\). Distinguishing sub-Gaussian mean costs separated by \(\Delta_C\) likewise needs \(\Omega(\sigma^2\Delta_C^{-2}\log(1/\beta))\). Full information changes the joint KL but does not eliminate the query-sample lower bound. **Status:** `FORMAL_PROOF_RESTRICTED`; **novelty:** `CLASSICAL_APPLICATION`.

## 8. T-CIBS7 — fixed-target/open-world boundary

CIBS-Fixed certifies one named action from one preregistered portfolio under the current (P_Q). Construct a second build distribution identical on every observed named build but assigning failure probability one to the next unseen build. The fixed-target data laws are identical, yet the unseen-build claim is false. Similarly, an arbitrary shifted query distribution can concentrate on failed queries. Thus no fixed-target certificate implies next-rebuild, unseen insertion order, query shift, another implementation, or open-world safety.

An outer-build claim needs an explicit build-generating distribution, independent portfolio/build units, and a hierarchical/outer-level procedure. **Status:** `FORMAL_PROOF_COMPLETE`; **novelty:** `RESTRICTED_DOMAIN_PROPOSITION`.

## 9. Gate disposition

Gates L, T, S, P, D, N and E pass at the theory-contract level. They authorize a Stage-I CIBS-Fixed pilot only. They do not establish NDC/p95 gains, net deployment value, or open-world rebuild portability.

