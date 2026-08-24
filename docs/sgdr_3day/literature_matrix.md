# SGDR compact primary-source literature matrix

This audit asks whether SGDR's proposed query-time, phase-gated additive edges collide
with an existing core contribution. Links are papers, publisher pages, author-hosted
manuscripts, or official repositories. `FATAL` means the same principal mechanism and
claim; broad overlap with query adaptation is not by itself fatal.

| Work | Index changed? | Query-time training / multi-graph | Decision granularity and guarantee | Cost / scale | Relation to SGDR | Collision |
|---|---|---|---|---|---|---|
| [Original HNSW](https://arxiv.org/abs/1603.09320) | Yes: hierarchical proximity graph | No / no | Fixed best-first traversal; empirical recall–speed tradeoff, no pointwise guarantee | Multi-layer graph and distance calls; large benchmark evaluation | SGDR retains HNSW as the immutable backbone | None; baseline |
| [GATE](https://arxiv.org/abs/2506.15986) | Adds a high-tier hub/navigation graph | Offline contrastive two-tower / auxiliary graph | Query-specific entry point among hubs; no exact recall guarantee | Learned inference plus small navigation graph; reported 1.2–2.0× speed-up | Query-aware routing and auxiliary topology overlap broadly, but GATE changes entry selection rather than conditionally expanding additive layer-0 edges | `RELATED`, not fatal |
| [GAAF](https://doi.org/10.1145/3797905.3807855) | Builds a frequency-aware graph ensemble | No query training / yes | Label-frequency partition and adaptive inter-graph pruning for Any-Match filtered ANNS | Multiple graphs, NUMA-aware placement; filtered-search workloads | Multi-graph and pruning language overlaps only superficially; query semantics and problem definition differ | None |
| [Ada-ef](https://arxiv.org/abs/2512.06636) / [official code](https://github.com/chaozhang-cs/hnsw-ada-ef) | No | Statistical model, update-friendly / no | Per-query `efSearch` chosen to approximately meet declarative recall | Model scoring; million-scale real embeddings; reports up to 4× latency improvement | Same query heterogeneity motivation, but adapts global exploration width rather than edge family by search phase | `RELATED`, not fatal |
| [DARTH](https://helios2.mi.parisdescartes.fr/~themisp/publications/sigmod26-darth.pdf) | No | Learned/estimated termination / no | Runtime early termination for declarative recall | Online prediction and search-state features | Controls when search stops; SGDR proposed which adjacency family to inspect | `RELATED`, not fatal |
| [Learned Adaptive Early Termination](https://github.com/efficient/faiss-learned-termination) | No | Offline GBDT / no | Per-query stopping from static and intermediate runtime features; empirical accuracy target | Model inference; million-to-billion-scale datasets; reported up to 7.1× | Strong overlap in query-adaptive search-state decisions, but not additive edge gating | `RELATED`, not fatal |
| [PEOs](https://arxiv.org/abs/2402.11354) | No | No / no | Per-neighbor probabilistic routing decides which exact distances to compute; probabilistic guarantee | LSH-like screening; HNSW/NSSG; reported 1.6–2.5× throughput | Closest overlap in neighbor-level conditional work, but PEOs filters existing neighbors and SGDR proposed extra neighbors selected by scale/depth | `RELATED`, not fatal |
| [CRouting](https://arxiv.org/abs/2509.00365) / [official code](https://github.com/ISCS-ZJU/CRouting) | No | No / no | Angle-distribution routing bypasses distance calls; empirical recall–efficiency | HNSW/NSG; up to 41.5% fewer calls | Both alter query-time neighbor work; CRouting prunes existing computations rather than injects additive graph edges | `RELATED`, not fatal |
| [Graph-based NNS: Practice to Theory](https://proceedings.mlr.press/v119/prokhorenkova20a.html) | Abstract graph models | No / no | Analyzes greedy search, shortcut edges, and dynamic candidate lists under restricted regimes | Theoretical low-dimensional setting | Directly relevant warning: shortcut utility depends on search regime and does not establish HNSW finite-beam monotonicity | None; theoretical context |
| [ANN-graph theory](https://arxiv.org/abs/2303.06210) | Approximate near-neighbor graph model | No / no | Greedy-search guarantees for low-dimensional/dense-vector assumptions | Theory rather than production HNSW | Shows guarantees require explicit structural/distributional assumptions absent from SGDR's empirical graphs | None; theoretical context |
| [Certify-then-Rectify HNSW](https://arxiv.org/abs/2607.02338) | Wraps HNSW; exact recovery path | Statistical certifier / no | Query-level certification then exact rectification, targeting correctness | Certifier plus potentially expensive exact recovery; benchmark study | Shares safe/fallback framing, but provides certification and exact escalation rather than heuristic delta navigation | `RELATED`, not fatal |
| [MESS multi-graph HNSW](https://arxiv.org/abs/2607.28999) | Multi-graph HNSW | Workload-specific / yes | Private semantic-search multi-graph routing | Additional graph/storage overhead | Broad auxiliary-graph overlap; application, privacy objective, and routing structure differ | None based on available primary description |

## Judgment

No reviewed work is a `FATAL` one-to-one novelty collision with the exact SGDR proposal.
However, the surrounding space is crowded: GATE covers query-aware auxiliary routing,
Ada-ef/DARTH/LAET cover per-query adaptive effort, and PEOs/CRouting cover conditional
neighbor distance work. A positive SGDR paper would therefore need evidence that
phase-gated *additive* adjacency is causally distinct and better than these simpler
adaptive-search alternatives. Gate O failed before such a claim became supportable,
so the appropriate contribution is the audited negative boundary, not a new-algorithm
novelty claim.
