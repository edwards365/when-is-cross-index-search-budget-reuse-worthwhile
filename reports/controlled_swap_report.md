# Trace-gated controlled-swap feasibility report

Date: 2026-08-22. Run ID: `controlled-swap-independent-holdout-s7`. Status: valid negative result for resistance-specific quality benefit.

## Question and boundary

The electrical identities, leverage bounds, rank-one updates, and frozen local submodular objective are already proved under their stated undirected/local assumptions. They do not imply that modifying a directed HNSW layer improves Recall@k or search cost. This experiment tests that missing empirical implication for one deterministic synthetic graph; it cannot prove a universal benefit or impossibility.

## Frozen intervention

The final 512-node layer-0 graph has 5,487 directed edges. The intervention replaces 46 directed edges (0.8383%) from 46 distinct sources. Trace+Resistance additions are the exact progressive orientations that could have entered the beam toward a missed top-10 neighbor in the earlier attribution workload. Resistance-only, Geometry, and Random use the same 46 sources and replacement count.

Every variant removes the same edge at each source. All 46 removed edges are reciprocal, so deleting one direction leaves the union-symmetrized electrical support unchanged and has zero frozen undirected deletion sensitivity. The added neighbor replaces the removed neighbor in the same stored-list position; every source degree and the total directed edge count are unchanged.

The controls are:

- `trace_resistance`: trace gate first; insertion-time Scheme B is retained as metadata;
- `resistance_only`: maximum Scheme-B rejected candidate for each matched source;
- `geometry`: nearest rejected candidate for each matched source;
- `random`: seeded random rejected candidate for each matched source;
- `original`: no replacement.

## Leakage audit

An initial evaluation used independent noise but perturbed existing base points. It produced an apparent ef=10 Recall@10 gain of 0.001855. That evaluation is rejected because its query templates overlap the selection workload's base identities; it is retained outside the frozen result directory as an invalid design audit and is not evidence.

The valid holdout contains 1,024 fresh points sampled with seed 101 directly from the balanced two-cloud Gaussian distribution, with no query overlap. Each is searched at `ef={10,20,40}`. For all 3,072 Original searches, the Python ordered layer-0 replay exactly matches the C++ hnswlib labels and exact distance-call count. Paired percentile bootstrap intervals use 5,000 replicates with seed 991 and are descriptive, not multiplicity-adjusted confirmatory intervals.

## Independent holdout result

| Variant | ef | Mean Recall@10 | Non-full-recall queries | Mean exact NDC | P95 NDC |
|---|---:|---:|---:|---:|---:|
| Original | 10 | 0.978125 | 190 | 107.407 | 132 |
| Trace+Resistance | 10 | 0.977734 | 191 | 106.978 | 132 |
| Resistance-only | 10 | 0.978027 | 188 | 107.236 | 132 |
| Geometry | 10 | 0.977930 | 190 | 106.864 | 131 |
| Random | 10 | 0.977734 | 191 | 107.519 | 132 |
| Original | 20 | 0.998926 | 11 | 146.895 | 171 |
| Trace+Resistance | 20 | 0.998828 | 12 | 146.466 | 170 |
| Resistance-only | 20 | 0.998828 | 12 | 146.692 | 170 |
| Geometry | 20 | 0.998828 | 12 | 146.248 | 169.85 |
| Original | 40 | 1.000000 | 0 | 198.100 | 223 |
| Trace+Resistance | 40 | 1.000000 | 0 | 197.610 | 222 |
| Resistance-only | 40 | 1.000000 | 0 | 197.903 | 223 |
| Geometry | 40 | 1.000000 | 0 | 197.413 | 221 |

At ef=10, Trace+Resistance minus Original Recall@10 is `-0.000391`, with 95% interval `[-0.001074, 0.000293]`; there is no demonstrated recall improvement. Its mean NDC difference is `-0.429688`, interval `[-0.575195,-0.294922]`. Resistance-only also reduces NDC by `-0.170898`, but its recall difference is `-0.000098` with an interval crossing zero.

The NDC reduction is not resistance-specific. Geometry reduces ef=10 NDC by `-0.542969`, more than Trace+Resistance in point estimate, while its recall difference also crosses zero. At ef=20 and 40, Geometry has lower mean NDC than Trace+Resistance by 0.217773 and 0.197266 respectively. Random slightly increases NDC.

## Decision

Three conclusions must remain separate:

1. **Mathematical feasibility: established locally.** The resistance quantities and frozen local optimization guarantee are correct within their declared graph model.
2. **Engineering feasibility: established.** Real HNSW candidates can be logged, scored, trace-attributed, swapped under exact degree budgets, and evaluated reproducibly.
3. **Resistance-specific ANNS benefit: not established.** On the valid independent holdout, neither resistance variant improves recall, and a simpler Geometry control explains at least as much or more of the NDC reduction.

The current trace-gated resistance rewiring route therefore fails its proof-of-benefit gate on this fixture. No further tuning on these queries is permitted. A future continuation requires a preregistered multi-seed/public-dataset external-validity study or a materially new query-independent hypothesis; it should not present this configuration as an improved HNSW algorithm.
