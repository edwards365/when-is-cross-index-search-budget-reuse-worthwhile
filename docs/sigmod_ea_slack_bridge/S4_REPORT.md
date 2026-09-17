# S4 Fresh-Query Confirmation and Cost Closure

## Status

`COMPLETE_FRESH_QUERY_CONFIRMATION`; S5 is not authorized or started.

The preregistration was committed before any future-replication vector or truth access. For each dataset, 1,000 previously untouched query IDs were split in frozen list order into 500 source-certification and 500 target-evaluation queries with zero overlap. Existing 24 hnswlib and 24 Faiss HNSW indexes per dataset were replayed; no graph was built or changed.

## Measurement repair

The first Faiss replay exposed a runtime-interface error: in the frozen Faiss 1.8.0 ABI, HNSW distance computations are accumulated into the legacy `n3` member, while `ndis` remains zero. A one-query diagnostic showed `n3=398` and `ndis=0`. The reader was corrected to select the positive version-specific counter and fail closed if neither is populated. The invalid first-pass files were isolated, never used in the final analysis, and the full Faiss replay was regenerated. All final per-query NDC values are positive.

## Fresh-query results

All percentages below use the 500 untouched target-evaluation queries, preserve each query's complete 552 directed-build-pair vector in the 5,000-replicate seed-991 bootstrap, and are conditional on the 24 registered builds.

| Implementation | Dataset | Lane | Target risk (95% CI) | Qualified / indeterminate / above-delta pairs | Mean-NDC saving vs endpoint (95% CI) | Source fallbacks |
|---|---|---:|---:|---:|---:|---:|
| hnswlib | SIFT-100K | +0 | 1.487% [0.845, 2.260] | 543 / 9 / 0 | 1.313% [1.307, 1.319] | 0 |
| hnswlib | Arxiv-Nomic-100K | +0 | 1.317% [0.600, 2.158] | 552 / 0 / 0 | 0.000% [0.000, 0.000] | 0 |
| Faiss HNSW | SIFT-100K | +0 | 1.297% [0.852, 1.865] | 478 / 74 / 0 | 53.806% [53.758, 53.855] | 0 |
| Faiss HNSW | Arxiv-Nomic-100K | +0 | 1.724% [1.097, 2.474] | 528 / 24 / 0 | 58.210% [58.165, 58.255] | 2 |
| Faiss HNSW | SIFT-100K | +1 | 0.183% [0.083, 0.316] | 552 / 0 / 0 | 8.274% [8.266, 8.283] | 0 |
| Faiss HNSW | Arxiv-Nomic-100K | +1 | 0.674% [0.280, 1.211] | 552 / 0 / 0 | 29.095% [29.063, 29.127] | 0 |

The +2 lane coincides with the endpoint in both implementations and datasets. Every lane's aggregate risk interval is below 5%, but pairwise three-state status is retained: +0 has 9 indeterminate hnswlib/SIFT pairs, 74 Faiss/SIFT pairs, and 24 Faiss/Arxiv pairs; none is confidently above delta. The Faiss +1 lane is the clean fixed bridge: all 552 pairs qualify on both datasets, mean-NDC savings are positive with bootstrap lower bounds above zero, p95/p99 are below endpoint, and LOBO savings remain positive (6.48–8.63% on SIFT; 28.19–30.36% on Arxiv). Deleting the largest-risk 1% of queries leaves risk below 0.25% on both datasets.

## Interpretation

Fresh data support a deployable, source-certified one-rung slack bridge for the registered Faiss HNSW family. They do not support a universal economic bridge: hnswlib +1 collapses to the endpoint, while +0 yields only 1.31% saving on SIFT and none on Arxiv. Thus S4 strengthens the paper's conditional-method story without licensing a cross-implementation SOTA claim. Stable-tail remains a retrospective truth-dependent diagnostic and was not used for deployment.

Wall-clock remains `WALL_CLOCK_EXPLORATORY_ONLY`; all primary cost claims use legal per-query distance computations. The 24-build scope and query-level bootstrap do not constitute open-world or independently replicated evidence.

## Verification

- 96/96 frozen index hashes matched.
- Final raw cubes: 48 hnswlib + 48 Faiss files, 6,000 rows each.
- Five unit tests pass.
- 210/210 validation checks pass after the frozen-runtime counter correction.
- No validation-dev, formal-test, W6 edit, target-evaluation tuning, new graph construction, or stable-tail deployment occurred.
