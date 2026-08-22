# Mathematical claim-boundary report

## Proved in this repository

- The weighted cut-space projector, leverage normalization/Foster identity, bridge equivalence, Rayleigh local upper bound, common-kernel spectral resistance stability, regularized direction-logdet submodularity, frozen DLS greedy factor, rank-one insertion/deletion formulas, exact terminal Kron preservation, score-gap selection, fixed-ground-set greedy stability, cross-cut path concatenation, and the pure-greedy delta-progress bound.
- Each `proved` YAML entry records dependencies, the original/imported statement it rests on, and its precise algorithm relation.

## Imported and verified from primary text

- HNSW Algorithm 4; Spielman--Srivastava projection/sparsification; exact/approximate Schur results of Durfee et al.; navigability definitions and bounds; the cited worst-case ANN theorems; DABS's theorem in its own model; the stochastic-greedy factor; and the empirical findings explicitly labeled as such in the reading cards.

## Imported but not fully verified

- Directed Kron theorem labels/hypotheses and the complete Graph Vector Index Evaluation text. Only official abstract/landing-page facts are used. No project theorem depends on them.

## Empirical support only

- Hub-highway behavior, insertion-order sensitivity, modern projection/collision speedups, VIBE benchmark breadth, and every recall/NDC effect of the current repair. The aggressive repair smoke run is negative: replacing 45.3% of directed edges did not dominate baseline and required larger `efSearch` for the recall target.

## Disproved

- High resistance implies navigation utility; low resistance is safely removable; spectral similarity preserves adjacency navigation; a hop-local graph controls global rankings; the explicit dynamic-leverage sum is submodular; the local greedy factor transfers to reciprocal/global HNSW; and an existing monotone path guarantees HNSW discovery.

## Conjectural or blocked

- A small approximate terminal Schur complement can preserve useful score ranks on hard regions (`conjecture`).
- Resistance-direction repair guarantees better HNSW recall or logarithmic query cost (`conjecture`, presently unsupported).
- Resistance alone can imply ANN navigation (`blocked` by explicit counterexamples).

## Safe one-sentence project claim

The method is a degree-limited local selector that combines rigorously normalized nonredundancy on an explicitly symmetrized reference graph with a monotone-submodular direction/locality objective; its current guarantee is local-objective approximation, while ANN benefit remains an empirical question requiring candidate coverage, query alignment, and beam-retention evidence.
