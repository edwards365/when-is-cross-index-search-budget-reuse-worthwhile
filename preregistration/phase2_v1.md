# Phase II preregistration v1

Status: **frozen design; formal test firewall sealed**

## Confirmatory question

After query-independent geometric navigation quality is protected, can frozen local
effective-resistance leverage act as a secondary structural objective that improves
stability across construction seeds and insertion orders without materially harming
Recall or mean search cost?

The primary comparison is **GGR minus Geometry-only**. Comparisons with Original are
necessary baselines but cannot establish a resistance-specific effect.

## Algorithms

Only five methods enter the confirmatory comparison:

1. Original HNSW;
2. Geometry-only;
3. Resistance-only;
4. Geometry-Guarded Resistance Selection (GGR), the single primary method;
5. a random degree-preserving control.

Trace+Resistance and ordinary weighted mixtures are Phase I diagnostics and are
excluded from parameter selection and the confirmatory decision.

Geometry-only is the existing deterministic greedy selector with `alpha=0`,
`beta=1`, `gamma=1`, `sigma=0.5`, and node-local `rho` equal to the median positive
center-to-candidate distance. It maximizes the marginal gain of

`log det(I + sigma^-2 sum z_e z_e^T) + sum exp(-(d_e/rho)^2)`.

GGR begins from exactly that Geometry-only set. Candidate Scheme-A leverage values
are computed once on the explicitly augmented, union-symmetrized local reference
graph and remain frozen during selection. Deterministically ordered one-for-one
swaps are accepted only if the total frozen leverage improves by more than the
registered numerical tolerance and the complete set retains at least
`(1-epsilon) F_geo(S_geo)`. The algorithm stops at local optimality or the fixed
round cap. It preserves each outgoing list size and therefore total directed edge
budget. Queries, query traces, failure labels, and ground truth are absent from its
API.

Reverse pruning and reciprocal-link effects are not covered by the local theorem;
they will be logged separately when the selector is integrated into HNSW.

## Epsilon and development amendment

The only confirmatory structural tolerance candidates are `0`, `0.005`, and `0.01`.
They may be compared using development queries only. The choice rule is lexicographic:

1. reject any value whose development Recall is more than `0.001` below Geometry;
2. among the remainder, require an improvement larger than run-to-run noise in either
   matched-Recall mean NDC or cross-build variance;
3. choose the smallest epsilon satisfying that condition;
4. if no difference is clear, choose `epsilon=0`.

The numerical objective tolerance is initially `1e-12` in float64 and may only be
increased on synthetic correctness cases if a recorded conditioning failure requires
it. The exchange cap is `M * (|C_u| - M)` accepted swaps per node; deterministic
strict leverage improvement also guarantees finite termination.

The selected main epsilon will be recorded in a signed development-only amendment
with its own hash and commit before the first formal test access. Other epsilon values
may subsequently appear only as labelled exploratory ablations.

## Data and isolation

Core public datasets are SIFT1M (Euclidean), GloVe-100 (angular/cosine), and VIBE
Arxiv-Nomic (angular/cosine). On the detected 15.6 GiB Tier-0 machine, development
starts at 10K and may proceed to 100K. Full 1M multi-seed execution is deferred to
adequate hardware. Dataset manifests must record source, license, checksum, counts,
dimension, metric, query count, ground truth, preprocessing, and normalization.

Construction vectors build the graph and local reference graphs. Development queries
are restricted to correctness checks, epsilon selection, numerical tolerance, and
runtime budgeting. Formal test queries are opened once for the frozen evaluation and
never influence candidates, weights, subsets, metrics, or code. Detailed controls are
in `test_firewall.md`.

## Construction design

- `M=16`; `efConstruction=100`.
- Construction seeds: `7, 17, 29, 43, 61`.
- Orders: seeded random permutation and deterministic approximate-LID ascending.
- Approximate LID uses construction vectors only, `k=20`, the standard maximum-
  likelihood distance-ratio estimate, finite values first, then original row id as
  tie-breaker. No query or class label is used.
- Core work finishes before exploratory `M in {8,32}`, `efConstruction=200`, extra
  seeds, or graph perturbations.
- Each paired method uses identical vectors, seed, order, candidate pool, `M`,
  `efConstruction`, threads, hardware, and build mode.

## Search and outcomes

The frozen `efSearch` grid is `10, 20, 40, 80, 120, 200, 400`. It may be expanded
only through a pre-test amendment if development data show it cannot reach the target.
The primary matched-Recall target is `R0=0.95`; `R1=0.99` is secondary.

At matched Recall report mean, P95, and P99 distance computations; mean, P95, and P99
latency; and visited nodes. Stability outcomes are cross-build variance of matched-
Recall cost and Recall@10, worst-build cost, worst regret relative to Geometry, edge
Jaccard, SCC/WCC counts, indegree, hubness, reciprocity, cross-cluster edge fraction,
and high-leverage retention. Leverage-weighted graph distance is reported only after
recomputing leverage on a common frozen union reference graph.

Inference uses a hierarchical paired bootstrap: the outer resampling unit is the
`seed x insertion-order` build cluster and queries are paired-resampled within each
selected cluster. Report mean and relative differences, 95% intervals, per-dataset
and pooled summaries, and build/query variance components. Query-only intervals on a
single graph are descriptive and not confirmatory.

## Frozen Go/No-Go decision

Performance Go requires GGR versus Geometry to reduce matched-Recall mean NDC by at
least 3%, or P95/P99 NDC by at least 5%; the direction must agree on at least two
public datasets and at least 80% of builds; Recall loss must be at most `0.001`; real
latency must improve; and build overhead must be acceptable or plausibly optimizable.

Stability Go may apply without a mean-performance gain if cross-build cost variance
falls at least 20%, worst-build cost falls at least 10%, or preregistered post-Core
perturbation Recall degradation falls at least 20%; the direction must agree on at
least two datasets; mean query cost may rise at most 2%; and Recall loss must be at
most `0.001`.

No-Go ends the resistance-performance route if GGR cannot exceed Geometry, effects
remain about 0.2--0.5%, occur on only one dataset or isolated seeds, trade Recall for
tiny NDC changes, cost too much to build, do not improve stability, are explained by
Geometry, require query/trace leakage, or require post-test epsilon/subset changes.
Negative results remain part of the project record.

## Formal-test gate

Formal evaluation is prohibited until this design and firewall are hashed and
committed, the development-only epsilon amendment is hashed and committed, public
artifact checksums are verified, and the implementation/test suite passes. This v1
does not claim that any Phase II public-data experiment has run.
