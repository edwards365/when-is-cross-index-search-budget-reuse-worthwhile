# ICBA Vamana–HNSW theory delta: executive summary

## Decision

`READY_WITH_CONDITIONAL_VAMANA_SEMANTIC_BRIDGE`

The finite-environment/finite-action ICBA objects transfer to Vamana, but raw parameters and costs do not. The pilot is authorized only after a deterministic replay preflight at the frozen Microsoft DiskANN3 commit `8fb4d42e6a8bff0cff4db976a55c5fb99faaf475`. The primary Vamana action is `Knn::l_value` with `beam_width=1`; in-memory and SSD modes are different cost regimes.

No reviewed paper simultaneously covers independent Vamana rebuilds, build-specific safe budgets, source-to-target budget transport, censoring, one-sided under-budget risk, conservative cost, held-out target builds, fixed-target certification, and data-by-operator interaction. The defensible statement is `NO_DIRECT_PRIOR_FOUND_WITHIN_REVIEWED_SCOPE`, not a priority claim.

## Semantic correction

With the raw definition

\[
B_G(q)=\min\{a:Z_G(q,a)=0\},
\]

the requested list containing `UNDER_BUDGET_OBSERVED_SAFE` and omitting `OVER_BUDGET_UNSAFE` is not exhaustive when raw recall is nonmonotone. The locked primary partition is:

1. three censoring classes;
2. `UNDER_BUDGET_UNSAFE`;
3. `EXACT_BUDGET_SAFE`;
4. `OVER_BUDGET_SAFE`;
5. `OVER_BUDGET_UNSAFE`.

`RAW_NONMONOTONE` is a diagnostic flag, not a mutually exclusive transport class. No monotone envelope is used to certify raw actions.

## Theory disposition

- T-V1, T-V3, T-V4, T-V5, T-V7 and T-V8 are complete restricted propositions or definitions.
- T-V2 is a complete counterexample-based non-equivalence proposition.
- T-V6 is complete only after the event-partition correction above; the original requested eight-label partition is refuted.
- The pair-symmetry identity holds only for finite, jointly feasible minimal budgets over complete reverse pairs. H2 is principally an algebraic decomposition of H1 in that design.

The strongest retained contribution is a Graph-ANNS-specific combination: algorithm-native rebuild environments, raw finite action grids, endpoint-aware transport, asymmetric held-out builds, and preregistered data-by-operator interpretation. It is not a new generic lower bound or a proof of Graph-ANNS universality.

## Access discipline

No ANN build/search was run. No validation-dev, formal-test, evaluation vectors/truth, or future-replication vectors/truth were accessed.
