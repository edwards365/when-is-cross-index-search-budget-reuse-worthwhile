# Phase II counterexample obligations

1. **Guarded but unnavigable.** A fixed-cardinality set can retain the same local
   log-det/locality value while replacing the only edge that connects to the query's
   target basin. GGR's local guard therefore does not guarantee Recall.
2. **High-leverage detour.** A bridge in the local undirected reference graph has high
   leverage but can point away from all relevant progress cones. A positive epsilon
   can admit it while increasing NDC.
3. **Reference/final mismatch.** Union symmetrization can make a candidate edge look
   structurally critical although the directed final edge has no reciprocal path and
   is never traversed in the useful direction.
4. **Stable scores, unstable exposure.** Two insertion orders can expose different
   candidate pools even when the frozen scoring rule is perfectly stable on each
   pool. GGR cannot recover absent candidates.
5. **Near-tie discontinuity.** Arbitrarily small coordinate perturbations can reverse
   a zero-margin Geometry choice or a near-tied leverage swap, producing different
   graphs despite deterministic tie-breaking.
6. **Local gains, global hubness.** Independent swaps can repeatedly choose the same
   incoming vertex, preserving all outgoing degrees but increasing hubness and search
   congestion.
7. **Epsilon zero is not identity.** Distinct sets can be numerically or exactly tied
   under `F_geo`; GGR may change edges at epsilon zero. The guarantee is objective
   preservation within tolerance, not graph identity.

These families are proposed obligations until executable minimal instances are added.
They delimit any future empirical stability claim.
