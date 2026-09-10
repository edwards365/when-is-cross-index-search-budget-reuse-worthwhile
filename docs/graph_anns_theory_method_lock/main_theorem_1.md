# Main Theorem I — Hidden-environment non-portability

## Statement

Let \(E_0,E_1\) be two build environments. Under environment \(E_i\), an admissible procedure observes a transcript \(T\sim P_i^T\) and outputs an action according to a randomized Markov kernel \(A(\cdot\mid T)\). Let \(D_i\) be the decision region that is nontrivially acceptable in environment \(E_i\), and assume \(D_0\cap D_1=\varnothing\). Let \(\ell_i(a)\ge 0\) be a Graph-ANNS deployment loss and suppose

\[
\ell_i(a)\ge \Delta\,\mathbf 1\{a\notin D_i\},\qquad \Delta>0.
\]

Then every transcript-based procedure satisfies

\[
\max_{i\in\{0,1\}}\mathbb E_i[\ell_i(A(T))]
\ge
\frac{\Delta}{2}\left(1-\operatorname{TV}(P_0^T,P_1^T)\right).
\]

Consequently, if the transcript does not identify which conflicting safe-action region applies, an environment-blind policy cannot uniformly avoid the domain-specific loss assigned to unsafe under-budgeting, conservative computation, fallback, or abstention.

For an adaptive transcript \(T_m=(H_{m-1},A_m,Y_m)_{m=1}^m\), let

\[
K_m=\operatorname{KL}(P_0^{T_m}\Vert P_1^{T_m}).
\]

The same decision reduction gives the classical consequences

\[
\max_i\mathbb E_i[\ell_i]
\ge \frac{\Delta}{4}e^{-K_m},
\qquad
\max_i\mathbb E_i[\ell_i]
\ge \frac{\Delta}{2}\max\!\left\{0,1-\sqrt{K_m/2}\right\}.
\]

If every observation contributes conditional KL at most \(I_\star\), then \(K_m\le mI_\star\). Any procedure that identifies the correct region with error at most \(\beta<1/2\) in both environments must therefore acquire information on the order required by the binary-testing inequality

\[
mI_\star\ge \operatorname{kl}(1-\beta,\beta).
\]

## Ordered-budget corollary

When conflicting regions encode “small enough to avoid conservative/fallback cost in \(E_0\)” and “large enough to avoid under-budget failure in \(E_1\),” the theorem yields an explicit risk–conservatism–abstention trade-off. This is a Graph-ANNS loss instantiation of classical two-point testing, not a new general Le Cam theorem.

## Assumptions and scope

- The result quantifies over all randomized rules measurable with respect to the stated transcript.
- Disjointness concerns nontrivially acceptable decision regions, not necessarily all statistically safe actions.
- The lower bound applies to a declared pair or finite registered class through pairwise witnesses.
- It does not assert that every pair of builds is indistinguishable, nor that open-world recovery is universally impossible.
- Le Cam, total-variation testing, Bretagnolle–Huber, Pinsker, and adaptive KL chain rules are classical. The contribution is their explicit connection to build-conditioned Graph-ANNS safety, conservative cost, fallback, and abstention.
