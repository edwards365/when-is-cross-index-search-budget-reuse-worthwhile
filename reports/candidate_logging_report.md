# HNSW insertion-candidate logging smoke report

Date: 2026-08-22. Run ID: `hnsw-candidate-logging-s7`. Status: successful Tier-0 instrumentation run.

## Instrumentation contract

Before each sequential `addPoint`, the logger copies HNSW's level RNG to predict the next level, replays the same upper-layer descent and `searchBaseLayer`, and applies the exact `getNeighborsByHeuristic2` strict-occlusion rule. It records every candidate returned in the bounded construction result queue as `accepted`, `occluded` (with the first selected blocker), or `budget_exhausted`. After the real unmodified insertion, it asserts that every replayed selected set equals the new node's actual adjacency at every participating layer.

For every selected neighbor it snapshots adjacency before and after insertion, recording reverse additions and pruning removals. At export time it checks whether both directions survive all later insertions. The upstream hnswlib submodule is unchanged.

The replay performs extra construction-time distance calls. Therefore this instrumented build is valid for candidate/adjacency mechanism analysis but **not** for measuring HNSW construction cost. Query NDC remains valid because the counting space is reset immediately before every query.

## Local fixture result

The deterministic 512-by-8 two-cloud fixture uses `M=16`, `efConstruction=100`, graph seed 7, and sequential unique labels. The final graph is unchanged from the earlier instrumentation fixture: 5,487 directed layer-0 edges, 5,372 reciprocal directed edges, maximum degree 32, Recall@10=1, exact mean query NDC 199, and mean high-layer hops 3.3125.

| Quantity | Value |
|---|---:|
| all-layer candidate rows | 46,504 |
| all-layer accepted | 2,959 |
| all-layer occluded | 43,545 |
| all-layer budget-exhausted | 0 |
| layer-0 candidate rows | 46,150 |
| layer-0 accepted | 2,807 |
| layer-0 occluded | 43,343 |
| mean/median/P95 layer-0 candidates per noninitial insertion | 90.31 / 100 / 100 |
| selected reverse edge present immediately | 99.93% |
| selected forward edge survives final graph | 97.60% |
| selected reverse edge survives final graph | 96.59% |
| reverse adjacency additions/removals | 2,957 / 170 |
| rejected candidates later appearing as either final edge | 0 |

## Interpretation

On this fixture, Algorithm 4 direction/relative-neighborhood occlusion—not the `M` stopping budget—creates the rejected set. This is the correct population for the next mechanism question: among candidates rejected as geometrically redundant, do scheme-B pre-insertion gain or other resistance scores identify query-aligned cross-region edges that the original heuristic missed?

The high accepted-edge survival rates show that later insertions and reverse pruning perturb, but do not erase, most initial decisions. They are still not universal constants and must be measured by dataset, insertion order, layer, and seed.

## Scope and next action

The logger currently assumes sequential unique-label insertion with no deletion/replacement. `C_u` means the candidates retained by HNSW's `efConstruction`-bounded `searchBaseLayer` result queue, not every node visited during construction. The next step is to compute scheme A/B/C scores on the logged layer-0 accepted/rejected pairs without modifying the graph, then measure score dispersion, ties, top-rank overlap, blocker geometry, and final-edge survival.
