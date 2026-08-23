# GB-MPCC Theory Gate T0 decision

Decision: **PASS_TO_REPLAY_R0**. This authorizes offline candidate replay only. It
does not authorize 10K graph construction, 100K performance experiments, or formal
test access.

## Evidence against the frozen criteria

| Criterion | Result | Evidence |
| --- | --- | --- |
| Exact strict/multiplicative progress, beam admission, and Algorithm 4 equivalence | PASS | Random numerical equivalence tests in `tests/navigation_coverage/test_progress_conditions.py` |
| Hard/smooth coverage normalization, monotonicity, and submodularity | PASS | Exhaustive small-set checks and frozen-backbone greedy check in `test_coverage_objective.py` |
| Proxy mismatch and Monte Carlo bounds are stated without Recall claims | PASS | `docs/gb_mpcc_theory.md` |
| Query-independent capacity non-degenerate on at least two datasets | PASS | Empirical-direction coverage is non-degenerate on GloVe and Arxiv under the frozen 0.05–0.95 rule |
| Objective measurably differs from Algorithm 4 | PASS FOR PROXY POOL | Equal-budget pure-objective median Jaccard is 0.3333, 0.3333, and 0.2899 on SIFT, GloVe, and Arxiv; median coverage gain is +0.0132, +0.0208, and +0.0190 |
| No identical published objective/constraint/build stage found | PROVISIONAL PASS | `docs/novelty_matrix.md`; high-threat adjacent work is explicitly retained |

All T0 numerical work read only `train[:100000]`; metadata records
`formal_test_members_accessed=false`. The 16 new theory tests, 75 existing Python
tests, and three native smoke executables pass on the server.

## Required negative findings

Ambient `ISOTROPIC-SPHERE` is degenerate at the near scale on SIFT and GloVe and at
all three scales on 768-dimensional Arxiv under the preregistered analytic 0.05
threshold. It is frozen as a theoretical/negative reference and cannot be selected
as the primary state model. Exact-kNN proxy candidates also make empirical coverage
saturate at medium/far scales; R0 must determine whether real insertion candidate
pools retain discriminatory coverage.

The overlap audit compares a pure MPCC objective with Algorithm 4 on an exact-32-NN
proxy pool. It proves only that the objectives can select different equal-budget
sets. It does not establish that the frozen 12+4 geometry-backbone selector differs
on real insertion candidates, survives reciprocal pruning, or improves navigation.

## R0 authorization and stop rule

R0 may now use existing or newly regenerated construction-only HNSW candidate logs
from `train` to compare Algorithm 4, Geometry, MaxMin-Angle, LengthAware-Angle,
GGR-0, random/shuffled controls, and the three frozen MPCC state models. Development
queries may label mechanism diagnostics but cannot change candidates, states, scores,
or construction parameters.

If real-candidate GB-MPCC has Jaccard above 0.95 without incremental coverage, or
does not beat LengthAware-Angle/Algorithm 4 on the preregistered mechanism criteria,
the performance-algorithm branch stops with
`MECHANISM_EQUIVALENT_TO_GEOMETRY` or `PERFORMANCE_NOT_ESTABLISHED` as applicable.
