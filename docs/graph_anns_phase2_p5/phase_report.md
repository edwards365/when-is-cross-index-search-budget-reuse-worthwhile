# Phase P5 report — paper integration, final ICLR review, next loop

## Goal
Integrate P0-P4 results into a complete, number-verified revision package for the anonymous
DOCX; run the final ICLR-standard review; define the next optimization loop.

## Execution record (step 2)
- make_figures.py produced three publication figures (pooling ladder, decision plane,
  contract ablation) in figures/graph_anns_phase2/ (PNG+PDF); M1 cost added after visual
  check showed the naive-transport point missing.
- verify_patch_numbers.py: 14/14 number-traceability checks binding every figure quoted in
  paper_revision_patch.md to the P2-P4 artifacts (one mismatch found and fixed: M2 overall
  unsafe-execution is 0.18/0.08%, patch initially said 0.95/1.30%).

## Deliverables
- docs/graph_anns_phase2_p5/paper_revision_patch.md (R1-R12, complete edit list)
- docs/graph_anns_phase2_p5/final_iclr_review.md (strict review + P6 plan)
- figures/graph_anns_phase2/* (3 figures x PNG/PDF)

## Theory/paper consistency review (step 5)
- All patch numbers machine-verified against artifacts; no frozen number changed.
- Patch keeps claim discipline: pooling is uncertified and registered-conditional;
  Theorem-2 verdict is grid/data-conditioned; predictor layer marked untested.

## Final review closure (step 5)

The strict ICLR review is in final_iclr_review.md. Verdict: the package after the R1-R12
patch is a solid 6 with realistic 7 upside; the 8/10 target requires the P6 evidence
loop (1M cell, predictor probe, distinguishability instantiation), which is scoped and
ordered there. Self-loop protocol: P6 gates mirror P0-P5 (progress.json five-step cycle,
phase reports, deterministic tests, no estimand changes).
