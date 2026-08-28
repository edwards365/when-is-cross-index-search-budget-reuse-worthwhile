# ICBA Open-World Input Audit

## Frozen reproduction

- Frozen parent: `exp/icba_micro_closure@77e0d430bc04b819276b570a96eedb339a66c043`.
- New independent worktree/branch: `exp/icba_open_world_autopsy`.
- Parent worktree was clean; 123/123 frozen SHA256 entries verified.
- Located exactly 81 frozen graph files and 972,000 query-budget rows: 3 datasets × 3 implementations × 3 histories × 3 seeds × 1,000 queries × 12 budgets.
- The corresponding within-dataset/implementation directed source-target design contains 648 pairs (`9×8×9`).
- Frozen split is 256 labeled sentinels plus 744 disjoint evaluation queries per dataset; membership is unchanged.
- Frozen decision reproduces `CLOSED_WORLD_ONLY_NOT_OPEN_WORLD_PORTABLE`.
- `validation-dev` and `formal-test` remain sealed and were not accessed.

## Denominators and labels

Endpoint failure is Recall@10 below 0.9 at a named budget. Under-budget means an allocated budget is smaller than the target stable sufficient budget; it is identifiable only for uncensored queries. Right-censored target queries are failures only in the explicitly conservative analysis, not point-identified stable-budget labels. Query-risk denominators are evaluation queries within a target graph; build-level reliability uses distinct target builds, never 972,000 rows or 648 dependent pairs as independent environments.

Closed-world candidate sets include the target graph. Open-world leave-one-build-out removes the target graph hash from its same-dataset/implementation environment library before nearest sentinel matching. The frozen replay confirms `target_in_set=false` for every open-world row.

## Information channels

The previous successful closed-world lane uses `target_sentinel_stable_budget`, which requires labeled target Recall over the complete budget grid, plus `stable_sufficient_budget` for each source query, which is a per-query source Oracle. It is not deployable. No frozen deployable source policy exists (`DEPLOYABLE_SOURCE_POLICY_ABSENT`).

Potentially deployable frozen observations are limited to declared dataset/implementation/build metadata and native runtime outputs such as NDC, returned IDs and (where recorded) returned-distance/latency/entry-point statistics. The compact Faiss/Vamana schema lacks several of these fields. Visited/frontier/prefix trajectory statistics are not present in this 81-graph evidence and are `UNLABELED_FINGERPRINT_NOT_AVAILABLE` for the common cross-implementation analysis.

## Integrity decision

`GATE_A_INPUT_INTEGRITY_PASS`. The audit authorizes derived analysis only. It does not authorize rebuilding indexes, rerunning searches, training a new policy, accessing sealed splits or treating labeled/Oracle fields as deployment observations.
