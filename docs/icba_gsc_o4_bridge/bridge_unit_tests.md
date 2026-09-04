# Bridge unit and invariant tests

Eight bridge tests passed before interpreting smoke metrics. The no-op baseline comparison covered 1,500 query–ef rows (500 queries × 3 ef × 3 fixed evaluator rounds) with zero harmed pairs and native/tracer equality. Each O4 index had a non-empty mutation, changed edge hash, unchanged upper-layer hash, valid degree/ID/self-loop invariants, and equal in-memory/reloaded edge audits. Results are in `bridge_unit_tests.csv` and per-config bridge metadata.
