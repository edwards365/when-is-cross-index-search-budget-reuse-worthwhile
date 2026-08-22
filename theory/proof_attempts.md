# Proof attempts

## Active attempts

- **Beam-retention lemma (`proof_sketch`).** Given a globally delta-progressing successor at each expanded state, add an explicit rank condition ensuring that successor remains in HNSW's result queue of size `efSearch` until expansion. Missing: a noncircular bound on the number of closer distractors.
- **Separated clusters (`proof_sketch`).** Candidate coverage plus a retained cross-cut edge proves a monotone path. Missing: query/entry mass and policy compatibility sufficient for greedy or beam discovery.
- **Kron localization (`conjecture`).** Hard-region terminal sets may admit small approximate Schur complements whose resistance rank errors are below observed greedy score margins. Missing: a data-dependent spectral approximation theorem and scalable construction.
- **Insertion stability (`proof_sketch`).** Theorem C handles a fixed ground set. Missing: a coupling that matches candidates across insertion orders and bounds candidate-set loss.
- **Resistance-to-navigation (`blocked`).** No proof can proceed from resistance alone because C1, C2, C7--C12 refute the required implication. Any resumed attempt must add candidate coverage, query alignment, and search-policy premises.
