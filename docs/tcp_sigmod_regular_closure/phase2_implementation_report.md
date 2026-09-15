# TCP-HM9-TC Phase 2 implementation report

## Status

The canonical stable-tail implementation and its fixed-sequence target
certificate are executable on both registered datasets. These are fixed-target
query-risk results, not a 5% exchangeable-build certificate.

## Arxiv-Nomic-100K

- Endpoint efSearch=200 passed on all 10 target builds.
- TCP passed on 9/10 target builds; seed 1621 had CP UCB 0.050564 and correctly
  fell back to the endpoint.
- Pooled deployed evaluation risk was 0.0207.
- Mean distance computations were 733.5945 versus 2422.6331 for the endpoint,
  a 69.72% reduction.
- Query-pooled p95 was 2485.05 versus 3289.05; p99 was 3174.01 versus 3602.06.
- The nested bootstrap mean difference was -1689.0386 with 95% interval
  [-1883.5881, -1310.3934].
- The candidate used endpoint abstention for 0.1% of evaluation queries.

## SIFT-100K

- Endpoint and TCP passed on all 10 target builds.
- Pooled deployed evaluation risk was 0.0240.
- Mean distance computations were 532.2958 versus 1978.3692 for the endpoint,
  a 73.09% reduction.
- Query-pooled p95 was 1298.00 versus 2639.00; p99 was 2129.08 versus 2753.01.
- The nested bootstrap mean difference was -1446.0734 with 95% interval
  [-1454.3746, -1437.6806].
- Endpoint abstention covered 0.2%-0.3% of evaluation queries by target build.

## Interpretation boundary

The corrected Arxiv evidence reverses the old zero-headroom artifact, but the
endpoint is not yet the best deployable efficiency baseline. The previously
selected fixed ef baseline and target-only profiling must be reconstructed
with valid selection/certification separation before the SIGMOD efficiency
Gate can be evaluated. Lifecycle cost, LOBO, largest-benefit deletion, cold
queries, and prospective builds also remain open.
