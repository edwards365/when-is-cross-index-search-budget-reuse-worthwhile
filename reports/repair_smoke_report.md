# Degree-preserving repair smoke report

Date: 2026-08-22. Status: completed negative Tier-0 smoke result.

This experiment used the actual layer-0 adjacency exported from an hnswlib `v0.8.0` index over a deterministic 512×8 two-cloud fixture (`M=16`, `efConstruction=100`, seed 7). All variants preserved every node's outgoing degree and the total 5,487 directed-edge budget. Search used the same instrumented bottom-layer candidate-queue implementation from the fixed hnswlib entry point. One hundred exact-ground-truth queries were generated independently with seed 23.

## Matched-recall observations

| Variant | Smallest ef reaching 0.95 | Recall@10 | Mean NDC | P95 NDC | Smallest ef reaching 0.99 |
|---|---:|---:|---:|---:|---:|
| Original | 10 | 0.995 | 98.05 | 125.05 | 10 |
| Random | 20 | 0.978 | 139.73 | 177.00 | 40 |
| Distance | not reached | 0.588 at ef=80 | 193.75 | 201.05 | not reached |
| Geometry | 20 | 1.000 | 139.01 | 191.10 | 20 |
| Resistance | 40 | 0.966 | 182.05 | 205.00 | not reached |
| Resistance+Direction | 20 | 0.984 | 135.94 | 160.05 | 40 |

The current full-reselection intervention is negative: neither resistance variant beats Original at matched recall, and Resistance-only fails to reach 0.99 in the scanned range. Geometry restores recall better than Resistance-only, while distance-only destroys cross-region navigation. Random rewiring also degrades performance.

## Interpretation boundary

This does not decide H2. It is one small synthetic fixture, one graph seed, and a bottom-layer-only reference search. The intervention replaces 2,487 directed edges for Resistance+Direction (45.3% of the graph), uses an augmented star to define candidate-edge leverage, and does not yet use rejected insertion candidates or a small repair fraction. It therefore tests an intentionally simple, aggressive version and reveals that wholesale local objective optimization can erase useful HNSW structure.

The next implementation must preserve most original heuristic edges and apply controlled swaps only when a rejected candidate clears a frozen margin, with Random and Geometry swaps matched by replacement count. This change is a response to a mechanistic failure, not test-set tuning; its rule must be frozen before evaluation on new queries/seeds.

