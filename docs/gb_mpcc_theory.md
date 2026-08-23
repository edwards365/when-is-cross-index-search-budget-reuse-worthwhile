# GB-MPCC theory gate T0

Status: mathematical specification and executable checks; no global HNSW performance
claim. All construction distributions are frozen before local selection and use only
base/train geometry.

## 1. Exact one-step Euclidean progress

Fix current point (u), candidate (v), and query (q\ne u). Write

\[
r=\|q-u\|,  s=\|v-u\|, 
\omega=(q-u)/r,  d=(v-u)/s.
\]

The polarization identity gives

\[
\|q-v\|^2=r^2+s^2-2rs\langle\omega,d\rangle.
\]

Consequently,

\[
\|q-v\|<r
\iff s^2-2rs\langle\omega,d\rangle<0
\iff \boxed{\langle\omega,d\rangle>s/(2r)}.
\]

Thus the strict-progress set at radius (r) is an open spherical cap. If
(s/(2r)\ge1), it is empty (at equality the strict inequality still excludes the
single aligned boundary direction). Longer edges can therefore be useless at a
near scale even when their direction is favorable.

For (0\le\eta<1), squaring the nonnegative inequality
(\|q-v\|\le(1-\eta)r) and rearranging yields

\[
2rs\langle\omega,d\rangle
\ge s^2+(2\eta-\eta^2)r^2,
\]

or

\[
\boxed{\langle\omega,d\rangle\ge
  s/(2r)+(2\eta-\eta^2)r/(2s)}.
\]

A threshold greater than one denotes an empty cap. If every chosen step while
outside radius (r_{\min}) actually satisfies the multiplicative condition, then
(r_t\le(1-\eta)^t r_0); hence crossing (r_{\min}) requires no more than

\[
\left\lceil\log(r_0/r_{\min})/[-\log(1-\eta)]\right\rceil
\]

such chosen steps. Existence of an edge is insufficient: this statement assumes the
search chooses it. It is not a beam-search Recall or complexity theorem.

## 2. Beam admission diagnostic

Let the current result boundary be (B=br), and put (\lambda=s/r>0). Dividing
(\|q-v\|^2<B^2) by (r^2) gives

\[
1+\lambda^2-2\lambda\langle\omega,d\rangle<b^2,
\]

therefore

\[
\boxed{\langle\omega,d\rangle>
  (1+\lambda^2-b^2)/(2\lambda)}.
\]

The runtime boundary (b) is allowed only as a development-trace diagnostic. It is
not a construction input because no frozen query-independent model for its
conditional distribution has yet been justified.

## 3. Algorithm 4 is already length-aware angle diversity

Algorithm 4 processes candidates by nondecreasing center distance. Suppose already
selected (w) has (s_w=\|w-u\|\le s_v=\|v-u\|), and let (\phi) be the angle
between their displacement vectors. Its occlusion event (\|v-w\|<s_v) obeys

\[
s_v^2+s_w^2-2s_vs_w\cos\phi<s_v^2
\iff \boxed{\cos\phi>s_w/(2s_v)}.
\]

At equal lengths this is (\phi<60^\circ). GB-MPCC must therefore demonstrate
selection Jaccard below the preregistered 0.95 equivalence threshold and incremental
coverage not explained by matched edge-length/angle distributions. Merely renaming
this occlusion rule as a cone is not a new mechanism.

## 4. Frozen hard coverage and submodularity

For center (u), freeze candidate pool (C_u), scale (\ell_u>0), and a probability
measure (\mu_u) over states (z=(\omega,\rho)) before selecting any edge. Define

\[
a_v(z)=\mathbf1[\langle\omega,d_v\rangle>
  \tilde s_v/(2\rho)],\qquad \tilde s_v=s_v/\ell_u,
\]

and (A_v=\{z:a_v(z)=1\}). Then

\[
F_u(S)=\mu_u(\cup_{v\in S}A_v).
\]

Normalization follows from an empty union. If (S\subseteq T), their unions are
nested, proving monotonicity. For (x\notin T),

\[
F(S\cup\{x\})-F(S)=\mu(A_x\setminus A_S)
\ge\mu(A_x\setminus A_T)
=F(T\cup\{x\})-F(T),
\]

which is diminishing returns and hence submodularity. Replacing the measure with
weighted Monte Carlo atoms gives the identical proof.

Let a frozen mandatory geometry backbone be (B_u), and define

\[
H_u(A)=F_u(B_u\cup A)-F_u(B_u).
\]

Subtracting a constant preserves diminishing returns, and contraction by fixed
(B_u) preserves normalization and monotonicity. Under only
(|A|\le R), standard greedy marginal maximization therefore satisfies
(H(A_g)\ge(1-1/e)\max_{|A|\le R}H(A)). This guarantee does not apply to an
arbitrary non-downward-closed geometry floor or to the later reciprocal/pruning
dynamics.

## 5. Smooth coverage

For margin

\[
m_v(\omega,\rho)=\langle\omega,d_v\rangle-
\tilde s_v/(2\rho),
\]

let (\psi_\tau(m)=0) for (m\le0), (m/\tau) for (0<m<\tau), and (1) for
(m\ge\tau). Define

\[
f_S^\tau(z)=\max_{v\in S}\psi_\tau(m_v(z)),\qquad
F_\mu^\tau(S)=\mathbb E_\mu f_S^\tau.
\]

For fixed (z), a maximum of fixed nonnegative singleton scores is normalized,
monotone, and submodular: adding (x) improves the maximum by
(\max(0,a_x-\max_{v\in S}a_v)), which decreases as (S) grows. Nonnegative
expectation preserves all three properties.

## 6. Proxy-distribution mismatch

For hard coverage event (A_S) and true routing distribution (\nu_u), the adopted
definition (\|\nu-\mu\|_{TV}=\sup_A|\nu(A)-\mu(A)|) immediately gives

\[
\boxed{|F_\nu(S)-F_\mu(S)|\le\|\nu-\mu\|_{TV}}.
\]

For the smooth objective, assume (\rho\ge\rho_{\min}>0) and
(\tilde s_v\le s_{\max}). With
(d_Z(z,z')=\|\omega-\omega'\|_2+|\rho-\rho'|),

\[
|m_v(z)-m_v(z')|
\le\|\omega-\omega'\|_2+
  {s_{\max}\over2\rho_{\min}^2}|\rho-\rho'|.
\]

The clipped ramp is (1/\tau)-Lipschitz and the maximum of functions sharing a
Lipschitz bound retains that bound. Thus

\[
L_\tau\le{1\over\tau}\max\{1,s_{\max}/(2\rho_{\min}^2)\}.
\]

Kantorovich–Rubinstein duality, assuming finite first moments, then yields

\[
\boxed{|\mathbb E_\nu f_S^\tau-\mathbb E_\mu f_S^\tau|
\le L_\tau W_1(\nu,\mu)}.
\]

Both bounds concern proxy coverage only. Neither controls HNSW Recall, NDC, or
latency without additional links in the mechanism chain.

## 7. Monte Carlo error and adaptive selection

For fixed (S), independent Bernoulli coverage samples give Hoeffding's inequality

\[
\Pr(|\widehat F(S)-F(S)|>\epsilon)\le2e^{-2L\epsilon^2}.
\]

For (K) fixed simultaneous claims, a union bound permits

\[
\epsilon=\sqrt{\log(2K/\delta)/(2L)}.
\]

This is not automatically uniform over data-adaptive greedy sequences. T0 reports
the number (K) of evaluated fixed claims; later adaptive validation uses fresh
frozen states or a separately justified uniform bound.

## 8. High-dimensional spherical-cap capacity

If (\omega) is uniform on (S^{d-1}) and (t\in[0,1]), rotational symmetry and
the beta law of the first squared coordinate give

\[
p_d(t)=\Pr(\langle\omega,e_1\rangle>t)
=\tfrac12 I_{1-t^2}((d-1)/2,1/2).
\]

For a set of at most (M) edges, Boole's inequality gives

\[
F(S)\le\min\{1,\sum_{v\in S}p_d(t_v)\}
\le\min\{1,M\max_v p_d(t_v)\}.
\]

The capacity audit must compare this analytic upper bound with Monte Carlo union
coverage at preregistered scales. An isotropic median upper bound below 0.05 is the
frozen degeneracy stop for that model, not evidence that empirical directions are
also degenerate.

## 9. Metric boundary

Unit-normalized cosine ranking is equivalent to squared Euclidean ranking because
(\|x-y\|^2=2-2x^Ty). Unnormalized MIPS instead has progress event
(q^Tv>q^Tu\iff q^T(v-u)>0); the Euclidean length/radius cap formula is not used for
unnormalized MIPS.

Executable randomized equivalence tests and exhaustive small-set submodularity tests
are under `tests/navigation_coverage/`. Passing them establishes algebraic and
implementation consistency only.
