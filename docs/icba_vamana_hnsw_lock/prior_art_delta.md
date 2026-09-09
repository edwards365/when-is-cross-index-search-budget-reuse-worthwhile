# Directed prior-art delta

## Review result

`NO_DIRECT_PRIOR_FOUND_WITHIN_REVIEWED_SCOPE`

Ten highest-risk full texts and two implementation/current-construction sources were checked. DiskANN and FreshDiskANN define Vamana-family construction/search; HNSW, NSG and Faiss establish different graph and action semantics; Indyk–Xu and Gollapudi et al. give worst-case graph/search guarantees; Elliott et al. directly establish insertion-order sensitivity for HNSW. None of these supplies the nine-part ICBA transport object.

## What is already known

- Vamana/RobustPrune, HNSW and NSG are established algorithms.
- Search-list/beam parameters and graph-dependent search trajectories are established.
- Worst-case reachability and approximation analysis for DiskANN-family graphs is established.
- HNSW insertion order can materially affect recall.
- Dynamic and filtered DiskANN variants are established.

## Remaining delta

The remaining domain-specific combination is: treat a replayable build instance as a registered environment; define a per-query endpoint-aware safe action with explicit censoring; transport that action from preregistered source builds to disjoint targets; separate one-sided unsafe under-budget risk from conservative cost; and interpret the effect through a data-by-operator table.

This delta is a protocol/problem combination, not a new graph-construction theorem. It does not justify “first”, open-world impossibility, or all-Graph-ANNS scope.

## Evidence levels

Level A means the full paper was available and its relevant definitions, algorithms, formal claims and experimental protocol were checked. Level B means relevant sections/code were checked but not every proof or appendix. No abstract-only item supports the decision.
