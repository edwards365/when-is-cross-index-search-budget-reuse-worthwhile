# Frozen Vamana Stage-I experimental contract

This is a preregistration, not an executed experiment.

## Scope

- implementation: Microsoft DiskANN3 at `8fb4d42e6a8bff0cff4db976a55c5fb99faaf475`;
- provider: in-memory primary mode; SSD is a separate future regime;
- data: SIFT 30K and Arxiv-Nomic 30K, same base corpora as registered HNSW units;
- builds: 12 per dataset, six source and six held-out target;
- queries: 750 mutually exclusive evaluation queries per dataset;
- actions: six preregistered raw `Knn::l_value` values, with `beam_width=1`;
- primary design: 36 asymmetric source-to-target directions per dataset;
- full 132 directed non-diagonal pairs: descriptive only.

No evaluation or future-replication vector/truth may be inspected while finalizing values, seeds, splits or gates.

## Build lock

Freeze corpus hash, input order/permutation seed, `random_seed`, maximum degree, `l_build`, alpha/prune settings, start-point strategy, distance metric, thread count, Rust/compiler version, Cargo lock hash, feature flags, CPU/SIMD and serialization format. Vary exactly one legitimate replayable build variable in Stage I; the recommended variable is preregistered input permutation while all other controls remain fixed. Never discard a failed build.

## Preflight

Before touching pilot queries: identical-config duplicate replay must be within deterministic replay tolerance; different environment values must yield distinct artifact hashes or declared graph summaries; save/load must preserve registered query traces on a non-held-out toy set. Failure stops the pilot.

## Outcomes

Primary: build environment changes the endpoint-aware safe-budget response. Report corrected transport categories, right-censoring, jointly feasible budget disagreement, asymmetric unsafe migration increment, and implementation-local ROM cost tax.

Costs are a vector: `l_value`, distance computations, visited/hops, in-memory bytes/touches when available, wall-clock, and (only in SSD mode) I/O operations/bytes. No cross-family raw NDC or wall-clock equality is assumed.

## Gates

Detection requires correct direction, uncertainty excluding zero or replay noise, LOBO direction stability, top-1%-query deletion stability, and no single-build dominance.

Materiality requires category change at least 10% or jointly feasible budget disagreement at least 5%, plus asymmetric migration-risk increment at least 2 percentage points or within-implementation ROM cost tax at least 3%.

Stage II is authorized only if Stage I passes: either 24 builds per dataset or one 100K validation unit, never simultaneous Vamana and NSG expansion.

## Stopping

Stop on replay failure, unclear native budget, missing failure/cost counters, query-role contamination, endpoint misclassification, inability to reproduce source/target split, or a fatal mismatch between configured and executed action.
