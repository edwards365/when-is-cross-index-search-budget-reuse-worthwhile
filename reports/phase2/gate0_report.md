# Gate 0: epsilon-zero numerical and treatment-strength audit

## A. Stage conclusion

Status: **BLOCKED** overall; numerical sub-gate **PASS**, final-HNSW integration
sub-gate **BLOCKED**.

Scientific conclusion: the observed epsilon-zero action space is real under the
implemented frozen Geometry objective and is not created by the former absolute
`1e-12` tolerance. However, the selector is not yet integrated before reciprocal
insertion/reverse pruning, so actual retained treatment strength in the final HNSW
graph is unknown. This is a numerical/development-mechanism result, not a search or
confirmatory result.

## B. Evidence

Configuration: first 10,000 `train` vectors from SIFT1M, normalized GloVe-100, and
normalized Arxiv-Nomic; seed 7; 128 deterministic centers per dataset; 32 candidates;
`M=16`; one thread; epsilon zero; Geometry tolerances `0, 1e-15, 1e-12, 1e-9`;
frozen-leverage tolerance `1e-12`. Decimal-60 recomputation covered a fixed stratified
32-center sample per dataset. Code commit: `34586b3`.

| Dataset | Changed sources at every tolerance | Swaps at every tolerance | Proposed directed Jaccard | Proposed support Jaccard | Total leverage gain |
|---|---:|---:|---:|---:|---:|
| SIFT | 73/128 | 163 | 0.856754 | 0.857403 | 6.057851 |
| GloVe-100 | 57/128 | 106 | 0.902462 | 0.902428 | 19.370506 |
| Arxiv-Nomic | 50/128 | 110 | 0.899814 | 0.899814 | 9.467793 |

The complete swap counts and selected sets were identical across the four tolerance
levels. Repeating every selection with identical inputs produced a deterministic
fraction of 1.0. Float64 final Geometry change was never negative. Among
high-precision sampled centers that actually swapped, Decimal-60 final-minus-baseline
Geometry changes were all strictly positive:

| Dataset | Sampled changed centers | Minimum | Median | Maximum |
|---|---:|---:|---:|---:|
| SIFT | 18 | 0.000029 | 0.010812 | 0.114369 |
| GloVe-100 | 13 | 0.000338 | 0.008696 | 0.025215 |
| Arxiv-Nomic | 11 | 0.000037 | 0.006203 | 0.012103 |

Individual exchanges can reduce Geometry relative to the immediately preceding set,
but every accepted set stays above the fixed greedy baseline; this is why per-swap
minimum deltas can be negative while final-minus-baseline deltas are nonnegative.
Every swap records float64 and sampled Decimal deltas, leverage delta, guard margin,
candidate size, source, target, and layer. All audited swaps were layer 0.

Total wall time was 262.97 s; dataset audit times were 50.39 s (SIFT), 27.96 s
(GloVe), and 170.73 s (Arxiv-Nomic). Peak process RSS was 179,953,664 bytes. These are
audit costs, not final integrated construction overhead. The v2 core numeric rows are
exactly value-identical to the superseded field-incomplete v1 run.

Artifacts are registered in `artifacts/phase2_dev_manifest.yaml`. The derived partial
graph topology table is explicitly scoped to the 128 audited sources and cannot stand
in for final-HNSW connectivity, reciprocity, clustering, indegree, or hubness.

## C. Falsification and controls

- Tolerance artifact: not observed through `1e-9`; zero-tolerance results are identical.
- High-precision reversal: not observed for any sampled changed center.
- Seed/thread nondeterminism: not observed under the audited seed and one-thread setup.
- Reverse-pruning erasure: unresolved because GGR currently operates outside the
  in-build reciprocal/reverse-pruning path.
- Geometry-safe Random: not yet implemented.
- Shuffled-Resistance: not yet implemented.
- Data leakage: no official `test`, `neighbors`, or `distances` HDF5 member was read.

## D. Decision

Gate 0 does **not** authorize Gate A. The numerical component permits epsilon zero to
remain the candidate main setting, but it cannot be frozen as the integrated main
method until proposed swaps are inserted through the real HNSW reciprocal and reverse-
pruning path and their survival/treatment metrics are measured. Next work is final-
graph integration instrumentation, followed by Geometry-safe Random and
Shuffled-Resistance on the identical feasible-swap path.

Do not state that epsilon-zero GGR improves HNSW, that the greedy Geometry baseline is
globally optimal, or that the proposed-edge Jaccard is a final-index treatment measure.
