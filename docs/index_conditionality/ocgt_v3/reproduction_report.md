# OCGT-v3 Gate R reproduction report

Status: `PASS_GATE_R_TO_MAIN_MATRIX`.

- Nine graphs completed: three datasets × random/LID-ascending/LID-descending × graph seed 43.
- Every graph was rebuilt and queried twice from scratch.
- Confirmatory cells per repetition: 54,000; retained reproduction rows: 108,000.
- All 54,000 native-versus-instrumented query×ef cells matched exactly for returned top-10 labels, Recall and exact NDC.
- Repeat 1 and repeat 2 matched exactly after excluding descriptive latency; all nine graph hashes, entry points and maximum levels matched.
- All 18 raw files contain 6,000 rows and the complete preregistered schema.
- No failure or non-empty error log was observed.
- validation-dev was not available; only the frozen independent train-member fallback queries were used.
- formal-test was not accessed and OCGT-v2 evidence was not modified.

The nine repeat-1 graphs are authorized to enter the main matrix. The remaining seed-59 and seed-71 graphs may now run without changing code, inputs or protocol.
