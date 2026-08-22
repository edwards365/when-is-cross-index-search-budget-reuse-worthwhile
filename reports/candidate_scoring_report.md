# Offline insertion-candidate resistance scoring report

Date: 2026-08-22. Run ID: `candidate-scoring-s7`. Status: successful Tier-0 mechanism run.

## Frozen scoring contract

The run reads the immutable `hnsw-candidate-logging-s7` artifacts and replays only logged layer-0 adjacency changes. It does not rebuild, mutate, or query an HNSW index. The replay recovers all 5,487 final directed edges exactly.

For insertion center \(u\), the local vertex set is \(u\) plus the candidates retained by HNSW's `efConstruction`-bounded result queue. Directed HNSW edges are union-symmetrized. All schemes share one Gaussian scale \(\rho\): the median Euclidean edge length in the union of the actual post-insertion induced graph and the dense center star. The logged hnswlib L2 distance is squared Euclidean distance, so a proposed center edge has weight \(\exp(-d_{\mathrm{HNSW}}/\rho^2)\).

- Scheme A scores every candidate as existing-edge leverage in the dense-center-star reference graph.
- Scheme B scores only a rejected edge by \(wR\) in the actual post-insertion graph, before hypothetically adding that edge. A cross-component endpoint pair has infinite gain.
- Scheme C scores only an accepted edge by its existing-edge leverage in the actual post-insertion graph.

The Scheme-B state is intentionally after standard HNSW has inserted its accepted center edges. Before insertion the new center is isolated and every proposed edge would have infinite effective resistance.

## Results

| Quantity | Value |
|---|---:|
| layer-0 rows scored | 46,150 |
| accepted / occluded | 2,807 / 43,343 |
| final directed edges recovered | 5,487, exact match |
| Scheme-A finite rows | 46,150 / 46,150 |
| Scheme-A median, accepted / rejected | 0.153741 / 0.057769 |
| Scheme-A median per-insertion score range | 0.262399 |
| Scheme-A median per-insertion Spearman correlation with distance | -0.670531 |
| Scheme-A top-|accepted| overlap with actual accepted set | 42.47% |
| Scheme-B connected rejected rows | 99.9815% |
| Scheme-B disconnected/infinite rejected rows | 8 |
| Scheme-B finite median / P95 / maximum | 0.129998 / 0.349907 / 51.7840 |
| Scheme-C median / P95 | 0.284668 / 0.522987 |
| A/C leverage violations above \(1+10^{-4}\) | 0 / 0 |
| finite Scheme-B score greater than its blocker's Scheme-C score | 5.86% |

Scheme A is not constant on this real candidate population: its median within-insertion range is 0.2624. It is nevertheless substantially entangled with locality, and selecting the same number of top-A candidates recovers only 42.47% of HNSW's Algorithm-4 accepted set.

The eight infinite Scheme-B rows are genuine local induced-graph disconnections. They are retained explicitly rather than regularized. Scheme B is otherwise finite, with a long upper tail. Scheme C obeys the existing-edge leverage bound within the declared numerical tolerance. Comparisons between B and a blocker's C value are diagnostics, not exact swap gains; exact swaps remain order-dependent.

## Two-cloud cross-region diagnostic

For insertions 256--511, 20.70% of rejected candidates point to the earlier cloud. Ranking rejected candidates by Scheme B reduces, rather than enriches, this fraction: top-1 is 7.42%, top-5 is 4.69%, and top-10 is 4.65%. On this fixture, raw local Scheme-B gain is therefore not a justified cross-region-edge selector.

This is negative mechanism evidence, not a general impossibility result. Cluster membership is a fixture-only diagnostic and was not supplied to the scorer.

## Numerical audit and next gate

The implementation caught and corrected two silent numerical hazards before this result was frozen: hnswlib's L2 log uses squared distance, and SciPy's dense weighted connected-component conversion can drop very small nonzero conductances. The final code checks logged distances against `points.csv`, computes connectivity from the exact Boolean support, checks final graph equality, and rejects leverage violations above \(1+10^{-4}\).

The next step is not broad rewiring. First add exact query-trace attribution and test whether high-B rejected edges intersect failed or expensive search routes. Only trace-supported candidates should enter a small-fraction controlled-swap experiment, with Geometry and Random controls matched by replacement count.
