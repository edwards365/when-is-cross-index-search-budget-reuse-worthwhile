# GSC operator cards (smoke scope)

* **O4 — Response-Weighted Robust Pruning.** Domain-specific combination;
  graph-only proposal/validation API.  Preserves per-node degree and forbids
  self-loops.  The smoke validates these invariants on a 256-node fixture, but
  no HNSW replay is available, so no response claim is made.
* **O6 — Response-Aware Insertion Schedule.** Domain-specific combination;
  bounded deterministic prefix reorder driven by proposal-query response
  scores.  The smoke replays four registered profiles in hnswlib on SIFT-10K.
  It does not use certification or evaluation feedback.

Both cards are exploratory and do not claim novelty beyond the registered
mechanism family.
