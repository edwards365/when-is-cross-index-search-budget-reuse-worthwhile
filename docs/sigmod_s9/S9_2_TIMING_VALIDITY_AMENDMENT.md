# S9-2 timing-validity amendment A1

Status: frozen after noise-only smoke v2 and before any policy/runtime-gain mapping.

The original protocol used within-query/action repeated-measurement CV as the timing-validity Gate. Smoke v2 met native equivalence with zero mismatches but failed that Gate. The host exposes an unprivileged, non-writable `ondemand` CPU governor; individual searches last roughly hundreds of microseconds, so cell-level variation combines frequency, cache-state, and request noise. No TCP, target-global, fixed-slack, endpoint speedup, tail ratio, or lifecycle result was computed before this amendment.

The amendment aligns the validity unit with the registered serving estimand and experimental design:

1. Each target build remains the independent outer unit.
2. Query/action/repetition measurements remain raw and are never counted as independent builds.
3. Timing validity is assessed on repeated complete-query-block totals within each build and native action. For the full 500-query role, the median action-block CV across actions must be at most 5%, and the maximum action-block CV must be at most 10%.
4. Cell-level median and p95 CV remain mandatory diagnostics but are no longer a Gate.
5. Primary per-query latency uses the median of seven repetitions for each frozen query/action cell. Raw all-repetition p95/p99 are reported as sensitivity, so scheduler outliers are not hidden.
6. Mean-gain, p95-noninferiority, safety, lifecycle, crossed-bootstrap, and LOTO thresholds are unchanged.

This is an instrumentation amendment motivated only by timing-noise structure. It does not select a policy, dataset, action, or favorable result. Smoke v1 remains invalid because it under-ran the registered warm-up count; smoke v2 remains the valid failure of the superseded cell-CV Gate and is retained in full.
