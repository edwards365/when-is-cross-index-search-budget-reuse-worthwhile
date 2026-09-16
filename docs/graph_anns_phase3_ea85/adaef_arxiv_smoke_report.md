# Ada-ef Arxiv-100K One-Build Scientific Smoke

## Registered setup

The smoke uses the official Ada-ef core at commit `ed463f9993868f7ecc7c103920644e7f94abb377`, normalized Arxiv vectors, a 100K HNSW index, `M=16`, `efConstruction=500`, seed 991, and the primary event `Recall@10 < 0.95`. Query roles were frozen before execution and are disjoint: 2,000 design, 500 certification, and 1,000 evaluation queries. Evaluation was not accessed until the certification decision was frozen.

The build took 182.24 seconds and the offline adapter took 2.47 seconds. Ada-ef selected weighted-average `ef=10.475`; evaluation actions were ef 10 for 904 queries, ef 13 for 46, and ef 20 for 50. The fixed-safe comparator was ef 200.

## Independent certification

| Lane | Failures / 500 | Risk | One-sided 95% CP UCB | Mean distance computations | p95 distance computations |
|---|---:|---:|---:|---:|---:|
| Raw Ada-ef | 63 | 12.6% | 15.31% | 1,115.23 | 1,155.05 |
| Fixed-safe ef 200 | 6 | 1.2% | 2.35% | 2,633.25 | 3,347.10 |

Raw Ada-ef failed the registered 5% safety certificate. Fixed-safe passed, so the ICBA-audited deployment was frozen as fixed-safe ef 200 before evaluation was read.

## Sealed evaluation

| Lane | Failures / 1000 | Risk | Mean Recall@10 | Mean distance computations | p95 | p99 |
|---|---:|---:|---:|---:|---:|---:|
| Raw Ada-ef, diagnostic only | 95 | 9.5% | 0.9872 | 1,114.88 | 1,153.05 | 1,173.00 |
| Certified fixed-safe deployment | 6 | 0.6% | 0.9994 | 2,636.47 | 3,373.10 | 3,594.05 |

The raw method is substantially cheaper but misses the per-query safety target too often. ICBA prevents unsafe deployment by falling back; consequently, its efficiency gain relative to fixed-safe is zero in this build. This is a useful boundary result rather than evidence that Ada-ef is ineffective for its original average-recall objective.

## Gate decision

`SMOKE_PASS_SEMANTICALLY_VALID_EXTEND_TO_REGISTERED_MAIN`.

The smoke validates the metric, query firewall, official algorithm bridge, exact distance-computation counter, independent certification, and delayed evaluation access. It does not support outer-build inference. The next registered step is the three-build Arxiv main comparison. Euclidean SIFT remains `NOT_IMPLEMENTATION_SUPPORTED_UNDER_REGISTERED_METRIC` because the official Ada-ef estimator has no L2 implementation; it will not be silently converted to cosine.
