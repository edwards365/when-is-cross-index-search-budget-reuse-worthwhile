# Input and event audit

- Frozen input: `97ca42a120fff015885bba509e8aa90178aabfa2`.
- Evidence: `EXPLORATORY_FIXED_TARGET`.
- Z_abs is consistently represented by `abs_fail`, with `rec_fail` (under-budget) and `censor_fail` retained separately.
- One-sided Clopper-Pearson upper bound was independently recomputed at alpha=0.05. Exact row consistency: 1.000000.
- Evaluation risk is used only for retrospective quadrant assignment, never selection/certification.
- Query roles inherit the frozen mutually-exclusive firewall.
- Query-pooled p95 is reconstructed from frozen candidate query costs.
- No validation-dev/formal-test or GloVe data accessed.
- Low-disk streaming/compact-output mode active.
