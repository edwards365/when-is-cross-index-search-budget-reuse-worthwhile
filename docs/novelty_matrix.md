# GB-MPCC novelty matrix

Audit date: 2026-08-24. Sources are original papers, proceedings pages, author
preprints, or official code/paper pages. “Threat” means overlap with the narrow
working claim, not a judgment of paper quality. Preprints and technical reports are
marked as such and do not establish peer-reviewed priority.

The claim under audit is deliberately narrow:

> During HNSW construction, use a query-independent, original-space exact one-step
> progress condition to define length-aware multi-scale direction coverage; maximize
> its incremental coverage in a few slots beyond a frozen geometry backbone, with a
> local submodular guarantee and explicit proxy-distribution mismatch bounds.

| Work | Graph / stage | Query-independent? | Geometry used | Length / query-radius ratio? | Guarantee | Overlap and difference from GB-MPCC | Threat |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [HNSW, Malkov & Yashunin](https://arxiv.org/abs/1603.09320) | Hierarchical proximity graph; online construction and search | Construction yes | Algorithm 4 relative-neighborhood occlusion; length-aware angle diversity | Edge-length ratios appear implicitly in the occlusion inequality, but no future-query radius distribution | Conditional Delaunay/scale discussion; no distribution-free practical Recall theorem | Closest structural baseline. It already rejects angularly redundant neighbors. It does not optimize the union of exact future-query progress caps across radii or freeze a backbone for submodular slot selection. | **High** |
| [NSW, Malkov et al.](https://doi.org/10.1016/j.is.2013.10.006) | Incremental navigable small-world graph; construction/search | Construction yes | Proximity plus long/short links | No explicit edge/query-radius progress cap | Small-world motivation, primarily empirical | Foundational navigation mechanism; lacks hierarchy-specific local coverage objective and proxy-distribution analysis. | Medium |
| [NSG, Fu et al.](http://www.vldb.org/pvldb/vol12/p461-fu.pdf) | MRNG-like graph construction and connectivity repair | Yes | RNG-style geometric pruning and monotonic-search motivation | Length comparisons, not a multi-scale future-query radius distribution | Monotonic-search motivation under graph assumptions | Strong geometry baseline and potential explanatory substitute. It does not maximize weighted progress-cap union coverage beyond a fixed HNSW backbone. | **High** |
| [DiskANN/Vamana, Subramanya et al.](https://proceedings.neurips.cc/paper/2019/hash/09853c7fb1d3f8ee67a61b6bf4a7f8e6-Abstract.html) | Degree-bounded Vamana graph; construction/pruning plus SSD search | Yes | Alpha robust pruning balances proximity and diversity | Alpha-scaled distance comparisons, not edge length divided by modeled query radius | System/design analysis and empirical scaling | RobustPrune is a mandatory strong pruning baseline. No exact one-step query-direction cap coverage or local submodular backbone objective. | **High** |
| [NN-Descent, Dong et al.](https://doi.org/10.1145/1963405.1963487) | Approximate k-NN graph construction | Yes | Neighbor-of-neighbor locality | No | Empirical convergence behavior; not GB-MPCC’s local guarantee | Candidate generation/construction predecessor, not a directional coverage selector. | Low |
| [k-Diverse NN graph](https://ojs.aaai.org/index.php/AAAI/article/view/12138) | Diversified k-NN graph construction | Yes | MMR-style proximity and direction redundancy | Direction/length tradeoff, but no frozen query-radius state distribution | Empirical objective | Direct prior art for angular diversification; makes any generic “first direction diversity” claim invalid. Exact progress-cap union and frozen-backbone submodularity remain distinct. | **High** |
| [Graph-based NNS: From Practice to Theory, Prokhorenkova & Shekhovtsov](https://proceedings.mlr.press/v119/prokhorenkova20a.html) | Analysis of greedy/beam search on near-neighbor graphs with shortcuts | Graph model yes | Uniform-sphere geometry and spherical-cap intersection analysis | Search scale enters asymptotics, not a per-node construction distribution over (s/r) | Rigorous conditional search bounds in dense/low-dimensional regimes | Important collision in spherical-cap language and routing theory. It analyzes prescribed random graph models rather than using exact progress caps as an HNSW neighbor-selection objective. | **High** |
| [Navigable Graphs: Constructions and Limits, Diwan et al.](https://proceedings.neurips.cc/paper_files/paper/2024/hash/6dc63b4063c978cf195bc15178e8152a-Abstract-Conference.html) | Universal greedy-navigable graph construction/lower bounds | Yes | Greedy distance decrease to a data-point target | Exact target progress, but not a probabilistic query-radius local cap objective | (O(\sqrt{n\log n})) average-degree construction and near-(\sqrt n) lower bound in (O(\log n)) dimensions | Establishes that strong universal navigability can require far more than HNSW’s constant degree. GB-MPCC optimizes a local distributional proxy and must not claim universal navigability. | **High boundary** |
| [Probabilistic Routing / PEOs, Lu et al.](https://proceedings.mlr.press/v235/lu24l.html) | Query-stage neighbor filtering/routing on an existing graph | No; query-dependent | Locality-sensitive probabilistic tests before exact distance evaluation | Query-specific routing probability, not frozen construction (s/r) states | Probabilistic routing guarantee | Strong collision on “routing probability,” but it changes query execution rather than graph construction and does not select edges by submodular progress coverage. | Medium |
| [Learning to Route in Similarity Graphs, Baranchuk et al.](https://proceedings.mlr.press/v97/baranchuk19a.html) | Learned query-stage routing policy | No; trained on query/target labels | Learned hop-to-target probabilities/features | Learned query relation, not exact length/radius cap | Probabilistic learning objective, empirical ANN results | Demonstrates that routing distributions can be learned when query leakage is allowed. GB-MPCC explicitly forbids such labels in construction. | Medium |
| [HNSW insertion order and LID, Elliott & Clark](https://arxiv.org/abs/2405.17813) | HNSW construction-order intervention and diagnosis | Yes for ordering | Local intrinsic dimensionality | No cap ratio | Empirical sensitivity | Makes insertion order/LID mandatory robustness factors. It does not define an edge coverage objective. | Medium |
| [CSPG, Yang et al.](https://proceedings.neurips.cc/paper_files/paper/2024/hash/bab1486cec466c980b40e7d633dd4bbc-Abstract-Conference.html) | Randomly partitioned sparse proximity graphs plus routing vectors; construction and two-stage search | Construction mostly yes; search query-dependent | Partition proximity graphs and cross-partition routers | No local edge/query-radius cap | Expected exploration analysis for its framework | Changes global graph decomposition and query staging, not HNSW local neighbor selection. | Low |
| [MCGI, Zhao](https://arxiv.org/abs/2601.01930) (2026 preprint) | Disk-resident graph indexing; construction-time pruning and query-time beam adaptation | Construction component yes; search component query-state dependent | LID/manifold-consistent geometry, adaptive pruning and beam | Uses LID/local geometry; audited text contains no same exact progress-cap union objective | Claimed manifold/topology and approximation results in preprint | Closest recent manifold/LID threat. It invalidates broad “first LID/manifold-aware graph construction” claims, but no same frozen backbone, exact (s/(2r)) cap coverage, or submodular objective was found. | **High; monitor** |
| [Aperon HNTL, Fu](https://arxiv.org/abs/2606.08813) (2026 technical report) | Pointerless tangent-local grains and sequential scans; index/search | Index yes; routing query-dependent | Local PCA/tangent spaces and quantization | No progress cap | Systems measurements; technical-report scope | Invalidates broad “first local-PCA/tangent ANN” claims. It abandons proximity edges and does not select HNSW neighbors. | Medium |

## Audit decision

No screened work uses the same combination of (i) HNSW construction-time edge
selection, (ii) exact original-space one-step progress caps parameterized by edge
length/query-radius ratio, (iii) a frozen query-independent multi-scale state
distribution, and (iv) cardinality-constrained incremental submodular coverage beyond
a mandatory geometry backbone. The T0 novelty condition is therefore
**provisionally satisfied**, not a claim of absolute priority.

The largest threats are HNSW/NSG/Vamana/k-Diverse for length-aware geometric
diversity, Prokhorenkova–Shekhovtsov for spherical-cap routing analysis, and MCGI for
recent LID/manifold-aware construction. Accordingly, prohibited claims include
“first use of spherical caps,” “first direction-diverse ANN graph,” “first local-PCA
ANN,” “first LID-aware graph index,” and “first probabilistic routing.”

The permitted working description is the narrow claim quoted at the top. It must be
withdrawn if R0 reveals effective equivalence to Algorithm 4/LengthAware-Angle, or if
a later full-text/version update reveals the same objective, constraint, and build
stage.
