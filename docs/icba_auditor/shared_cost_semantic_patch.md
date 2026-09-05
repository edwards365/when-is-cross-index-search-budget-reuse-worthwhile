# ICBA Unified Certified Auditor — retrospective closure

This audit starts from `exp/icba_shared_frontier_cost_realizability@9b2f18ae9936aac1624d46676b3c498ac04e6dea` and keeps all earlier CALS, BN-APD, and shared-cost artifacts read-only. The historical limitation remains exactly `LEGACY_BASELINE_CONDITIONALLY_REPRODUCED: 111/123 matched, 8 mismatched, 4 untracked __pycache__ entries`.

The shared-cost semantic patch is retrospective: action-level quality qualification is used rather than per-query filtering; practical and strong failure events are Recall@10 < 0.90 and < 0.99; zero and negative critical coefficients are retained; candidate cost is the incremental candidate set relative to the primary candidate set; and mean/median summaries use matching bootstrap statistics. Earlier outputs are preserved and the repaired outputs are separate.

ICBA-Auditor v1 has seven frozen actions: REUSE_SOURCE_POLICY, CONSERVATIVE_REUSE, TARGET_RECALIBRATION, TARGET_REPROFILE_OR_RETRAIN, FIXED_SAFE_FALLBACK, REJECT_NO_SAFE_ENDPOINT, and INSUFFICIENT_EVIDENCE. No serialized source policy or frozen training pipeline is present, so source reuse and full retraining real costs are NOT_ESTIMABLE; target fixed-ef profiling is the only measurable retrospective proxy.

The replay is fixed-target and retrospective only. Endpoint-aware event is `Recall@10 < 0.99 OR no practical safe endpoint`; CP certification is reported separately from post-hoc evaluation diagnostics. Missing independent logs, true wall-clock, and future-confirm queries remain NOT_ESTIMABLE. The lexicographic order is endpoint feasibility, safety, p95/p99 tail, finite break-even, total cost, decision regret, then complexity.

Final retrospective status: `ICBA_UNIFIED_METHOD_NOT_READY_FOR_PROSPECTIVE_CONFIRMATION`. No future-confirm or sealed role was accessed. This is a method-readiness closure, not an open-world impossibility claim.
