# Literature matrix

| Work | Primary contribution | Relation to OCGT-v2 | Novelty implication |
|---|---|---|---|
| Malkov & Yashunin, *Efficient and robust approximate nearest neighbor search using HNSW* (https://arxiv.org/abs/1603.09320) | Defines hierarchical NSW construction and search | Establishes randomized hierarchy and incremental construction mechanisms | OCGT-v2 does not claim a new HNSW algorithm |
| Aumüller & Ceccarello, *The Role of Local Intrinsic Dimensionality in Benchmarking NNS* (https://arxiv.org/abs/1907.07387) | Connects LID to query-set difficulty | Motivates the static LID baseline | Query difficulty itself is not novel; graph-instance conditionality is the narrower hypothesis |
| He et al., *On the Difficulty of Nearest Neighbor Search* (https://arxiv.org/abs/1206.6411) | Introduces Relative Contrast as a difficulty measure | Motivates query-only geometry features | Static geometry baselines are prior art |
| Zhang & Miller, *Distribution-Aware Exploration for Adaptive HNSW Search* (https://arxiv.org/abs/2512.06636) | Proposes adaptive per-query ef selection | Closest adaptive-search direction found | Any future algorithm claim must differentiate construction-history transfer and fully charge probe cost |
| nmslib/hnswlib official implementation (https://github.com/nmslib/hnswlib) | Reference implementation and parameter semantics | Code base used by this project | Implementation behavior is not a new contribution |

## Novelty assessment

A defensible contribution would be a controlled measurement of how HNSW construction history changes per-query sufficient budgets and breaks cross-index transfer. The present run cannot establish that claim confirmatorily because its reproduction and raw-schema gates were not completed before performance collection.
