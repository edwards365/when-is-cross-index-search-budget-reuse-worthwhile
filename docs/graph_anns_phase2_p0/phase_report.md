# Phase P0 report — takeover hardening

## Goal

Convert the handoff plan into an executable, auditable working state without touching any
frozen result: working branch, fixed environment record, reproducible aggregation for every
Section-8 falsification-ladder number cited in the anonymous paper, and a reference-anchor
audit for the DOCX. P0 produces no new scientific claim.

## Inputs and dependencies

- Authoritative base: `ffe5798` on `exp/graph_anns_iclr_phase1_1_final_evidence_hotfix` (verified in sync with remote).
- Anonymous paper DOCX (session attachment `01-ICBA_ICLR_Anonymous_Revised.docx`), extracted read-only.
- Frozen result trees: `results/icba_cals_seal`, `results/icba_fixed_target_auditor`,
  `results/icba_bn_apd*`, `results/icba_gsc`, `results/graph_anns_e4*`, `results/graph_anns_iclr_phase1*`.
- Runtime: repo `.venv` (Python 3.11) with `LD_LIBRARY_PATH=/home/wlk/miniconda3/lib`
  (system libstdc++ lacks GLIBCXX_3.4.29 for the venv pandas build).

## Deliverables

1. `results/graph_anns_phase2_p0/ladder_aggregate_audit.csv` — for each Section-8 aggregate:
   computed value, paper value, source file, status (`REPRODUCED` / `STORED_VERIFIED` / `ORIGIN_UNLOCATED`).
2. `results/graph_anns_phase2_p0/reference_anchor_audit.csv` — per reference: anchor found or missing.
3. `docs/graph_anns_phase2_p0/environment.md` — pinned runtime facts.
4. `scripts/graph_anns_phase2/p0/*.py` — aggregation code (pure code, no ANN access).
5. `tests/graph_anns_phase2_p0/test_p0.py` — deterministic assertions over the audit outputs.
6. `results/graph_anns_phase2_p0/decision_manifest.json`.

## Constraints

- Frozen trees are read-only; all outputs in new directories only.
- `ORIGIN_UNLOCATED` is an acceptable outcome (recorded, not interpolated).
- No new experiment, no estimator changes, no paper edits in P0.
