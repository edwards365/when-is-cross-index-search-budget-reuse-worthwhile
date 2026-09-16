# Supplement Loop 2: harmonized lifecycle distance cost

Decision: **LIFECYCLE_DISTANCE_COST_GATE_PASSED**.

Costs use native distance evaluations. Exact target labels, the full registered selection grid, independent certification search, source profiling, and serving are all counted. Rebuild cost cancels because TCP and fixed-safe serve the same rebuilt target graph. Control adds no distance calls beyond selection replay; wall-clock remains exploratory.

| Dataset | Ratio-of-means break-even | 95% build CI | Max finite build | Non-amortizing builds | First registered positive N |
|---|---:|---:|---:|---:|---:|
| sift100k | 138836 | [138607, 139055] | 139254 | 0 | 1000000 |
| arxiv_nomic_100k | 107378 | [96583, 138090] | 96920 | 1 | 1000000 |

The result is an amortized lifecycle-distance claim, not a controlled wall-clock or monetary claim. Phase 2 safety and tail decisions are imported unchanged.
