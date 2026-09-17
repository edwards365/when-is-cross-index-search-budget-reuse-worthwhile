# S3 — Unchanged-Data Source-Policy Bridge

## Evidence boundary

S3 freezes a source-only fixed-action selector and replays it on unchanged-data target builds. The within-analysis roles are disjoint (375 source-certification, 94 unused bridge-holdout, and 281 target-evaluation queries, seed 991), and target outcomes never select an action. However, all 750 response rows were inspected in prior project stages. The correct evidence label is therefore `POST_HOC_ROLE_LIMITED`, not prospective confirmation or independent certification.

Each source build selects the lowest native fixed action whose one-sided Clopper–Pearson UCB passes 5% under a six-action Bonferroni allocation. If no action qualifies, it falls back to the endpoint. The frozen source action and its +1/+2 grid shifts are then replayed on every other build.

## Main results

| Operator | Dataset | Source-selected action pattern | Target risk +0 (95% query-bootstrap CI) | +1 | +2 | Endpoint | Legal cost observation |
|---|---|---|---:|---:|---:|---:|---|
| hnswlib | SIFT-100K | 23/24 endpoint; 1/24 at 120 | 0.369% [0.100, 0.751]% | 0.237% | 0.237% | 0.237% | +0 mean NDC 2,204.9 vs endpoint 2,234.3 |
| hnswlib | Arxiv-Nomic-100K | 24/24 endpoint | 1.349% [0.415, 2.491]% | 1.349% | 1.349% | 1.349% | no saving: mean NDC 2,447.4 in every lane |
| Faiss HNSW | SIFT-100K | 4/24 at 128; 20/24 at 256 | 0.972% [0.459, 1.635]% | 0.141% | 0.059% | 0.059% | cumulative NDC not estimable |
| Faiss HNSW | Arxiv-Nomic-100K | 14/24 at 128; 10/24 at 256 | 1.581% [0.770, 2.581]% | 0.426% | 0.089% | 0.089% | cumulative NDC not estimable |

All 24 source builds qualify under the registered source-side rule, but hnswlib qualification is almost entirely achieved at the endpoint. For hnswlib SIFT, the one non-endpoint source policy reduces mean NDC by only 1.3% relative to endpoint and leaves 12/552 target pairs indeterminate under the descriptive evaluation interval; +1 becomes the endpoint and all 552 pairs qualify. Arxiv offers no non-endpoint source policy at all. Faiss shows a cleaner fixed-action bridge—+1/+2 progressively reduce risk—but the frozen batch cube cannot establish cumulative work savings, so this cannot be presented as an efficiency win.

## Interpretation

The executable source-policy bridge passes its semantic Gate: the action family is native, source-only, fixed before target evaluation, and reproducible from registered IDs. Scientifically, the result is deliberately sobering. Strict simultaneous source qualification largely collapses hnswlib to fixed-safe endpoint behavior; therefore it does not close an economically useful unchanged-data recovery result. Faiss supplies directional mechanism evidence but lacks legal NDC accounting. This phase supports ICBA's distinction between safe executability and deployable value, while leaving the latter unresolved for a source-only policy.

S3 must not be used to claim fresh confirmation. It does justify proceeding to the S4 feasibility Gate: determine whether unused query IDs and a replay interface can provide genuinely fresh risk and legal per-query cost without new graph construction.
