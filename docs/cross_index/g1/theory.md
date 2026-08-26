# Cross-Index G1 theory boundary

For fixed data, implementation, parameters, and construction history, `B_tau(q;I,h)` is the first frozen search-budget point attaining Recall@10 >= tau at that point and every larger frozen point; failure at the endpoint is right-censored. This is inherited rather than redefined.

**THEOREM.** On any finite declared history set, a strictly history-blind sufficient allocation is at least `max_h B_tau(q;I,h)`. Under nondecreasing cost, this maximum is the pointwise minimum safe blind allocation.

**PROPOSITION.** A global multiplier can explain cross-history transfer only if budget ratios are sufficiently concentrated; rank inversions and positive residual interaction variance falsify pure global scaling on the observed histories, not on every possible graph.

**EMPIRICAL CLAIM G1.** Faiss HNSW reproduces within-family history-dependent budget reshaping on at least two datasets under the frozen gate.

**EMPIRICAL CLAIM G2.** Official Vamana reproduces construction-dependent safety cost on at least two datasets under separately controlled or explicitly compound histories.

**BOUNDARY.** Failure to expose behavior-preserving exact NDC is instrumentation inconclusiveness, not evidence that Vamana lacks the mechanism. Cross-family absolute NDC is not interpreted because implementations and budget semantics differ.
