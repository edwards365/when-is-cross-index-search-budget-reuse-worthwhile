# Phase 5 Statistical and Economic Seal

## Frozen purpose

This phase integrates the already sealed Phase 1--4 evidence. It does not
select a new method, rerun a search matrix, or relax any prior gate. The
primary statistical unit remains the target build. Dataset-level estimates
are kept separate; pooled values are descriptive only when action semantics
are commensurate.

## Frozen inputs

- Phase 1 DARTH and Ada-ef build tables and decision manifest.
- Phase 2 mixed-refresh per-build table and decision manifest.
- Phase 3 Vamana per-target-build table and decision manifest.
- Phase 4 Deep1M per-target-build table, input ledger, and decision manifest.

Every input is recorded with SHA-256 before integration. No validation,
formal-test, certification-reserved, or evaluation-reserved role is accessed
outside the already sealed aggregate tables.

## Registered outputs

1. `evidence_inventory.csv`: one row per dataset/method/estimand.
2. `robustness_matrix.csv`: confidence interval, LOTO/LOBO, deletion, tail,
   censoring, and claim-boundary fields.
3. `cost_ledger.csv`: measured search, profiling, truth, certification,
   rebuild, serving, control, and fallback costs, or `NOT_ESTIMABLE` with a
   reason.
4. `break_even.csv`: N in {1e3,1e4,1e5,1e6,1e7}; search-only and full
   lifecycle conclusions are distinct.
5. `boundary_negative_results.csv`: retained negative, null, conditional,
   post-hoc, and infrastructure-boundary results.
6. `claim_evidence_matrix.csv`: allowable paper claims and their exact
   evidence scope.
7. report, checksum ledger, tests, and a machine-readable decision manifest.

## Statistical rules

- Reuse registered 5,000-repetition, seed-991 target-build bootstrap results.
- Do not create false precision by treating queries as independent builds.
- Require positive lower confidence bounds plus registered LOTO/deletion
  robustness for positive claims.
- Preserve p95/p99 and right-censoring fields; missing fields are explicit.
- External methods are assessed for transport safety, not universal quality.

## Economic rules

The full lifecycle total is

`rebuild + profiling + truth + selection + certification + control +
fallback + N * serving`.

Search-only break-even is reported only where the numerator and serving
savings were measured under a common action/cost unit. Full lifecycle
break-even is `NOT_ESTIMABLE` unless all required components are harmonized.
No search-only result may be stated as an end-to-end economic win.

## Frozen decisions

- `PHASE5_STATISTICAL_ECONOMIC_SEAL_COMPLETE_LIFECYCLE_CONDITIONAL` when the
  evidence inventory, robustness, boundary table, and measured search-only
  economics are complete but any lifecycle component remains unharmonized.
- `PHASE5_FULL_LIFECYCLE_ECONOMIC_GATE_PASSED` only if all lifecycle cost
  components are measured and the registered robust benefit is positive.
- `INVALID_PHASE5_INPUT_OR_SEMANTICS` on checksum drift, incompatible event
  semantics presented as pooled evidence, or a missing required sealed input.
