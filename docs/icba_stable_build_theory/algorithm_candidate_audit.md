# Algorithm candidate audit

## Route comparison

The numerical scorecard is in `algorithm_candidate_scorecard.csv`; higher scores are better after risk/cost columns are direction-normalized. Ranking follows the task’s lexicographic Gates, not a simple total.

### A. Canonical deterministic construction

Replays the same build given a fully fixed environment. Lowest complexity and a necessary baseline, but novelty and open-world potential are minimal. It cannot address updates, version changes or unobserved order changes. **Disposition:** baseline only.

### B. Consensus-Stabilized Construction

Builds `R` shadows, estimates edge persistence, protects registered bridges, and repairs degree/connectivity. T-SC6 makes the estimator auditable, but consensus can stabilize the wrong edges and delete rare critical ones. **Disposition:** fallback route.

### C. Critical-Path Stabilized Construction

Uses registered design-query traces and frontier margins to weight edges/backups. It has the strongest T-SC5/T-SC10 interface and highest Graph-ANNS specificity, but risks workload overfit and requires instrumentation. **Disposition:** construction core of the primary route, not a standalone safety claim.

### D. Best-of-R

Selects one build using sentinels. It is build autotuning, and if selection uses truth it is target-assisted. It does not produce a stable construction rule and incurs repeated build cost. **Disposition:** comparator, not selected.

### E. Stabilize-then-Certify

Combines C’s registered structural intervention with independent surrogate calibration, target safety certification and fixed-safe fallback. It alone exposes construction, residual shift, risk and deployment cost. **Disposition:** Primary Route.

## Primary pseudocode

```text
STABILIZE_THEN_CERTIFY(X, design_queries, calibration_queries, target_cert_queries,
                       base_builder, R, degree_cap, tau, delta, alpha):
  require role sets pairwise disjoint and preregistered
  shadows <- [base_builder(X, registered_seed[r]) for r in 1..R]
  traces <- instrument deterministic search on design_queries in every shadow
  weights <- aggregate edge retention, frontier rank, path impact, and backup reachability
  G_stable <- base_builder(X, canonical seed/order)
  G_stable <- degree-constrained repair(G_stable, weights,
                  protect high-impact edges and at least one registered backup,
                  preserve connectivity, index size, build-time and recall constraints)
  phi_bound <- calibrate one-sided (d_phi -> budget-shift) on calibration_queries
  if phi_bound invalid, nonmonotone, or endpoint infeasibility worsens: STOP/FALLBACK
  candidates <- preregister shifted policy ladder implied by phi_bound
  certificate <- simultaneous one-sided risk bounds on independent target_cert_queries
  if a candidate is certified and build/service break-even is finite and p95 gate passes:
       return smallest certified action, G_stable, certificate
  else:
       return fixed-safe/retrain action; never use evaluation truth
```

## Objective and constraints

The implementable objective substitutes a design-scope instability proxy for population `Diam_B`:

\[
\min_G \widehat C_{search}(G)+\lambda\sum_{q\in D_{design}}w_q d_\Phi(G,G_q^{shadow})+\mu C_{build}(G),
\]

subject to degree/memory/connectivity, endpoint feasibility, registered recall non-inferiority and a build-time cap. Calibration and target certification are not optimized by this objective.

## Complexity

Shadow construction costs `R T_build`. Trace collection costs the registered design workload times search cost. Edge aggregation is linear in observed trace edges; constrained repair is implementation dependent and should be capped near linear in candidate edges. Online search complexity remains that of the base index plus no learned model; certification and construction are offline. Storage must remain within the degree/index-size constraint.

## Failure modes

Trace overfit; missing/unstable entry paths; weak frontier margins; endpoint infeasibility; degree repair breaking connectivity; consensus dropping rare bridges; worse mean or p95; `gamma_eff<=0`; failed independent certification; and no finite break-even. Every failure returns fallback/retrain, not a revised definition.
