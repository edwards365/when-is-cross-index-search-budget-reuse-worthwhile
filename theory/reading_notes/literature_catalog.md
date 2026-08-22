# Required-paper verification catalog

This table supplies the citation/review-status fields; the mathematical cards named in the last column supply definitions, assumptions, results, proof tools, transfer, missing conditions, and collision analysis. “Peer reviewed” follows the venue/DOI metadata; arXiv-only items are marked preprint even when current metadata reports a later acceptance.

| # | Work / stable identifier | Status | Verification | Detailed card |
|---:|---|---|---|---|
| 1 | Malkov & Yashunin, *Efficient and Robust ANN Search Using HNSW*, TPAMI, DOI 10.1109/TPAMI.2018.2889473 | peer reviewed | full primary PDF | `hnsw.md`, `hnsw_algorithm4.md` |
| 2 | *Fast ANN Search via k-Diverse Nearest Neighbor Graph*, AAAI 2018, DOI 10.1609/aaai.v32i1.12138 | peer reviewed | official page/PDF text | `ann_collision_and_benchmarks.md` |
| 3 | Indyk & Xu, *Worst-case Performance of Popular ANN Implementations*, NeurIPS 2023 | peer reviewed | full primary PDF | `worst_case_ann_2023.md` |
| 4 | Diwan et al., *Navigable Graphs for High-Dimensional NNS*, NeurIPS 2024 | peer reviewed | full primary PDF | `navigable_graphs_2024.md` |
| 5 | *Graph-Based Vector Search: An Experimental Evaluation of the State-of-the-Art*, DOI 10.1145/3709693 | peer reviewed | full author preprint | `ann_collision_and_benchmarks.md` |
| 6 | *Down with the Hierarchy / FlatNav*, arXiv:2412.01940 | preprint | full primary PDF | `ann_collision_and_benchmarks.md` |
| 7 | Al-Jazzazi et al., *DABS*, NeurIPS 2025 | peer reviewed | full proceedings PDF | `query_guarantees.md` |
| 8 | *A Theoretical Analysis of NNS on Approximate Near Neighbor Graph*, arXiv:2303.06210 | preprint | full primary PDF | `query_guarantees.md` |
| 9 | Elliott & Clark, insertion order/LID, arXiv:2405.17813; related DOI 10.1145/3664190.3672512 | peer reviewed version linked | full primary PDF | `ann_collision_and_benchmarks.md` |
| 10 | Spielman & Srivastava, *Graph Sparsification by Effective Resistances*, DOI 10.1137/080734029 | peer reviewed | full primary PDF | `resistance_sparsification.md`, `spectral_algorithms.md` |
| 11 | Spielman & Teng, *Spectral Sparsification of Graphs*, DOI 10.1137/08074489X | peer reviewed | primary metadata/abstract | `spectral_algorithms.md` |
| 12 | Sugiyama & Sato, *Kron Reduction and Effective Resistance of Directed Graphs*, DOI 10.1137/22M1480823 | peer reviewed | official abstract only | `spectral_algorithms.md` |
| 13 | Yang & Tang, *Efficient Estimation of Pairwise Effective Resistance*, DOI 10.1145/3588696 | peer reviewed | full author preprint | `spectral_algorithms.md` |
| 14 | Durfee et al., *Sampling Random Spanning Trees Faster than Matrix Multiplication*, arXiv:1611.07451 | peer-reviewed version not asserted here | full primary PDF | `spectral_algorithms.md` |
| 15 | Nemhauser, Wolsey & Fisher, *Submodular Set Functions—I*, DOI 10.1007/BF01588971 | peer reviewed | theorem known; full primary PDF not retrieved in this batch | `submodular_logdet.md` |
| 16 | Krause, Singh & Guestrin, *Near-Optimal Sensor Placements in GPs*, JMLR 9 (2008) | peer reviewed | full primary PDF | `submodular_logdet.md` |
| 17 | Mirzasoleiman et al., *Lazier Than Lazy Greedy*, AAAI 2015, DOI 10.1609/aaai.v29i1.9486 | peer reviewed | official full text | `submodular_logdet.md` |
| 18 | Zhao, *MCGI*, arXiv:2601.01930 | preprint | full primary PDF | `modern_projection_collision.md` |
| 19 | *pHNSW*, arXiv:2602.19242 | preprint | full primary PDF | `modern_projection_collision.md` |
| 20 | *Projection-Augmented Graph*, arXiv:2603.06660 | arXiv; metadata reports ICML 2026 poster | full primary PDF | `modern_projection_collision.md` |
| 21 | *VIBE*, arXiv:2505.17810 | preprint | full primary PDF | `ann_collision_and_benchmarks.md` |

No theorem is marked `imported_verified` merely from an abstract. Item 12 and the exact NWF theorem numbering remain explicit verification debt.
