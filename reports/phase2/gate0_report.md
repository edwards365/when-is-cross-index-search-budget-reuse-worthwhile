# Gate 0: epsilon-zero numerical and final-graph treatment audit

## A. Decision

Status: **PASS for development screening** at epsilon zero. The numerical and
final-graph treatment sub-gates both pass. Formal HDF5 `test`, `neighbors`, and
`distances` members remain sealed; this result contains no search-performance claim.

The pass is deliberately scoped to a paired, independent, post-build level-0
fixed-selection integration. The external Geometry or GGR set is written first and
then hnswlib's reciprocal insertion, capacity check, and Algorithm-4 reverse pruning
are executed. It proves that the selected GGR treatment is real and survives in a
final HNSW graph. Native per-insertion selection remains an engineering task before
large-scale timing claims.

Under the preregistered rule, epsilon zero is now frozen as the Phase-II main setting.
Epsilon 0.005 and 0.01 remain development-only sensitivity settings and may not be
selected using formal outcomes.

## B. Numerical authenticity

The audit used the first 10,000 `train` vectors from SIFT1M, normalized GloVe-100,
and normalized Arxiv-Nomic; seed 7; one thread; 128 fixed centers per dataset; 32
candidates; `M=16`; and Geometry tolerances `0, 1e-15, 1e-12, 1e-9`. Decimal-60
recomputation covered 32 fixed centers per dataset.

| Dataset | Changed centers | Swap steps | Geometry total delta | Leverage total gain |
|---|---:|---:|---:|---:|
| SIFT | 73/128 | 163 | +1.628146 | +6.057851 |
| GloVe-100 | 57/128 | 106 | +0.661461 | +19.370506 |
| Arxiv-Nomic | 50/128 | 110 | +0.362605 | +9.467793 |

Counts and selected sets were identical at every tolerance, and duplicate runs were
byte-identical for every retained CSV. Float64 final-minus-baseline Geometry was never
negative. Decimal-60 changed-center minima were +0.000029 (SIFT), +0.000338 (GloVe),
and +0.000037 (Arxiv). Thus epsilon-zero action is not a tolerance artifact.

Geometry delta quartiles over all 128 centers were SIFT `[0, 0.003558, 0.016953]`,
GloVe `[0, 0, 0.006365]`, and Arxiv `[0, 0, 0.002527]`; maxima were 0.169773,
0.071992, and 0.054834. Leverage-gain quartiles were SIFT
`[0, 0.008597, 0.051067]`, GloVe `[0, 0, 0.166860]`, and Arxiv
`[0, 0, 0.078567]`; maxima were 0.633300, 1.916425, and 0.738989. Every audited
exchange was at layer 0.

## C. Paired final-graph treatment strength

Frozen run: `phase2_gate0_retention_s7_v8`, code/config commit `150a0fe`. Two
independent indexes per dataset use identical data, insertion order, seed, `M=16`,
and `efConstruction=100`; one receives Geometry selections and the other GGR-0
selections. Only centers with a different terminal set are treated.

| Dataset | Proposed terminal edges | Actual new edges | Source retained | Reciprocal retained | Directed Jaccard | Support Jaccard |
|---|---:|---:|---:|---:|---:|---:|
| SIFT | 158 | 157 (99.37%) | 158/158 | 157/158 (99.37%) | 0.996045 | 0.996873 |
| GloVe-100 | 105 | 104 (99.05%) | 105/105 | 99/105 (94.29%) | 0.998532 | 0.999029 |
| Arxiv-Nomic | 108 | 108 (100%) | 108/108 | 106/108 (98.15%) | 0.997875 | 0.998430 |

The one or two terminal edges already present after reciprocal effects are reported as
non-effectual rather than counted as new treatment. No source edge was erased. Final
graphs remained one weak component. Relative Geometry-to-GGR changes were small:
reciprocal directed fraction changed by -0.000196/-0.000068/-0.000099; mean local
clustering by +0.000026/-0.000016/-0.000012; indegree Gini by
+0.000063/+0.000048/+0.000050 for SIFT/GloVe/Arxiv. Indegree maxima were unchanged
(54/96/88). Complete degree, indegree, reciprocity, component, clustering, and hubness
rows are in `topology.csv`.

The final run took 17.30 seconds including two builds per dataset, CSV export, and
Python topology analysis. Peak monitored C++ RSS was 36,855,808 bytes (SIFT),
33,456,128 bytes (GloVe), and 113,594,368 bytes (Arxiv); peak Python analysis RSS was
248,016,896 bytes. These are audit-process costs, not native in-build GGR overhead.

## D. Falsification status and next gate

- Tolerance artifact: falsified through `1e-9`.
- High-precision reversal: absent in the fixed Decimal-60 sample.
- Determinism: all final graph/treatment/topology CSVs reproduced byte-for-byte.
- Reverse-pruning erasure: falsified; reciprocal terminal retention is 94.29%–99.37%.
- Data leakage: no formal HDF5 member was read.
- Geometry-safe Random and Shuffled-Resistance controls: still required before Gate A.

Gate 0 therefore authorizes control implementation, not formal tests and not a claim
that resistance improves ANNS. Gate A may start only after both negative controls use
the identical feasible-swap and mutual-connection path.
