# Proof appendix and adversarial audit

## A. Measurability and simultaneous selection

The selection rule may use the entire sentinel matrix \(\{Z_i(a),C_i(a)\}_{i,a}\), including correlated observations across actions. The only inclusion used in T-CIBS1 is

\[
\{\forall a:r(a)\le U_a\}\subseteq\{r(\widehat a)\le\delta\}
\]

whenever \(\widehat a\in\{a:U_a\le\delta\}\). This remains true for arbitrary measurable tie-breaking. A candidate generated after inspecting the same observations is outside the indexed simultaneous event and invalidates the proof unless the inference was uniform over the generation space.

## B. Exact-binomial calculation

For (0\le x<n), the one-sided upper endpoint (u) solves

\[
\Pr_{Y\sim\operatorname{Bin}(n,u)}(Y\le x)=\alpha/M.
\]

Equivalently, \(u=\operatorname{Beta}^{-1}(1-\alpha/M;x+1,n-x)\). Exhaustive integer enumeration gives:

- (K=3,L=12,n=256): (U(3)=0.0484701181\le.05), while (U(4)=0.0549482108>.05).
- (K=2,L=12,n=128): (U(0)=0.0470879851\le.05), while (U(1)=0.0638799000>.05).
- if only 250 frozen sentinel queries exist: (U(3)=0.0496109868\le.05), while (U(4)=0.0562271340>.05).

Zero failures gives (U(0)=1-(\alpha/M)^{1/n}\), hence the stated exact minimum sample size.

## C. Cost-regret proof

On \(\mathcal E_C\),

\[
C(\widehat a)\le\widehat C(\widehat a)+\eta_{\widehat a}
\le\widehat C(a^*_{\widehat S})+\eta_{\widehat a}
\le C(a^*_{\widehat S})+\eta_{a^*_{\widehat S}}+\eta_{\widehat a}.
\]

There is no unconditional regret bound to the ideal safe action because a safe action can be rejected with high probability when (r(a)\) is arbitrarily close to \(\delta\). A uniform cost confidence interval also needs a bounded, sub-Gaussian, empirical-Bernstein, or otherwise stated tail assumption; CIBS does not silently assume one.

## D. Pairing boundary

The covariance identity follows by bilinearity. An exact witness against unconditional paired dominance uses variances one and covariance \(-1/2\), giving paired variance 3 versus independent-sample difference variance 2. Positive covariance is an empirical efficiency opportunity, not a theorem assumption for safety.

## E. Lower-bound reduction

Let \(\phi\) indicate which of two swapped instances is present. If CIBS chooses the uniquely safe/cheaper action with probability at least \(1-\beta\) in both instances, \(\phi\) has summed error at most \(2\beta\). Bretagnolle–Huber gives summed error at least \(\tfrac12e^{-n\mathrm{KL}(P_0\|P_1)}\). Rearrangement proves the stated necessary condition. This is a specialization of classical testing/BAI, not a new lower-bound technique.

## F. Endpoint semantics

If the largest measured budget fails to reach \(\tau\), replacing the observation by “success at max `ef`” changes (Z=1) to (Z=0) and can make an unsafe action certifiable. The absolute event therefore includes endpoint infeasibility. Right-censoring is not evidence of success. A distinct abstention action is legal only if its safety and cost are specified before observation.

## G. Tail limitation

Mean improvement cannot control p95. For example, action A costs zero on 94% of queries and 100 on 6%, while B always costs 7. A has mean 6, below B's 7, but its nearest-rank p95 is 100 versus 7. The pilot therefore applies an independent p95 non-inferiority gate.

## H. Fixed-target countermodel

Let all observations for the named portfolio equal zero failure under two worlds. In world 0 every future build is safe; in world 1 the next build fails surely. The likelihood of current data is identical. No rule using only current named-build observations can distinguish the worlds, so any claimed next-build guarantee lacks an identifying assumption.
