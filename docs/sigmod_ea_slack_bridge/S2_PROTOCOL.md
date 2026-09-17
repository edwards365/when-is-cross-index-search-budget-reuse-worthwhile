# S2 Frozen Protocol — Theory and Certification Semantics

Registered after S1 commit `3e393038f509db46d8acaa219d1fc5edcf6b75ed` and before producing S2 result tables.

## Fixed inputs

- The same 96 frozen hnswlib and Faiss HNSW response files registered in S1.
- The same four operator–dataset settings, 24 builds, 750 query IDs, action grids, risk event `Recall@10 < 0.95`, and S1 action rules.
- No new ANN search, index construction, query split, target-specific tuning, or W6 edit.

## Registered analysis

1. Distinguish the first-passing index from the stable-tail index. The latter is the least action whose entire observed suffix passes; neither is called a native-`ef` guarantee.
2. For every directed source–target build pair, query, and registered action lane, verify the finite-grid implication: if the target stable-tail index is finite and the executed action is at least that index, then the target response at that action passes.
3. Report exact target failure count `k`, sample size `n`, and one-sided Clopper–Pearson lower and upper bounds. Classify a policy as:
   - `QUALIFIED` when the upper bound is at most `delta=0.05`;
   - `CONFIDENTLY_ABOVE_DELTA` when the lower bound is greater than `delta`;
   - `INDETERMINATE` otherwise.
4. Report two fixed error allocations for every target without target-specific changes:
   - single-policy analysis with `alpha=0.05`;
   - candidate-plus-endpoint family analysis with `alpha_candidate=0.025` and `alpha_endpoint=0.025`.
5. Output per-pair and aggregate three-state counts, source/target failures, stable-tail gap events, and the finite-grid implication audit.
6. Include executable counterexamples showing that first-passing need not be stable-tail and that failure of an upper-bound qualification test does not prove risk above `delta`.

## Registered theoretical status vocabulary

Only `PROVED_UNDER_STATED_ASSUMPTIONS`, `CLASSICAL_APPLICATION`, `EMPIRICAL_CONTACT`, and `NOT_INSTANTIATED` may be used. The deterministic stable-tail implication is a finite-grid proposition; Clopper–Pearson is a classical application. No claim of a universal native-`ef` guarantee, new confidence-bound theorem, prospective validation, or independent-build certification is authorized.
