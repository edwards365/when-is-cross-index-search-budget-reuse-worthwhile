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

## Execution record (step 2–3)

- `aggregate_ladder.py` ran clean (pure code, frozen trees read-only): 17 aggregates audited —
  8 REPRODUCED, 2 STORED_VERIFIED, 7 ORIGIN_UNLOCATED, 0 MISMATCH.
- Notable upgrades over the pre-P0 review: the shared-frontier compression range 79.5%–93.4%
  is now exactly reproduced from `results/icba_shared_cost_gate/critical_compression.csv`
  (min 79.55% over kappa_recall/kappa_hit rows, max 93.43%); portal sums and auditor
  regret CIs reproduce to stored precision.
- `reference_anchor_audit.py`: 17/23 references anchored; 6 have no in-text anchor
  (Bae/QBAT, Elliott & Clark, Garivier & Kaufmann, Prokhorenkova & Shekhovtsov, Yu 1997,
  Zhang & Miller).
- `test_p0.py`: 16/16 checks pass.

## Theory/paper consistency review (step 5)

P0 makes no scientific claim, so no theory conflict arises. Consistency findings:

1. Handoff §12 (traceability) is now measurable: 10/17 Section-8 aggregates trace to frozen
   artifacts; 7 do not. The unlocated set covers the recalibration paragraph
   (29.40/26.17, +0.90 [-8.73, 11.25], -0.13 [-9.24, 10.26], -7.35, -12.49), the
   protected-edge repair pair (509.49→503.41, 849→833), and the matched-lane
   ratios/deficits (2.77×/2.47×, 4.79/3.29pp). None of these can enter the camera-ready
   unchanged: P5 must attach provenance, substitute the reproducible stored values
   (e.g. same-ef primary wall-clock ratios 2.93×/2.68× with explicit semantics), or drop.
2. The paper sentence "auxiliary work would need 79.5%–93.4% compression" is fully
   supported and should cite the critical-compression table semantics in the artifact.
3. Six references without in-text anchors are a camera-ready defect (P5 fix list).
4. No frozen number was modified; no estimand was reinterpreted.
