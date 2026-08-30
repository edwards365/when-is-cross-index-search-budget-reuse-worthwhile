# Stable-by-Construction full theory report

## 1. Problem and estimands

For dataset `X`, build algorithm `A`, and environment `xi`, an index is `G_xi=A(X,xi)`. Environment includes declared randomness, insertion order, concurrency schedule, approximate-neighbor candidates, implementation version and numerical semantics. Fix query law `P_Q`, ordered budget grid `E`, target recall `tau`, and search implementation.

The minimum safe budget is

\[
B_G(q)=\min\{e\in\mathcal E:R_G(q,e)\ge\tau\},
\]

with an explicit `infinity` state when the endpoint is infeasible. The safe-set monotonicity required by the positive theory is an assumption to test, not a consequence of the grid. Right censoring is not imputed as `e_L`.

Three response distances are useful: mean absolute grid-rank distance, a high quantile of that distance, and the one-sided exceedance probability `Pr(B_t>B_s+m)`. The last one is directly aligned with under-budget migration. Define `Diam_B` over a declared build family; it is meaningless without its support.

The ideal stable construction objective is

\[
\min_A E_\xi C_{search}(G_\xi)+\lambda Diam_B(\mathcal G_A)+\mu C_{build}(A)
\]

subject to recall non-inferiority, endpoint feasibility, degree, memory, build-time and mean/tail cost constraints. Because `B_G` uses truth, deployment needs a surrogate `Phi` and a calibrated interface. The report proves that generic edge metrics cannot serve this role universally.

## 2. Eight distinct stability objects

1. **Reproducibility:** same complete build input gives the same bytes/index.
2. **Edge-set similarity:** a graph-level set statistic.
3. **Local structural similarity:** neighborhoods, degrees, connectivity, layers.
4. **Search-path similarity:** trace/frontier behavior under a named query and algorithm.
5. **Recall–budget similarity:** the whole query response curve.
6. **Minimum-safe-budget similarity:** a target-recall crossing time with censoring.
7. **Certification complexity:** evidence needed for a risk statement.
8. **Service cost:** mean and tail NDC/latency plus build/evidence/fallback/control costs.

Only adjacent arrows with explicit premises are licensed. In particular, edge overlap does not imply path or budget stability, and a mean budget statement does not imply p95.

## 3. Theory status

The exact statements and proofs are in `proof_appendix.md`. In short, T-SC2 is the central risk interface; T-SC5/T-SC10 are the only nontrivial Graph-ANNS structural link; T-SC4/T-SC6 are classical concentration; T-SC1/T-SC8 are identities; and T-SC9 prevents surrogate overclaiming.

| ID | Result | Status | Novelty class |
|---|---|---|---|
| T-SC1 | canonical deterministic replay | proved | IDENTITY_OR_DEFINITION |
| T-SC2 | one-sided grid-coupled migration risk | proved | RESTRICTED_DOMAIN_PROPOSITION |
| T-SC3 | budget-to-NDC/latency conditional bound | proved conditionally | RESTRICTED_DOMAIN_PROPOSITION |
| T-SC4 | effective-margin certification size | proved | CLASSICAL_APPLICATION |
| T-SC5 | path disruption and robust trace budget bound | proved in restricted model | POTENTIAL_NEW_GRAPH_ANNS_RESULT |
| T-SC6 | consensus-edge uniform concentration | proved | CLASSICAL_APPLICATION |
| T-SC7 | diameter/minimax safety-compute-reject tax | proved in two-point/Lipschitz classes | RESTRICTED_DOMAIN_PROPOSITION |
| T-SC8 | build/service break-even | proved | IDENTITY_OR_DEFINITION |
| T-SC9 | 16 structural non-implications | constructive | COUNTEREXAMPLE_ONLY |
| T-SC10 | general surrogate impossibility; restricted certificate | proved/restricted | POTENTIAL_NEW_GRAPH_ANNS_RESULT |

## 4. Literature forensics result

The A-level set contains 23 papers. HNSW, NSG and Vamana define strong construction baselines but do not optimize cross-build `B_G`. FreshDiskANN empirically preserves recall under a stream, not source-policy portability. Elliott–Clark directly establish insertion-order sensitivity. ANNiE states that a concrete index affects query cost and limits its theorem to the training distribution. QBAT and the adaptive methods profile or train for a concrete configuration. Yang et al. (2024) is the most dangerous structural neighbor: its Theorem 4.1 relates beam-search results to minimax path rank after pruning, and Theorem 4.2 gives an expected pruning/path-quality statement under uniform infinite-space and independence assumptions. It neither studies rebuild pairs nor minimum safe budget, but it makes generic “first path-aware construction theory” claims untenable.

Risk-control papers provide the certification half. LTT/RCPS give high-probability fixed-distribution selection/certification; CRC is an expected-risk calibration result; Duchi et al. address an outer environment layer but not graph construction or ordered compute. These are reusable modules, not direct method precedents.

## 5. Algorithm route

The selected primary route is **Stabilize-then-Certify with Critical-Path/Frontier Stabilization**. It does not optimize the inaccessible population `B_G` directly. It preregisters design probes, builds a small shadow family, extracts trace edges and robust backups, repairs a base graph under degree/connectivity and quality constraints, calibrates the surrogate-to-budget relation on separate queries, and finally uses independent target certification. It falls back to consensus-with-protected-bridges if trace instrumentation is unavailable.

This route is chosen because it is the only one that exposes all links needed by T-SC2/T-SC5. Canonical construction is cheap but solves only repeatability. Naive consensus estimates the wrong object. Best-of-R is selection/autotuning and often label-dependent. A Stable-then-Certify combination is operationally complete, but each module retains its own failure Gate.

## 6. Cost and tail discipline

Stable construction is deployable only if

\[
N(g_{search}+g_{cert}+g_{fb}-C_{control})>\Delta C_{build}.
\]

If the net per-query term is nonpositive, the correct output is `NO_FINITE_BREAK_EVEN_WORKLOAD`. A finite mean break-even does not authorize p95; the pilot must show separate query-pooled p95 non-inferiority and top-1% deletion robustness.

## 7. Scope of safety

T-SC2 is a pairwise source/target result under an explicit coupling. T-SC4 is fixed-target conditional certification from independent target queries. An outer-build statement needs a probability law over builds, support coverage and independent build units. Nothing here converts query-level resampling into build-level evidence. The current positive theory therefore remains fixed-target plus a conditional pairwise construction theorem.

## 8. Gate and recommendation

The structural object is valid; the general surrogate is not. A restricted surrogate exists and its components are observable on registered probes, so a small pilot is scientifically justified. The highest valid novelty is a Graph-ANNS-specific combination with a potentially independent restricted trace proposition. The recommended venue direction is database/systems first. A top-ML theory claim should wait for either a broader verifiable graph class with matching lower/upper bounds or an outer-build theorem with a real build distribution.
