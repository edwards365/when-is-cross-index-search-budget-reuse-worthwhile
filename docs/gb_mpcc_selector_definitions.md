# Frozen R0 selector definitions

These definitions were committed before R0 selector outputs were generated. Every
selector receives the same logged layer-zero candidate pool and the same budget,
equal to the number accepted by the recorded Algorithm 4 event (at most 16).

- **Algorithm4**: the recorded accepted candidates, whose replay is already checked
  against the original hnswlib insertion.
- **Geometry**: the project's frozen geometry selector with `alpha=0`, `beta=1`,
  `gamma=1`, `sigma=0.5`, and median center–candidate distance scale.
- **MaxMin-Angle**: choose the shortest candidate first; subsequently minimize the
  maximum cosine with already selected directions. Ties prefer shorter edges then
  smaller external labels.
- **LengthAware-Angle**: choose the shortest candidate first; subsequently minimize
  the largest positive Algorithm-4 occlusion margin
  `cos(d_v,d_w) - s_w/(2 s_v)` over already selected `w`. Ties prefer shorter edges
  then smaller external labels. Unlike Algorithm 4, it fills the common budget.
- **GGR-0**: the frozen epsilon-zero geometry-guarded exchange. Scheme-A leverage is
  computed on the logged post-insertion local induced graph plus the complete
  center–candidate star, using one frozen Gaussian scale.
- **Geometry-Safe-Random**: the existing no-query random control, with requested swap
  count matched to GGR-0 and deterministic event seed.
- **MPCC-Shuffled**: permute candidate identities attached to frozen coverage masks,
  then run the unchanged coverage greedy rule with an event-deterministic seed.
  The selected row positions are the candidate identities; they must not be mapped
  back through the permutation, which would cancel this negative control.
- **Pure-MPCC**: greedily maximize hard empirical-direction multi-scale union
  coverage under the common budget.
- **Geometry-Backbone-MPCC**: retain the first `min(12,budget)` recorded Algorithm 4
  candidates and fill remaining slots by maximum marginal empirical-direction
  coverage. The production claim concerns this version; Pure-MPCC is only a
  distinguishability upper diagnostic.
- **Geometry-Backbone-Random**: retain exactly the same Algorithm 4 backbone and
  fill exactly the same number of flexible slots by uniform sampling without
  replacement.
- **Geometry-Backbone-MPCC-Shuffled**: retain exactly the same Algorithm 4
  backbone and flexible-slot budget, but randomly permute candidate identities
  attached to empirical coverage masks before greedy filling.

The earlier Pure-MPCC-Shuffled and Geometry-Safe-Random selectors remain useful
diagnostics but are not budget-matched controls for GB-MPCC.

All greedy ties are deterministic. State samples, local scale, radii, and seeds are
those frozen in `preregistration/gb_mpcc_r0.yaml`. Isotropic-Sphere remains a negative
reference and cannot become the primary selector.
