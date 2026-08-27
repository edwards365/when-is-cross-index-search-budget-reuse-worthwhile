# Endpoint Feasibility and Gate E0

## Frozen audit

The compact streaming audit covers all 81 frozen Cross-Index graphs (three datasets, three implementations, three histories and three seeds), 1,000 design queries per graph and the twelve preregistered budgets. All 81 files have a complete budget grid and protocol-consistent successful rows. No new graph, query, truth or search result was generated.

Safety is Recall@10 at least 0.9 with marginal query risk at most `delta_q=0.05`. A budget is called certifiably safe only when the one-sided 95% Clopper--Pearson upper bound on its failure probability is at most 0.05. Stable sufficiency uses the complete observed upper-budget tail. Failure at the maximum observed ef=512 is treated as right censoring, never as evidence that a larger endpoint would fail.

## Results

Across all implementations, 54/81 graphs are `CURRENT_ENDPOINT_CERTIFIABLY_SAFE`, 17/81 are `GRID_RIGHT_CENSORED`, and 10/81 are `NO_PRACTICAL_SAFE_ENDPOINT`; no graph is incomplete or protocol-inconsistent.

| Implementation | Dataset | Safe graphs | Right-censored | No practical endpoint | ef=512 empirical failure range | Certified endpoint |
|---|---:|---:|---:|---:|---:|---:|
| hnswlib | SIFT-100K | 9/9 | 0 | 0 | 0--0.002 | 64 |
| hnswlib | Arxiv-Nomic-100K | 9/9 | 0 | 0 | 0 | 48 or 64 |
| hnswlib | GloVe-100K | 0/9 | 4 | 5 | 0.045--0.055 | none |
| Faiss HNSW | SIFT-100K | 9/9 | 0 | 0 | 0 | 64 |
| Faiss HNSW | Arxiv-Nomic-100K | 9/9 | 0 | 0 | 0 | 48 |
| Faiss HNSW | GloVe-100K | 0/9 | 7 | 2 | 0.050--0.065 | none |
| Vamana | SIFT-100K | 9/9 | 0 | 0 | 0 | 48 |
| Vamana | Arxiv-Nomic-100K | 9/9 | 0 | 0 | 0 | 32 or 48 |
| Vamana | GloVe-100K | 0/9 | 6 | 3 | 0.049--0.053 | none |

## Gate decision

`GATE_E0_PASS_WITH_DATASET_BOUNDARY`.

hnswlib has a certifiably safe endpoint on two of three datasets (SIFT and Arxiv), meeting the preregistered minimum for continuing the theoretical and synthetic closure. GloVe has no certifiable endpoint on any hnswlib graph and therefore cannot participate in a deployable safe-policy claim without redefining the problem or extending the frozen budget grid, neither of which is allowed here. The same GloVe boundary occurs for Faiss HNSW and Vamana, so it is not evidence of an hnswlib-only instrumentation defect.

The result authorizes Phase 2 theory work, not Graph-ANNS replay. Replay remains conditional on Gates G1 and G2. Query-level failure Parquet was not materialized because exact free disk remained below the 10 GiB resource threshold; the compact graph-level CSV is sufficient for Gate E0 and preserves every graph-level count, interval and endpoint label.
