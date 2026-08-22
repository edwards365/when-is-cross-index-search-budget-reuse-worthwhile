# Exact query-trace attribution report

Date: 2026-08-22. Run IDs: `query-tracing-s7` and `query-attribution-s7`. Status: successful Tier-0 diagnostic.

## Trace contract

A non-invasive C++ replay implements the unmodified hnswlib upper-layer greedy descent and bare-bone layer-0 beam search. For every exported query it asserts both the returned label set and the exact wrapped distance-call count against upstream `searchKnn`. The trace records upper evaluations, layer-0 entry, expansion order, first neighbor evaluations, queue lower bounds, result-queue sizes, and enqueue/prune outcomes. The graph is never changed.

The deterministic fixture contains 512 points in 8 dimensions. There are 256 noisy point queries, each evaluated at `ef={10,20,40}`, for 768 exact traces.

| ef | Mean Recall@10 | Queries below full recall | Mean exact NDC | P95 exact NDC | Mean layer-0 expansions |
|---:|---:|---:|---:|---:|---:|
| 10 | 0.996875 | 8 | 105.2891 | 126.25 | 10.9531 |
| 20 | 1.000000 | 0 | 145.8164 | 170.50 | 20.5703 |
| 40 | 1.000000 | 0 | 197.7227 | 224.25 | 40.2773 |

## First-opportunity attribution

For each historical rejected insertion pair, both directions are checked whenever one endpoint is expanded. A directed opportunity is eligible only if the target has not yet been visited and would pass the exact HNSW queue condition at that moment. It is progressive if the target is also strictly closer to the query than the expanded source.

This is a first-opportunity diagnostic. It does not simulate the downstream queue and expansion changes caused by actually adding the edge, so it is not a counterfactual recall claim.

| Quantity | Value |
|---|---:|
| historical rejected candidates | 43,343 |
| candidates with any trace opportunity | 43,337 |
| candidates with any queue-eligible opportunity | 42,278 |
| candidates with any progressive eligible opportunity | 3,232 (7.46%) |
| candidates with an eligible direction to an actually missed top-10 neighbor | 92 |
| exact failure-query orientations that are also progressive | 46 |
| failed queries covered by at least one eligible missed-neighbor edge | 8 / 8 |
| failed queries covered by at least one progressive missed-neighbor edge | 8 / 8 |

Scheme B has only weak rank association with progressive trace support: Spearman correlation is 0.1458. Its top-1 rejected candidate per insertion has 16.94% progressive support and top-5 has 14.84%, versus 7.46% over all rejected candidates. Thus Scheme B provides some enrichment, but it is not a sufficient primary filter.

The best progressive candidate's Scheme-B rank for the eight failed queries is `2, 4, 1, 9, 67, 3, 1, 1`. In particular, a B-only top-k rule would discard navigation-supported candidates for some failures. The evidence supports the ordering **query trace first, resistance score second**.

## Intervention gate

The next controlled intervention may use only directed candidates that satisfy all of the following on the attribution workload:

1. the edge was present in the real construction candidate population and rejected by Algorithm 4;
2. its source was expanded before its target was visited;
3. the target would have entered the beam under the recorded queue state;
4. the target was a missed exact top-10 neighbor and was strictly closer than the source.

There are 46 such directed failure-query opportunities covering all eight failures. Selection must cap replacements per source and use Scheme B only as a secondary ranking signal. Degree preservation requires an explicit add-first/delete-second rule and a newly computed final-graph deletion score; insertion-time Scheme C cannot be reused silently.

The 256 attribution queries are selection data and must not be reused to claim improvement. The intervention must be evaluated on fresh held-out queries from a separate seed, alongside Geometry and Random controls matched by directed replacement count and source-degree constraints. Until that held-out experiment is run, the correct result is candidate identification—not improved HNSW performance.
