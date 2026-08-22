# Reading cards: ANN construction, collisions, and benchmarks

The ten fields in every card are object, assumptions, result, mechanism, complexity, HNSW relation, transferability, missing conditions, verification level, and action.

## k-Diverse Nearest Neighbor Graph

1. Object: diversified k-NN graph. 2. Assumptions: vector distances and angular direction comparisons. 3. Result: an MMR-style rule trades proximity for directional diversity. 4. Mechanism: sequential relevance-minus-redundancy selection. 5. Complexity: candidate scoring overhead; exact bound not imported. 6. HNSW relation: close empirical predecessor to our direction term. 7. Transfer: motivates direction logging, not resistance. 8. Missing: submodular formulation, electrical model, and query guarantee. 9. Verification: official AAAI page and primary PDF text. 10. Action: compare its direction statistic as an ablation.

## FlatNav

1. Object: flat/compact HNSW implementation and hub structure. 2. Assumptions: evaluated systems and datasets. 3. Result: high-in-degree hubs empirically form a frequently used highway. 4. Mechanism: trace/in-degree analysis and systems layout. 5. Complexity: empirical latency/memory results. 6. HNSW relation: direct. 7. Transfer: motivates hub and trace diagnostics. 8. Missing: theorem connecting leverage to hub usage. 9. Verification: full primary arXiv PDF. 10. Action: log in-degree and visited-edge frequency separately from resistance.

## Impact of Insertion Order on HNSW

1. Object: HNSW graphs under reordered insertions. 2. Assumptions: selected datasets, orderings, and fixed parameters. 3. Result: recall can move by up to the reported 12 percentage points and correlates with local intrinsic dimension. 4. Mechanism: empirical construction perturbation. 5. Complexity: standard construction/search measurements. 6. HNSW relation: direct. 7. Transfer: insertion order is a required experimental factor. 8. Missing: a universal stability theorem. 9. Verification: full primary arXiv PDF and DOI metadata. 10. Action: retain order seeds and top-two score gaps.

## VIBE

1. Object: vector-index benchmark across modern embeddings. 2. Assumptions: 22 implementations and the paper's in-/out-of-distribution datasets/protocol. 3. Result: broad empirical comparison across 11 ID and 8 OOD datasets. 4. Mechanism: standardized build/search evaluation. 5. Complexity: measured build, memory, latency, and recall. 6. HNSW relation: benchmark baseline. 7. Transfer: dataset/metric coverage and reporting structure. 8. Missing: exact reproduction resources for this repo's current CPU budget. 9. Verification: full primary arXiv PDF. 10. Action: treat VIBE compatibility as a later external-validity tier.

## Graph Vector Index Evaluation

1. Object: experimental comparison of graph vector indexes. 2. Assumptions: twelve methods, seven real datasets, paper tuning protocol, and stated hardware. 3. Result: evaluation up to one billion vectors plus a five-paradigm design taxonomy. 4. Mechanism: controlled systems benchmark. 5. Complexity: measured indexing/search time, memory, and distance calculations. 6. HNSW relation: direct baseline context. 7. Transfer: reporting categories, controls, and design taxonomy. 8. Missing: exact reproduction on this repo's smaller Windows/16-GiB tier. 9. Verification: full author preprint corresponding to DOI 10.1145/3709693. 10. Action: use its diversification and seed-selection controls in the external-validity tier.
