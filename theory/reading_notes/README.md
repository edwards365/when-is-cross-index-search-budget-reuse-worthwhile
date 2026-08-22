# Reading-card index

Cards distinguish a full method/theory read from abstract screening. `verified_primary` means that this batch checked an official proceedings/DOI page and the paper or author preprint; it does not mean every result in the paper has been reproduced.

| Work | Review status | Peer review | Immediate use |
|---|---|---:|---|
| HNSW (Malkov--Yashunin) | `verified_primary`, algorithm/theory sections read | yes | exact Algorithms 1--5 and limits of complexity discussion |
| Spielman--Srivastava resistance sparsification | `verified_primary`, theorem/projection sections read | yes | projector, leverage, spectral approximation |
| Nemhauser--Wolsey--Fisher 1978 | `verified_primary`, theorem statement checked | yes | local cardinality greedy factor |
| Krause--Singh--Guestrin 2008 | `verified_primary`, objective/theorem sections read | yes | submodular information/log-det context |
| Worst-case ANN implementations | `verified_primary`, theorem/experiment sections read | yes | prohibits universal practical-graph query bound |
| Navigable Graphs 2024 | `verified_primary`, definitions/main results read | yes | separates formal universal greedy navigability from HNSW heuristics |
| ANN graph theoretical analysis | `author_preprint_read` | no in cited version | conditional low-dimensional/dense graph guarantees |
| Distance-Adaptive Beam Search | `verified_primary`, definitions/main result read | yes (NeurIPS 2025) | search guarantee conditional on input graph navigability |

Queued for full cards in the next literature batch: k-Diverse NNG, SIGMOD 2025 experimental evaluation, FlatNav, Spielman--Teng, PACMMOD resistance estimation, directed Kron resistance, fast random spanning trees, Lazier Than Lazy Greedy, non-submodular greedy guarantees, MCGI, pHNSW, Projection-Augmented Graph, and VIBE. Existing screening metadata remains in `literature/related_work_matrix.csv`; none of these queued works is cited as theorem support in this batch.
