# Proof appendix: T-SC1–T-SC10

## A. Common model

Let `X` be fixed and `G_xi=A(X,xi)`. Queries follow `q ~ P_Q`. The ordered budget grid is `E={e_1<...<e_L}`. For target recall `tau`, define the safe set

\[
S_G(q)=\{e\in\mathcal E:R_G(q,e)\ge\tau\}.
\]

The principal positive results assume **upward closure**: if `e` is in `S_G(q)` and `e' >= e`, then `e'` is in `S_G(q)`. Define `B_G(q)=min S_G(q)` when nonempty and `B_G(q)=infinity` otherwise. Infinity represents endpoint infeasibility, not the maximum grid point. For right-censored observations, only the statement `B_G(q)>e_L` is licensed.

For a possibly randomized policy `pi(q,U)`, with auxiliary randomness `U`, absolute failure is

\[
Z_G(q,U;\pi)=\mathbf1\{B_G(q)=\infty\text{ or }\pi(q,U)<B_G(q)\},\qquad
r_G(\pi)=\Pr_{q,U}(Z_G=1).
\]

Let `ceil_E(x)=min{e in E:e>=x}`, equal to infinity when the set is empty.

## T-SC1 — canonicalization identity

**Statement.** If `X`, program, implementation version, hardware arithmetic semantics, scheduling, tie-breaking and every component of `xi` are fixed, and `A` is a deterministic total function, then repeated evaluation returns the same index.

**Proof.** A deterministic function maps the same input tuple to one output. Therefore `A(X,xi)=A(X,xi)` across repetitions. This says nothing about `A(X,xi')` for any changed component `xi'`. QED.

**Status:** `IDENTITY_OR_DEFINITION`. It removes declared randomness only and gives no open-world guarantee.

## T-SC2 — one-sided budget-coupling migration bound

Define the grid-shifted policy

\[
\pi^{(m)}_t(q,U)=\lceil \pi_s(q,U)+m\rceil_{\mathcal E}.
\]

Let

\[
A=\{\pi_s(q,U)<B_{G_s}(q)\},\quad
D_m=\{B_{G_t}(q)>\lceil B_{G_s}(q)+m\rceil_{\mathcal E}\}.
\]

The event `D_m` includes `B_Gt=infinity` and grid overflow. Assume upward closure on the target and `Pr(D_m)<=eta`.

**Theorem.**

\[
r_{G_t}(\pi_t^{(m)})\le r_{G_s}(\pi_s)+\eta.
\]

**Proof.** On `A^c intersect D_m^c`, `pi_s>=B_Gs`; monotonicity of `ceil_E` gives

\[
\pi_t^{(m)}\ge \lceil B_{G_s}+m\rceil_{\mathcal E}\ge B_{G_t}.
\]

Upward closure makes the target action safe. Hence target failure is contained in `A union D_m`. Apply the union bound and integrate over `(q,U)`. Independence between `U` and `q` is unnecessary if the joint law used in both risks is the same; a policy whose randomization changes adversarially across builds is outside the coupling. QED.

**Right censoring.** A censored source value cannot be substituted for `B_Gs`. Either exclude it under a declared estimand or count it in `A/D_m`. **Nonmonotone recall.** If a larger budget can lose a previously found neighbor, `pi>=B` does not imply safety; CE11 invalidates the theorem without upward closure.

**Status:** `RESTRICTED_DOMAIN_PROPOSITION`; the proof template is a classical event inclusion.

## T-SC3 — budget-to-cost transfer

Budget, NDC and wall time are distinct. Suppose a pathwise inequality is separately established:

\[
C_{G_t}(q,\pi_t^{(m)})-C_{G_s}(q,\pi_s)
\le K(q)\bigl(\pi_t^{(m)}-\pi_s\bigr)+H(q),
\]

where `K,H>=0` are integrable and include implementation/build effects. Then

\[
\mathbb E[C_t-C_s]\le \mathbb E[K\Delta_E(m)+H],
\]

with `Delta_E(m)=sup_e(ceil_E(e+m)-e)` on non-overflow actions. This is immediate by expectation monotonicity.

For NDC this inequality must be measured or proved for the implementation; `ef` or another budget parameter is not NDC. For wall time, queuing, caches and concurrency belong in `H`. For quantiles, the mean identity gives no bound. A valid generic tail inequality is, for `beta_1+beta_2=beta`,

\[
Q_{1-\beta}(X+Y)\le Q_{1-\beta_1}(X)+Q_{1-\beta_2}(Y),
\]

under the union bound, with no independence required. A pathwise constant `Y<=h` gives the simpler `Q_p(X+Y)<=Q_p(X)+h`. CE07/CE14 show mean improvement with worse tail.

**Status:** `RESTRICTED_DOMAIN_PROPOSITION`.

## T-SC4 — effective margin and fixed-target certification

Suppose a registered target policy has target risk bounded by `r_t<=r_s+eta` using T-SC2 or a valid surrogate-to-shift calibration. Let

\[
\gamma_{\rm eff}=\delta-r_s-\eta.
\]

If `gamma_eff<=0`, stability provides no positive margin and the stated concentration route has `NO_FINITE_MARGIN_BASED_CERTIFICATION_GAIN`. If `gamma_eff>0`, for `M` preregistered candidates and independent i.i.d. Bernoulli certification failures, Hoeffding plus Bonferroni gives a sufficient order

\[
n\ge {\log(M/\alpha)\over 2\gamma_{\rm eff}^2}.
\]

Exact binomial inversion should be used in deployment. The sharp large-deviation scale for distinguishing `delta-gamma_eff` from `delta` is

\[
n\asymp {\log(M/\alpha)\over \operatorname{kl}(\delta-\gamma_{\rm eff}\Vert\delta)}.
\]

If stable construction changes `eta_0` to `eta_1<eta_0` while all other terms remain fixed and both effective margins are positive, these sufficient sizes decrease monotonically. Statistical uncertainty is not replaced by structural error: `eta` is added before concentration.

**Status:** `CLASSICAL_APPLICATION` of binomial concentration/RCPS/LTT.

## T-SC5 — critical-path retention

### Disruption bound

For a query let a registered certificate contain at most `h` critical edges `E_q^*`. If every edge has marginal loss probability at most `rho`, then

\[
\Pr(E_q^*\not\subseteq E(G_t))\le\sum_{e\in E_q^*}\Pr(e\notin E(G_t))\le h\rho.
\]

No independence is required. Independence would permit `1-(1-rho)^h`, but is not assumed.

### Budget consequence under a robust trace certificate

Consider deterministic best-first/beam search with fixed entry, fixed distances and fixed tie-breaking. A source certificate consists of the ordered expanded nodes through the first safe discovery, all edges that first introduce those nodes, and their priority keys. Assume in the target:

1. certificate edges are retained;
2. no certificate node/target is deleted and distance keys are unchanged;
3. every new noncertificate node that can enter ahead of a certificate node is counted as a priority intruder;
4. at most `rho_j` intruders precede certificate step `j`, with total `s=sum_j rho_j`;
5. endpoint success is upward closed.

**Proposition.** `B_Gt(q)<=ceil_E(B_Gs(q)+s)` whenever the target grid can represent that value.

**Proof.** Induct on the source certificate steps. Retained introduction edges ensure each next certificate node enters the target frontier no later than after the corresponding predecessor is expanded. Fixed keys/ties preserve its order relative to other certificate nodes. Only registered intruders can delay it, and their total count is at most `s`. Thus the safe target is discovered within the source expansion count plus `s`. Grid rounding gives the claim. QED.

Combining with the disruption event gives

\[
\Pr[B_{G_t}(q)>\lceil B_{G_s}(q)+s\rceil_E]\le h\rho+\zeta,
\]

where `zeta` is the probability that any non-edge certificate premise fails. Path loss need not increase budget if alternatives exist, and path retention alone need not preserve top-k; therefore the general HNSW claim is forbidden.

**Status:** disruption bound `CLASSICAL_APPLICATION`; budget consequence `POTENTIAL_NEW_GRAPH_ANNS_RESULT` but restricted.

## T-SC6 — consensus-edge concentration

For `R` independent builds and a fixed candidate edge universe `F` of size `M`, let `X_{r,e}=1{e in G_r}`, `p_e=E X`, and `p_hat_e=R^{-1}sum_r X_{r,e}`. Hoeffding and a union bound imply

\[
\Pr\left(\max_{e\in F}|\widehat p_e-p_e|>\varepsilon\right)
\le 2M e^{-2R\varepsilon^2}.
\]

Therefore with probability `1-alpha`, uniform error is at most

\[
\sqrt{\log(2M/\alpha)/(2R)}.
\]

Edges may be dependent within a build; only build-level independence is used. Correct threshold classification requires a margin `|p_e-theta|>epsilon`. Degree truncation and connectivity repair change the selected graph after classification. A rare bridge can be estimated accurately and still be deliberately dropped. There is no implication for `d_B` without T-SC5/T-SC10 premises.

**Status:** `CLASSICAL_APPLICATION`.

## T-SC7 — response diameter and minimax migration tax

Fix one query and two feasible environments with safe budgets `b_0<b_1`, diameter `D=b_1-b_0`. Let action `a` incur

\[
\ell(a,b)=\lambda\mathbf1\{a<b\}+c(a-b)_+,
\]

and allow reject/fallback for cost `f`. For any non-rejecting action: if `a<b_1`, worst-case loss is at least `lambda`; if `a>=b_1`, loss under `b_0` is at least `cD`. Choosing just below `b_1` or at `b_1` attains the corresponding extremes on a dense grid. Hence the two-point minimax value is

\[
V(D)=\min\{f,\lambda,cD\}
\]

up to grid rounding. It is nondecreasing in `D`; contracting diameter can strictly lower the minimax value when `cD` is the active term. This explicitly captures under-budget risk, conservative tax and reject cost.

More generally, if a loss is `K`-Lipschitz in `b` and the action space admits a metric center, choosing a center gives at most `K Diam_B/2` plus grid radius; a two-point class with a matching lower-Lipschitz property gives at least `k Diam_B/2`. Rejection probability or certification acceptance does not follow from diameter alone; it additionally needs a calibrated statistical procedure and positive margin.

**Status:** `RESTRICTED_DOMAIN_PROPOSITION`.

## T-SC8 — build/service break-even

Let the stable method add per-build cost `Delta C_build`. Let per-query savings relative to the registered baseline be `g_search`, certification amortization saving `g_cert`, fallback saving `g_fb`, and added per-query control cost `C_control`, all in one monetary or latency-equivalent unit. For workload `N`, net value is

\[
V_N=N(g_{search}+g_{cert}+g_{fb}-C_{control})-\Delta C_{build}.
\]

If `g_net>0`, break-even is `N^*=Delta C_build/g_net`; if `g_net<=0`, label `NO_FINITE_BREAK_EVEN_WORKLOAD`. This is an accounting identity. Mean savings cannot establish p95 non-inferiority; the pilot has a separate tail Gate.

**Status:** `IDENTITY_OR_DEFINITION`.

## T-SC9 — counterexample theorem

The constructions CE01–CE16 in `counterexample_catalog.md` establish non-implications among edge overlap, local structure, determinism, recall, NDC, p95, endpoint feasibility and open-world safety. They are finite constructive disproofs, verified by the deterministic script.

**Status:** `COUNTEREXAMPLE_ONLY`.

## T-SC10 — impossibility and restricted structural surrogate

### General impossibility

Let `Phi` be edge Jaccard similarity, unweighted local-neighborhood overlap, or any metric that assigns vanishing distance when one of `M` edges changes. CE01 constructs graphs differing by one critical entry-to-target edge with `d_Phi=O(1/M)` while one budget is finite and the other can be arbitrarily large or infinite. Thus no universal finite constants `L,epsilon` with bounded `epsilon` can satisfy

\[
|B_G(q)-B_{G'}(q)|\le Ld_\Phi(G,G';q)+\epsilon
\]

over general directed search graphs. CE02 shows the reverse: low edge overlap can coexist with identical budget.

### Restricted sufficient surrogate

For the robust trace class of T-SC5, define

\[
d_\Phi(G,G';q)=I_{\rm cert}(q)+s(q),
\]

where `I_cert=1` if a certificate edge/node/key premise fails and `s` is the number of priority intruders. On the event `I_cert=0`, T-SC5 gives

\[
B_{G'}(q)-B_G(q)\le s(q)
\]

in expansion-count units, with grid rounding. If `I_cert=1`, the bound abstains rather than assigning a false finite value. Backup reachability can reduce `I_cert`: require `kappa` edge-disjoint certificate introductions with no more than `f<kappa` failures, but verifying disjointness alone still does not control frontier priority.

Observable on registered probes: search traces, entry point, frontier keys, edge retention, intruder count, backup reachability and empirical budget. Theoretical/not uniformly observable: uniqueness and margin for every future query, unchanged floating arithmetic, the future-build law, and population-wide certificate coverage. Therefore this is a calibratable pilot surrogate, not an unconditional deployment certificate.

**Status:** general part `COUNTEREXAMPLE_ONLY`; restricted part `POTENTIAL_NEW_GRAPH_ANNS_RESULT`.
