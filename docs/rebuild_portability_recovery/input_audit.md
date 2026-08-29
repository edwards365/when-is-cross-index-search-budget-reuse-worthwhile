# Recovery Phase 0 input audit

Status: EXPLORATORY_DESIGN_AUDIT_ONLY

- Audit date: 2026-08-29 Asia/Shanghai
- Repository: /home/wlk/projects/navigation-aware-resistance-hnsw-rcrs
- Branch: exp/rebuild_portability_recovery_gate
- Frozen theory base: 6339c512d81abbe49ff11b526676ec4d6d571453
- Base object: present and resolved by Git
- Tracked worktree at entry: clean
- Preserved untracked material: logs/rcrs_signal (10 old files, about 28 KiB); not added, moved, compressed, or deleted
- Forbidden splits: validation-dev and formal-test were not accessed
- Graph construction: none
- GPU/complex model use: none

## Frozen evidence located

- results/icba_theory_elevation/phase0_summary.json
- docs/icba_theory_elevation/full_seal_reaudit.md
- results/icba_theory_elevation/checksums.sha256
- results/icba_micro_closure/checksums.sha256
- results/icba_micro_closure/{environment_sets,endpoint_audit,graph_replay,open_world_leave_build_out,unified_gate_table,cost_break_even,synthetic_bounds,synthetic_grid}.csv

The conditional baseline records 81 graphs, 972,000 query-budget rows, 648 directed build pairs (324 unordered), 54 certified endpoints, 17 right-censored endpoints, and 10 builds without a practical safe endpoint. It also records 94 directed Z0 collision candidates (47 unordered) over 70 builds. The current Full Seal set verifies 59/59 entries. The inherited micro-closure list does not reproduce exactly: 111/123 Git blobs match, eight tracked CSVs mismatch, and four listed Python bytecode cache files are absent.

## Definitions and source policy constraints

The recovery endpoint remains the target minimal safe budget on the fixed 12-level budget grid; NDC is the search-effort cost used by the frozen evidence. Any deployable source policy must use only static query information, source design statistics, and the permitted first-prefix checkpoint; target labels may enter only through the preregistered sentinel calibration. Source per-query Oracle is an upper bound and is not deployable.

## Gate

The checksum limitation is material to exact historical reproduction but the eight mismatches are aggregate/derived CSV artifacts, not newly discovered raw per-query records. Continuation is conditional: no exact 123/123 claim is allowed, all downstream source fields must be traced to the verified 59-file Full Seal evidence or independently recomputed in memory from frozen permitted inputs. If a required per-query source cannot be located without validation-dev/formal-test or cannot be hashed, the final label must be INVALID_RECOVERY_INPUT_DATA.

Phase 0 disposition: CONDITIONAL_INPUT_AUDIT_PASS_FOR_LIGHTWEIGHT_SOURCE_POLICY_AUDIT.
