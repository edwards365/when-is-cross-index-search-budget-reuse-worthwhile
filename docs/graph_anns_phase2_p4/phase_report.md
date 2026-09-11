# Phase P4 report — economics ledger + budget-grid sensitivity (handoff Phase D)

## Goal

1. Six-cell economics matrix: every cost component x every registered cell, each labeled
   MEASURED / DERIVED / SYMBOLIC_ONLY / NOT_ESTIMABLE, from frozen P4/P6 tables - closing
   handoff §8.2 item 8 (no more selected-setting cherry-picking).
2. Budget-grid sensitivity: recompute min-safe-action transport risk from per-query records
   under registered subgrids (FULL / DROP_MIN / DROP_MAX / COARSE). Non-registered action
   values are NOT_ESTIMABLE (would need new ANN search) - reported as such.

## Deliverables

results/graph_anns_phase2_p4/{economics_matrix.csv, grid_sensitivity.csv,
grid_sensitivity_summary.csv}; scripts; tests; decision manifest.

## Constraints

Pure code; frozen trees read-only; no new search; grid variants limited to registered
subgrids (subsetting only, no interpolation).

## Execution record (steps 2-3)

- economics_matrix.py: 30 cells (6 cells x 5 components), 8 measured, 2 NO_FINITE, 20
  NOT_ESTIMABLE with reasons. One retry: break-even strings and object-dtype thread
  filters fixed; no framework change.
- grid_sensitivity.py: FULL grids reproduce the four frozen absolute risks to 1e-6
  (independent replay validation #4); COARSE/DROP variants stay above the materiality gate.

## Theory/paper consistency review (step 5)

- The grid-sensitivity claim is framed as estimand-indexed (see theory note), consistent
  with the frozen native-action guardrail; no frozen number modified.
