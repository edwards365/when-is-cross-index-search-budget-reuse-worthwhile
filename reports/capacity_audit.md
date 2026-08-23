# GB-MPCC capacity audit

Scope: query-independent T0 audit over `train[:100000]` only. Formal HDF5
`test`, `neighbors`, and `distances` were not accessed. Exact 32-nearest base
neighbors are a pre-replay proxy candidate pool, not claimed to equal HNSW's
insertion-time Algorithm 4 pool.

| Dataset | LID | Scale | Local-d UB | Ambient-d UB | Empirical | Local-PCA | Ambient MC |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| sift_100k | 12.94 | near | 0.8214 | 0.0003 | 0.9575 | 0.1048 | 0.0000 |
| sift_100k | 12.94 | medium | 1.0000 | 0.1315 | 1.0000 | 0.6642 | 0.0755 |
| sift_100k | 12.94 | far | 1.0000 | 0.9559 | 1.0000 | 0.9474 | 0.5811 |
| glove100_100k | 36.11 | near | 0.0595 | 0.0001 | 0.8673 | 0.0059 | 0.0000 |
| glove100_100k | 36.11 | medium | 0.8740 | 0.2127 | 1.0000 | 0.4377 | 0.1056 |
| glove100_100k | 36.11 | far | 1.0000 | 0.9924 | 1.0000 | 0.9488 | 0.6140 |
| arxiv_nomic_100k | 26.47 | near | 0.1996 | 0.0000 | 0.8952 | 0.0029 | 0.0000 |
| arxiv_nomic_100k | 26.47 | medium | 0.9850 | 0.0000 | 1.0000 | 0.3746 | 0.0000 |
| arxiv_nomic_100k | 26.47 | far | 1.0000 | 0.0183 | 1.0000 | 0.9342 | 0.0132 |

Frozen T0 capacity status: **QUERY_INDEPENDENT_CAPACITY_NONDEGENERATE_ON_AT_LEAST_TWO_DATASETS**.

`Local-d UB` uses rounded estimated LID; `Ambient-d UB` matches the ambient
isotropic Monte Carlo model. The 0.05/0.95 interval and isotropic 0.05 stop
threshold were fixed before this run. Capacity cannot establish Algorithm 4 difference,
proxy transfer to routing states, or search performance.
