# Restricted recovery theory

Evidence label: `THEORETICAL`. These statements instantiate standard one-sided calibration ideas for the frozen Graph-ANNS budget grid; they are not claimed as new generic calibration theory.

## R1 — residual-certificate validity (`RESTRICTED_PROPOSITION`)

Fix a target build and an ordered budget grid. Let the deployable source policy return an index \(\hat b(q)\), and define the target residual \(D(q)=B(q)-\hat b(q)\), where \(B(q)\) is the minimum safe grid index. Assume the labelled sentinel residuals and the future evaluation residual are exchangeable, and that larger grid indices cannot turn a safe query unsafe. If \(\hat d\) is the preregistered one-sided order-statistic upper bound with miscoverage at most \(\delta_q\), then \(U(q)=\min\{\hat b(q)+\hat d,b_{\max}\}\) satisfies

\[
\Pr\{B(q)>U(q)\}\leq\delta_q.
\]

Proof: failure is exactly \(D(q)>\hat d\). Exchangeability makes the rank of the future residual among the sentinel residuals and itself uniform (with conservative handling of ties); choosing the corresponding upper order statistic bounds this event by \(\delta_q\). Clipping at the maximum grid value preserves safety only when that endpoint is certified; otherwise the method must abstain. The empirical implementation additionally reports a one-sided Clopper–Pearson upper bound and passes Gate S only when that bound is at most 0.05. This is a finite-target-build statement and is not an outer-build guarantee.

## R2 — support-gated recovery (`RESTRICTED_PROPOSITION`)

Fix a fingerprint metric, coverage radius, donor rule, residual envelope, and fallback before reading target evaluation outcomes. Suppose (i) an accepted target lies inside the historical support radius, (ii) its conditional residual tail is dominated by the preregistered donor envelope up to error \(\varepsilon_{\rm stab}\), and (iii) the target sentinel certificate has error \(\varepsilon_{\rm sent}\). Then the accepted-query under-budget risk is at most

\[
\delta_q+\varepsilon_{\rm stab}+\varepsilon_{\rm sent}.
\]

Outside support, or when the certificate fails, returning the independently certified fixed-safe endpoint has its inherited fixed-endpoint risk bound. Total cost decomposes into online search, fingerprint/probe collection, truth acquisition, donor computation, certification, and refusal/fallback cost.

Proof: on accepted targets, apply the donor domination assumption and a union bound with the finite-sentinel certificate. On rejected targets, safety is inherited from the fallback rather than from transfer. The result does not establish the stability assumption from nine builds and therefore does not certify open-world outer risk.

## Gate interpretation

R1 supports M1 under its stated exchangeability and certified-endpoint conditions. R2 is conditional; the current nine-build design evidence cannot establish the required local stability or a 5% outer-build guarantee. A future matching theorem would need joint dependence on the number of environments \(m\), queries \(n\), target probes \(k\), budget levels \(M\), residual separation \(\Delta\), and fingerprint covering number \(\mathcal N(\epsilon)\).
