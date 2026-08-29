# Legacy checksum semantic diff

Status: KNOWN_CONDITIONAL_BASELINE_LIMITATION

The inherited results/icba_micro_closure/checksums.sha256 contains 123 entries. At the frozen Git evidence boundary, 111 entries match, eight tracked CSVs mismatch, and four listed __pycache__ files are absent. No old file was repaired or regenerated.

## Eight mismatched tracked CSVs

1. results/icba_micro_closure/cost_break_even.csv
2. results/icba_micro_closure/endpoint_audit.csv
3. results/icba_micro_closure/environment_sets.csv
4. results/icba_micro_closure/graph_replay.csv
5. results/icba_micro_closure/open_world_leave_build_out.csv
6. results/icba_micro_closure/synthetic_bounds.csv
7. results/icba_micro_closure/synthetic_grid.csv
8. results/icba_micro_closure/unified_gate_table.csv

These are derived tabular artifacts. The expected byte streams cannot be reconstructed from SHA256 digests alone, so a byte-level patch or exact numeric-cell diff is NOT_ESTIMABLE. Their roles are endpoint summaries, environment membership, replay/gate summaries, synthetic checks, and cost summaries. They are therefore prohibited as sole sources for a recovery decision. Row/schema/sort/numeric-summary comparisons against a missing expected byte stream are also NOT_ESTIMABLE; current versions may be inspected only as conditional design context.

## Four absent entries

- src/icba_micro_closure/__pycache__/ecse.cpython-38.pyc
- src/icba_micro_closure/__pycache__/endpoint_audit.cpython-38.pyc
- src/icba_micro_closure/__pycache__/lower_bound.cpython-38.pyc
- src/icba_micro_closure/__pycache__/synthetic_closure.cpython-38.pyc

These are generated Python bytecode caches and are not admissible scientific evidence. Their absence does not justify recreating or committing them.

## Recovery firewall

Only fields traceable to verified Full Seal artifacts, frozen source/design records, and preregistered target sentinel samples may be used. No validation-dev, formal-test, source Oracle deployment, graph rebuild, or silent checksum repair is permitted. Any dependence of M0-M3 on an unverified legacy-only field forces INVALID_RECOVERY_INPUT_DATA for that method or for the full gate if the field is essential.
