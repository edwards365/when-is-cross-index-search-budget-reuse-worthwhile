# P3 literature audit + theory derivation + conclusion optimization

## Theory derivation: which contract clause carries the guarantee

The ablation gives a mechanistic reading of the deterministic contract. Write the build as
a function of (data, order o, seed u, thread schedule sigma, toolchain tau):
index I = C(data, o, u, sigma, tau). The measured chain isolates each factor:

1. *Order* enters the neighbor-selection sequence directly: with random order the greedy
   pruning decisions depend on insertion order, so two random permutations produce
   structurally different graphs even with identical seeds. Canonical-order pinning
   removes exactly this variance component: measured -34.1pp / -32.4pp of response
   variation (68.3->34.1% / 63.2->30.8%), at build-time ratio 0.80x/0.93x - canonical
   order is not slower (better locality), so this clause is free.
2. *Seed* under multi-threaded hnswlib construction is nearly inert: -1.3pp/-4.3pp beyond
   order pinning, and the six D2 builds (fixed order, fixed seed, 8 threads) produce six
   DISTINCT serialized indexes. The reason is that hnswlib parallelizes level-assignment
   and neighbor searches with thread interleaving; the exposed seed does not parameterize
   the schedule. Formally, C(., o, u, sigma, tau) depends on sigma through a
   nondeterministic interleaving map that u does not control.
3. *Threads* are the load-bearing clause: pinning to one thread removes every remaining
   source (D3: 3/3 byte-identical, variation 0). The entire build overhead (3.52x/1.71x vs
   D0C; 4.73x/1.86x vs the pinned-parallel D2 tier) is the price of single-threading, not
   of order or seed pinning.

Corollary for the paper's contract wording: "fix the thread count" is insufficient as
stated; the sufficient registered condition is single-threaded construction (or an
implementation with a deterministic parallel schedule, which hnswlib does not expose).
This is a sharper, more useful statement than the current text.

## Literature audit

- Insertion-order sensitivity of HNSW: Elliott & Clark 2024 (currently unanchored) report
  order/recall effects - the D0C->D1 step quantifies the same factor at response level.
  ANCHOR SUGGESTION for Section 7.3 / Appendix F.
- Determinism of parallel index construction: no standard ANN library guarantees
  deterministic parallel builds; DiskANN/Vamana single-threaded registered runs in this
  project are consistent with that practice. The paper should state this as an
  implementation fact of hnswlib (version pinned in the artifact), not as a general
  theorem. No new citation needed; scope stays implementation-conditioned.
- The free-mitigation finding (canonical order) parallels practice in reproducible-build
  movements (fixed toolchains, canonical serialization); the paper can borrow the
  reproducible-builds framing in Related Work without new claims.

## Conclusion optimization (fed to P5)

1. Section 7.3 gains the ablation table (four tiers x two datasets) with the chain-design
   caveat, and the contract description is upgraded to name single-threading as the
   necessary-and-sufficient registered clause.
2. The prescription ordering from P2 gains a cheaper intermediate: canonical-order pinning
   halves response variation at zero build cost - useful when full determinism is
   unaffordable; it does not reach zero risk (34.1%/30.8% variation remains).
3. Limitations: the ablation is a chain, not a full factorial; effects are descriptive.
