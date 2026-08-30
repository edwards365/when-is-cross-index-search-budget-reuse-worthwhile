# ICBA Stable-by-Construction semantic closure gate

## Final decision

`READY_WITH_THEOREM_DOWNGRADE_EMPIRICAL_BRIDGE`

No checked Level-A paper satisfies all four direct-prior conditions. The pinned hnswlib implementation is auditable, the four work units are separable, and all required trace fields are obtainable with a project-side tracer extension. However, the central implementation bridge is not proved: the restricted T-SC5 expansion-prefix result does not directly control native hnswlib `ef`.

## Gate results

| Gate | Result | Basis |
|---|---|---|
| L — literature | PASS WITH CLAIM NARROWING | 10 Level-A full texts; no four-condition direct prior |
| U — units | PASS | requested `ef`, retained-heap capacity, expansions, NDC, and time defined separately |
| H — source semantics | PASS | pinned hnswlib `3f342966...` / v0.8.0; `searchKnn` and `searchBaseLayerST` audited |
| B — implementation bridge | DOWNGRADED | `IMPLEMENTATION_BRIDGE_NOT_PROVED`; Interface C selected |
| O — observability | CONDITIONAL PASS | 16/24 current; 24/24 obtainable after specified tracer extension |
| A — repair | CONDITIONAL PASS | frozen pseudocode interface; `PSEUDOCODE_ONLY` |
| P — protocol | PASS AS CONTRACT | four query roles must be pairwise disjoint; sealed sets not accessed |

## Correct semantic mapping

For a query `q`, requested action `e_req` is passed into the base-layer search through `max(ef_,k)`. It bounds the retained top-candidate heap under the implementation's admission/deletion/filter branches; it does not hard-cap the candidate queue, number of popped/expanded nodes, number of distance computations, or wall time. Every fixed-`ef` call starts a new visited list and recomputes state. With distance-only comparison, equal keys lack a portable total tie rule.

Define `B_G^ef(q)` as the smallest tested requested `ef` whose independent run meets the endpoint-aware success target. Define `B_G^exp(q)` only for a declared resumable deterministic prefix/checkpoint action. Their correlation is an empirical question; no universal map was proved.

## Theorem disposition

- **T-SC5.** Its disruption union bound remains formally complete but classical. Its search statement is `FORMAL_PROOF_RESTRICTED` for a deterministic expansion-prefix model with total tie order and fixed certificate semantics. The old native-`ef` interpretation is `THEOREM_INVALID_FOR_EF_ACTION` and deleted.
- **T-SC10.** The negative claim that generic overlap/local similarity cannot universally control budget response remains valid by finite counterexamples. A robust-certificate expansion surrogate is restricted; the native-`ef` relationship is `EMPIRICAL_CALIBRATION_ONLY`.
- **Upward closure.** It holds for a resumable best-so-far prefix envelope by construction, not for raw independent fixed-`ef` recall. The latter has a finite tie-sensitive counterexample.
- **Introduction edge.** It is not graph-intrinsic. The deployment certificate freezes the first successful candidate-queue insertion parent in the total event order.

## Semantic verification

Sixteen finite checks cover the twelve required cases plus visited-before-admission, `ef` versus NDC, `max(ef,k)`, and resumable-envelope closure. All checks passed. The stdlib unit suite contains six tests and passes. These tests validate semantics and counterexamples, not effectiveness or a general theorem.

## Novelty and method boundary

Delete “first stable/rebuild-portable ANNS,” “T-SC5 directly guarantees safe `ef`,” “edge overlap controls budget,” “one intruder costs one `ef`,” “raw fixed-`ef` recall is monotone,” and any generic new graph-search/concentration claim. Retain the narrow systems contribution: cross-build query-effort stability as a distinct objective; explicit action/work-unit separation; endpoint/right-censoring-aware budget response; a trace-certificate repair template; and a sealed empirical calibration/certification protocol.

## Frozen-data statement

No validation-dev, formal-test, evaluation truth, formal stable-build effect experiment, or frozen result was accessed or modified in this gate. The requested server worktree was not mounted; an isolated staging tree was used and the deliverables were committed to the dedicated GitHub branch.

