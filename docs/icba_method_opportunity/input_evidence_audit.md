# Input evidence audit

- Status: PASS_WITH_EXPLICIT_MISSING_FIELDS
- Frozen start: `7417147e9ce2e526973cd47b3b390c0ae2bb7c65`
- Branch: `exp/icba_unified_method_opportunity_audit`
- Worktree created clean from the frozen start.
- All nine required references resolve; the certification-fallback theory object was fetched as a read-only remote reference and was not merged.
- Evidence ledger rows: 17; manifest parse failures: 0.
- Legacy limitation: `LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123`.
- Evidence policy: missing numeric or semantic fields remain `NOT_ESTIMABLE`; no raw large table was loaded.
- Access firewall: validation-dev, formal-test, certification_reserved, and evaluation_reserved were not accessed.
- Experiment mutation: no graph construction, algorithm implementation, model training, GPU job, or sealed-query access.
- Initial storage after worktree creation: 14,429,892,608 bytes free; mandatory reserve: 5 GiB.

## Resolved references

- frozen_start: `7417147e9ce2e526973cd47b3b390c0ae2bb7c65`
- semantic: `f7f08ce1f82e23eb4b14cdc08db1190301dc82af`
- stable_theory: `dca81b23ce3cfe7ca95e3b3362fb3129cf24f937`
- auditor: `be393d3c3b0a2450edefb3b2889f0511dfd8919f`
- cert_fallback_theory: `41a44bd930679b5e933034a1496d2fe42e1ae018`
- ordered_rung: `904de537f16798eac9f68da549f2741d92e2b1c2`
- active_gate: `97ca42a120fff015885bba509e8aa90178aabfa2`
- asrc: `5f4d04f6e836059c98024b01f4929bcd406cdcc1`
- open_world: `a9f88bbcfd9b2c2f3e8a27e1471e16628b60cdb0`

## Scope limitation

This audit standardizes only frozen, already-derived evidence. A manifest omission is not inferred from neighboring experiments. Oracle and single-build pilot evidence cannot establish deployable or cross-build performance.
