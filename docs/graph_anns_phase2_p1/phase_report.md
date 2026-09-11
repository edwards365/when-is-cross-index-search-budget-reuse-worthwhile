# Phase P1 report — semantics and data-hygiene sealing (handoff Phase A)

## Goal

Close the two hygiene/semantic gaps that block constructive work: (1) run the Vamana-style
query/base overlap audit at the same standard as the clean Faiss-100K forensics; (2) freeze
the estimand crosswalk (E4 original vs repaired h=10 vs paper-adopted values) and (3) draft
the definitions patch (incremental risk, variation families, DistComp rename, certification
parameters, preregistration binding) for application to the DOCX in P5.

## Inputs

- Vamana stages: `/home/wlk/data500/icba_vamana_stage1{,_arxiv}/` — per-build
  `data/V*/base.fbin|queries.fbin|truth.bin` + ID maps, stage-root `evaluation_queries.fbin`,
  `query_role_ids.json`, `query_roles.json`.
- Shared bases: `/home/wlk/data500/graph_anns_e4/inputs/{sift_100k,arxiv_nomic_100k}/`.
- Forensics standard to mirror: `results/graph_anns_iclr_phase1_1_hotfix/content_overlap_forensics.csv`.
- Estimand numbers: `graph_anns_e4_seal/h2_crossed_cluster_inference.csv`,
  `graph_anns_cross_family/main_effect_table.csv`,
  `graph_anns_iclr_phase1_1_repair/estimand_registry.csv`,
  `graph_anns_iclr_phase1_1_hotfix/cross_family_evidence_table_final.csv`.

## Deliverables

1. `results/graph_anns_phase2_p1/vamana_overlap_forensics.csv` (+ per-vector event counts)
   — query/base ID, raw-content, normalized-content overlap; historical-role overlap;
   internal duplicates; per-build base.fbin identity vs stage base and E4 input base.
2. `results/graph_anns_phase2_p1/estimand_crosswalk.csv` + `estimand_crosswalk.md`.
3. `docs/graph_anns_phase2_p1/definitions_patch.md` — paper-ready definition block.
4. `scripts/graph_anns_phase2/p1/*.py`, `tests/graph_anns_phase2_p1/test_p1.py`,
   `results/graph_anns_phase2_p1/decision_manifest.json`.

## Constraints

- Read-only on all frozen trees and on Vamana stage data (hash only, no rewrite).
- Overlap counts are reported, never "repaired"; a nonzero overlap is a Gate-fail disclosure
  for the paper, not something to fix in place.
- The estimand crosswalk must not reinterpret any frozen estimand; it only tabulates
  coexisting registered values and names which one the paper adopts.

## Execution record (steps 2–3)

- Vamana overlap audit PASS on both datasets at the Faiss-forensics standard: query/base raw
  and normalized overlap 0, historical-role ID overlap 0, internal raw/normalized duplicates
  0. Additional cross-stage check: Vamana evaluation queries vs the E4 hnswlib base = 0.
- All 24 per-build bases share one content multiset (differ only by registered row
  permutation); the Vamana base multiset differs from the E4 input base — recorded as a
  scope fact (separate registered snapshots per stage), consistent with the paper's
  never-claimed cross-family numerical equality.
- Limitation honestly kept: historical-role raw/normalized overlap is NOT_ESTIMABLE because
  the frozen Vamana stage did not retain role vectors (IDs only).
- Estimand crosswalk: 10 rows; the six paper-adopted values each carry their estimand label
  and source file.
- Definitions patch D1–D8 drafted for P5.
- test_p1.py: 24/24 checks pass.

## Theory/paper consistency review (step 5)

1. The Vamana hygiene attack surface (handoff §8.2 item 7) is closed: the paper may now state
   the audit symmetric to the clean Faiss-100K forensics, with the two disclosed caveats
   (role vectors not retained; separate base snapshot).
2. The crosswalk resolves review item P1 (hnswlib 21.55 vs E4 21.57): the paper must add one
   appendix table row-pair stating the repaired h=10 estimand is the adopted common estimand
   and the E4 original remains the registered primary label — no number changes.
3. D5 formalizes 59 = ceil(log 0.05 / log 0.95) exactly as the single-action zero-failure
   threshold; this supports the P2 certification design (select-then-certify needs the
   Bonferroni-inflated m, already present in per_target_cp_audit.csv as cp_ucb_bonferroni_48).
4. No frozen estimand was reinterpreted; no old result modified.
