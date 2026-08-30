# hnswlib semantic audit

## Version and provenance

- Project freeze: `dca81b23ce3cfe7ca95e3b3362fb3129cf24f937`.
- Submodule: `third_party/hnswlib` at `3f3429661187e4c24a490a0f148fc6bc89042b3d`.
- Lock record: hnswlib `v0.8.0`; `environment.yml` also pins Python package `hnswlib==0.8.0`.
- Upstream source audited: `hnswlib/hnswalg.h`, especially `HierarchicalNSW::searchKnn` and `searchBaseLayerST`; `hnswlib/hnswlib.h`; Python binding and build scripts.
- Project implementation audited: `cpp/include/narhnsw/hnsw_query_tracer.hpp` and `cpp/src/hnsw_gate_a_benchmark.cpp`.

The project C++ benchmark instantiates `HierarchicalNSW<float>` with either squared-L2 or inner-product distance and executes one query at a time. Its construction loop inserts points sequentially. CMake fixes C++17 but does not freeze optimization flags, compiler version, CPU feature set, or `NO_MANUAL_VECTORIZATION`; the exact deployed SIMD path is therefore `NOT_ESTIMABLE` from the repository. The separately built Python wheel normally uses `-O3 -march=native -fopenmp`, but that does not establish the flags of the C++ benchmark.

## Search control flow

`searchKnn` performs greedy descent from `enterpoint_node_` through upper layers. At each upper-layer node it evaluates all neighbors and moves only when `d < curdist`. It then calls

```text
searchBaseLayerST(currObj, query, max(ef_, k), filter)
```

At the base layer:

- `top_candidates` retains at most `ef` admissible result candidates;
- `candidate_set` is a separate min-priority frontier and has no `ef` capacity bound;
- a node is marked visited before its distance is evaluated and before admission is decided;
- admission is `top_size < ef || lowerBound > distance` in ordinary search;
- once over capacity, the farthest `top_candidates` item is removed and `lowerBound` is updated;
- bare-bone search stops when the nearest frontier distance is greater than `lowerBound`;
- the deletion/filter path additionally requires `top_candidates.size()==ef` when no custom stop condition is present;
- final output trims `top_candidates` to `k`.

Thus an `ef=1` descending chain can expand every node. The semantic check gives five expansions at `ef=1`; the construction generalizes to arbitrary chain length.

## Tie semantics

Upper descent uses strict `<`. Candidate admission uses strict `lowerBound > distance`. `CompareByFirst` compares only the distance component; equal-distance items are comparator-equivalent, with no explicit label tie token. A frozen binary/toolchain and insertion order can replay a tie deterministically, but the source does not define a portable total order. Any theorem requiring fixed ties must add an explicit composite priority `(distance, tie_token)` to instrumentation and either enforce it or abstain on ties.

The finite witness `0 -> {2,1}` with equal keys shows why this matters. At `ef=1`, the first equal candidate can fill the heap and the second is rejected; at `ef=2`, both are admitted and a permitted tie order can expand/output the other identity first. Therefore universal prefix equivalence and raw Recall monotonicity are false without a tie assumption.

## Deletion and filtering

When there are no deleted nodes and no filter, `searchKnn` selects the faster bare-bone template. Otherwise, a filtered/deleted entry may seed the candidate queue without entering the result heap, and admission/output checks differ. The current project tracer models only the no-deletion/no-filter path. A pilot using filters/deletions must either extend the tracer and certificate or be declared out of scope.

## Existing instrumentation

`HnswQueryTracer` independently mirrors the upper and base algorithms and records entry/evaluated/improved/enqueued/pruned/expanded events, source and target IDs, distance key, lower bound before the event, result size, upper/base evaluations and base expansions. `hnsw_gate_a_benchmark` uses a counting distance function and asserts final traced output equals upstream `searchKnn` for every measured query.

This is strong implementation evidence, but it does not yet emit heap contents, candidate-set snapshots, explicit stop reason, tie events, filter/deletion state, checkpoint top-k, or first-safe discovery. The pilot extension is specified in `observability_report.md`.

## Answers to the ten required questions

1. `ef` is retained-result capacity plus an admission/stopping parameter, not an expansion limit.
2. A larger `ef` is not universally guaranteed to contain the smaller run's expansion sequence as a strict prefix; equal-key behavior is a finite counterexample.
3. Independent runs do not reuse state.
4. Prefix equivalence is conditional at best (fixed graph/entry/numerics, total tie order, no filters/deletions); it is not an API guarantee.
5. Raw Recall nondecrease is not licensed universally; a tied-result counterexample exists.
6. Top-k identity can change and Recall against a tie-resolved truth set can decrease.
7. No deterministic Lipschitz relation from `ef` to NDC exists without graph-degree/frontier bounds.
8. One priority intruder means one extra prefix pop only under the T-SC5 machine; it need not change the global capacity threshold by one.
9. T-SC5's `s` is an expansion-prefix delay.
10. Grid rounding remains valid on an expansion grid, not on the `ef` grid absent a bridge.

## Audit conclusion

`HNSWLIB_IMPLEMENTATION_NOT_AUDITABLE` is not triggered. `ACTION_SEMANTICS_MISMATCH_REDEFINE_BUDGET` is resolved by splitting the theorem into an expansion-prefix theorem and an empirical fixed-`ef` interface. The bridge status is `IMPLEMENTATION_BRIDGE_NOT_PROVED`.
