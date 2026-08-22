# Methodology

## Experimental hierarchy

Tier-0 smoke runs establish numerical correctness, exact ground truth, graph invariants, metadata capture, and Recall--ef behavior. They do not establish H1 or H2. Mechanism runs precede performance intervention runs; held-out test queries are not used for tuning.

At matched Recall@10 targets, each method uses the smallest validation-selected `efSearch`. Report mean, P50/P95/P99 NDC and latency, failure rate, memory, build/repair cost, paired query bootstrap intervals, per-seed outcomes, and insertion-order variance. Random rewiring and geometry-only are mandatory controls.

## Local graph model

The standard quantity is computed on a connected undirected weighted candidate graph. Directed HNSW neighborhoods are evaluated under union, intersection, and reciprocal-upweight symmetrization. Unweighted and Gaussian distance-weighted graphs are separate ablations. Cross-component resistance is infinite; any component-wise or regularized calculation is labeled and never called the standard resistance.

## Leakage controls

Dataset splits, metrics, primary targets, candidate-pool rules, score definitions, and coefficients are frozen before the primary test. Failed seeds remain in raw results. No result is promoted from synthetic-only evidence.

