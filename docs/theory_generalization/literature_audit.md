# Targeted literature and naming audit

The working title **Information-Constrained Budget Adaptation (ICBA)** produced no exact-title collision in the targeted scholarly search performed on 2026-08-27. This is not a trademark search. The name remains a working title.

The reviewed Graph-ANNS and adaptive-ANN literature establishes graph construction/search mechanisms and query-dependent budget prediction. The decision-theory literature already establishes that more informative experiments can weakly improve attainable decision risk, so ICBA must not claim that generic value-of-information ordering is new. Conformal risk-control and Learn-then-Test literature already separates predictive scoring from finite-sample certification. ICBA's defensible positioning is the specialization and integration of these ideas for **index-instance-conditioned budget portability**, together with frozen multi-build evidence and computable safe-envelope/rank-inversion quantities.

Within the reviewed scope, no paper was found that jointly studies an old per-query ANN budget policy transported across rebuilt index instances, derives a source-summary safe envelope and monotone inversion lower bound, treats risk relaxation and censoring, and tests the boundary across hnswlib, Faiss HNSW and Vamana. Therefore all novelty language must use: “To our knowledge, under the reviewed literature scope...”

The audit is targeted rather than exhaustive. Verified sources are recorded in `verified_references.csv`; nearby claims and required narrowing are recorded in `novelty_matrix.csv`. Unverified references are excluded from the formal bibliography.

## Coverage matrix

| Direction | Object studied in prior work | Relationship to ICBA | Rebuild portability covered? | Claim consequence |
|---|---|---|---|---|
| HNSW | Navigable small-world construction and efSearch | Supplies one concrete budgeted-search mechanism | No controlled old-policy→rebuilt-index analysis found | Mechanism is prior; portability framing is qualified |
| Vamana/DiskANN | Degree-bounded graph construction and beam/search-list budget | Tests whether the phenomenon is graph-algorithm-specific | No direct per-query rebuild-transfer theorem found | Use as boundary evidence, not actionable cross-method proof |
| Faiss/IVF/HNSW | Library and inverted-file/HNSW search budgets | Establishes alternative implementation and budget families | No matching frozen-policy portability result verified | No novelty claim about Faiss itself; IVF pilot was skipped |
| Query-adaptive ANN / per-query ef | Static/runtime prediction of query effort | Closest algorithmic neighbor to source or target feature policies | Explicit index-instance rebuilding was not identified in reviewed sources | Claim only the rebuild-conditioned specialization/integration |
| Early termination / anytime search | Dynamic stopping or limited adaptivity | Closest neighbor to target-native filtration policies | No reviewed work jointly supplies the ICBA envelope, censoring, and complete-policy certificate | T8 is a class separation, not an algorithm novelty claim |
| Construction order/seed | Index-build randomness and structural variability | Candidate mechanism for budget reordering | Existing mechanisms do not by themselves establish policy transfer tax | Frozen controlled evidence is the project contribution |
| Blackwell/statistical decision theory | Comparison of experiments and value of information | Direct ancestor of T1 | Not ANN-specific | Never claim generic information ordering as new |
| Sufficient statistics/information refinement | Lossless or coarsened decision information | Interprets source-summary aliasing | Not rebuild-specific | T2 is an ANN-budget specialization of established decision logic |
| Isotonic/order-restricted inference | Monotone fits under statistical loss | Mathematical neighbor to T3 | No rebuild-specific safe majorant found | Stress hard-majorant rather than regression distinction |
| Rank/Kendall/ranking regret | Pair inversions and ranking error | Neighbor to T4 | Exact safe-budget matching result not found | T4 remains a narrowed proof sketch; no broad first claim |
| Conformal risk control / Learn-then-Test | Finite-sample loss control and multiplicity | Supplies certification vocabulary and methods | Not specific to rebuilt ANN policies | Certification theory is prior; power calculation and integration are applications |
| Selective classification | Coverage-risk tradeoffs under abstention | Conceptual neighbor to stopping/continue decisions | No direct index-rebuild portability result reviewed | Do not claim risk–coverage concepts as new |
| Optimal stopping / stopping times | Policies adapted to growing filtrations | Mathematical basis for T8 | Not specific to HNSW state and rebuild portability | T8 identifies the escape interface, not a new stopping algorithm |
| Right censoring/survival analysis | Partial observation beyond a horizon | Motivates conservative frozen-grid handling | ANN budget censoring treatment not found in reviewed set | Use standard censoring language; do not claim survival theory novelty |

## Direct novelty questions

1. **Is query difficulty already defined as index-instance-conditioned?** Query-adaptive ANN is established, but the reviewed primary sources did not explicitly make a rebuilt index instance the conditioning environment and test transported policies across controlled rebuilds.
2. **Has an old per-query budget policy been analyzed after graph rebuilding?** No directly matching theorem-plus-controlled experiment was located in the targeted set.
3. **Has rank inversion been converted into safe-budget regret?** General order and ranking tools exist; the exact narrowed matching construction was not located. This supports only a combination/specialization claim, especially while T4 remains a proof sketch.
4. **Is there a risk-certified HNSW-state stopping rule already?** Adaptive search and risk-control literatures exist separately. No reviewed source jointly matched resumable target-native HNSW state, full-policy fallback accounting, rebuild portability, and finite-family certification.

## Verification limits

The 12 entries in `verified_references.csv` were verified against primary paper, publisher, conference, DOI, or arXiv pages. Directions for which no additional primary citation was uniquely verified in the time box are covered as conceptual neighbors but are not added to the formal bibliography. This audit is sufficient for a qualified positioning statement, not for an unrestricted priority claim or systematic-review claim.
