# Euclidean progress cones and query-independent direction coverage

## Exact progress condition

Let the current point be `u`, candidate neighbor be `v`, query be `q`, and
`Delta=v-u`. Direct expansion gives

`||u-q||^2 - ||v-q||^2 = 2 <q-u, Delta> - ||Delta||^2`.

Therefore `v` is strictly closer to `q` than `u` if and only if

`2 <q-u, Delta> > ||Delta||^2`.

For `q != u` and `v != u`, write `omega=(q-u)/||q-u||` and
`Delta_hat=Delta/||Delta||`. At query radius `r=||q-u||`, this becomes

`<omega, Delta_hat> > ||Delta||/(2r)`.

Thus an edge covers the open spherical cap

`Omega_e(r)={omega in S^(d-1): <omega,Delta_hat_e> > ||Delta_e||/(2r)}`.

The cap is empty when `||Delta_e|| >= 2r` (apart from an unattainable strict boundary
at equality). This exposes a fact omitted by direction-only diversity: edge length and
query radius change whether a direction can produce progress at all.

## Discrete weighted coverage

Choose directions `omega_j` and nonnegative weights `a_j` using only construction or
development information. Define `A_e={j: omega_j in Omega_e(r)}` and

`F_cap(S)=sum_j a_j 1[j in union_(e in S) A_e]`.

This is normalized and monotone. For `A subset B` and edge `e`, its marginal is the
weight of `A_e` not already covered. Since the uncovered indices under `B` are a
subset of those under `A`, the marginal under `A` is no smaller. Hence the discrete
objective is submodular. This is a project rederivation of the standard weighted-
coverage argument.

For iid directions from a fixed query-independent distribution `mu` and weights
`1/n`, the estimator is an average of Bernoulli variables. For any fixed set `S`,
Hoeffding gives

`P(|F_hat(S)-F(S)| >= t) <= 2 exp(-2 n t^2)`.

Uniform control over a finite family `H` follows by a union bound with error at most
`sqrt(log(2|H|/delta)/(2n))`. This does not provide a dimension-free guarantee over
an unrestricted continuum of caps or adaptively test-selected distributions.

## Relation to the frozen log-det Geometry objective

Log-det direction diversity and cap coverage are neither equivalent nor ordered in
general. Log-det rewards linearly diverse unit directions and is insensitive to edge
length after normalization; cap coverage depends on length/radius and can saturate
when several directions cover the same mass. Conversely, finite sampled caps can miss
a direction that still improves log-det. The existing Geometry objective is therefore
a defensible query-independent diversity surrogate, but not an estimator of cap
coverage.

Phase II does not add a cap-based main algorithm. Doing so would introduce radius,
sampling-distribution, and sample-count choices before the simpler Geometry-guarded
hypothesis is tested. Cap coverage remains a theoretical diagnostic or future
pre-registered alternative.

## Boundary

The identity proves one-step Euclidean progress only. It does not prove reachability,
beam survival, HNSW layer transitions, reciprocal pruning behavior, or final Recall.
