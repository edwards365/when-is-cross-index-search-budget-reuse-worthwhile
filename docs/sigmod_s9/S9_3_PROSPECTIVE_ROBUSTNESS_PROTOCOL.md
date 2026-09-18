# S9-3 prospective robustness protocol

Status: frozen before any S9-3 query vector, truth, index, or response access.

## Handoff and scope

S9-2 established deployment-grade single-thread runtime value for the target-certified Faiss fixed-slack route on the registered 24-build families: wall-time gains were positive with crossed-bootstrap lower bounds above zero, p95 upper bounds below 1.05, zero native-response mismatches, and positive leave-one-target-out minima on both datasets. S9-2's separate recurring-query TCP/target-global runtime block and complete lifecycle ledger remain open. Therefore S9-3 prospectively confirms only the fixed-slack route; it does not upgrade or substitute for those open S9-2 estimands.

## Question and independent units

Does the source-derived one-rung candidate, followed by independent target certification, retain safety, serving-time value, tail noninferiority, and build robustness on entirely new graph builds and query roles?

The independent outer unit is the target build. Source directions, queries, and repeated timings are nested measurements. Eight new insertion-permutation builds per dataset yield eight target units and 56 directed source-target decisions per dataset. The directions are not treated as independent builds.

## Frozen build family

- Datasets: SIFT-100K and Arxiv-Nomic-100K; unchanged first 100,000 base rows and registered metric normalization.
- Implementation: the exact DARTH/Faiss 1.8.0 binary pinned by S9-2 environment correction.
- Construction: HNSW `M=16`, `efConstruction=100`, one thread, `k=10`.
- New insertion-permutation seeds: 6011, 6211, 6421, 6637, 6841, 7057, 7273, 7481.
- Native action grid: 16, 32, 64, 128, 256, 512; endpoint 512.
- No old serialized index is reused as an S9-3 scientific unit.

Faiss does not expose a reliable independent construction RNG in this interface; the registered experimental build factor is the seeded input permutation. Build order is seed-991 randomized and blocked by dataset. Index, permutation, source-data, toolchain, and environment hashes are recorded before query replay.

## Query roles and firewall

For each dataset, select 1,500 source-HDF5 training-row IDs from `[700000, 850000)` after excluding every machine-readable registered ID and external-role snapshot. Selection is seeded before vector or truth access and split into three disjoint roles of 500:

1. `source_design`: choose each source build's action;
2. `target_certification`: qualify the candidate and endpoint;
3. `target_evaluation`: estimate risk, NDC, runtime, and tails without feedback.

All pairwise overlaps and overlap with prior registered roles must equal zero. Access to validation-dev, formal-test, or any reserved sealed role is forbidden.

## Frozen policy and decision

On `source_design`, select the smallest grid action whose one-sided Clopper--Pearson risk UCB is at most 0.05 under Bonferroni allocation `alpha=0.05/6`; otherwise select the endpoint. The candidate is exactly one registered grid rung above that source action, clipped only at the endpoint.

On `target_certification`, separately test candidate and endpoint with `alpha_c=alpha_e=0.025`. Abstain if the endpoint does not qualify; deploy the candidate if both endpoint and candidate qualify; otherwise deploy the independently qualified endpoint. Evaluation cannot change the source action, candidate, threshold, grid, fallback, or reporting rule.

## Runtime and nuisance control

Use logical CPU 2, one Faiss/OpenMP/BLAS thread, no GPU, 50 deterministic warm-up queries per action, and seven interleaved repetitions per evaluation query/action. Record wall time, process-CPU time, top-k hash, recall, NDC, action order, build, role, and repetition. The S9-2 action-block timing-validity amendment remains fixed: median action-block CV at most 5%, maximum at most 10%; cell CV remains a diagnostic. Native top-k, recall, and NDC must be exact across repeated searches.

## Preregistered robustness views

The primary analysis uses the full six-action grid and 5% risk SLA. Without altering the primary decision, derive the following predeclared boundary analyses from the same response cube:

- sparse grid `[16, 64, 256, 512]`;
- upper grid `[32, 64, 128, 256, 512]`;
- risk limits 2.5% and 5%, with the same confidence-error accounting;
- NDC and wall-time endpoints reported separately;
- query-pooled p95 and p99, per-target rows, crossed target-build x query-ID bootstrap, leave-one-target-out, and deletion of the largest-gain 1% of queries.

Sensitivity failures are reported as boundaries. They do not authorize replacing the primary action or retuning the grid.

## Gates and stopping rules

1. Protocol: all role overlaps are zero; inputs and build artifacts match frozen hashes.
2. Instrumentation: zero native top-k, recall, or NDC mismatches and complete response cells.
3. Safety: every executed candidate/fallback is independently qualified; pooled held-out risk is at most 5% on both datasets.
4. Mean runtime: crossed-bootstrap 95% lower bound on relative wall-time gain versus endpoint is above zero on both datasets.
5. Tail: p95 ratio upper confidence bound is at most 1.05; p99 is reported.
6. Robustness: direction survives every target deletion and deletion of the largest-gain 1% of queries.
7. Interpretation: eight builds are prospective fixed-family confirmation, not open-population certification.

Stop immediately on role overlap, hash drift, endpoint-certification failure, native-response mismatch, uncontrolled timing, resource threat, or any need to tune after response access. Negative and mixed results are retained. S9-4 is not authorized by a partial S9-3 result.

