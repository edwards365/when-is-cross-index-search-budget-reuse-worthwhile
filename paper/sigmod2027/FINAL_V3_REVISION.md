# Final V3 revision record

## Outcome

Final V3 is the submission-oriented, zero-new-experiment revision of the SIGMOD 2027 Experiments & Analysis manuscript. The paper remains centered on budget non-portability, ICBA's target decision contract, a least-complexity recovery ladder, and lifecycle value. The revision reduces reader effort and closes statistical-semantic ambiguities without changing frozen experimental outcomes.

## Critical reading of the two detail reviews

The reviews were directionally correct on certificate scope, inference-unit labeling, policy naming, provenance, and baseline fairness. Those were not cosmetic requests: without them, a reader could mistake per-target certificates for campaign-wide coverage, treat a shared build panel as an independent replication, or compare policies with different information budgets. Final V3 therefore implements these items directly.

Several suggestions required qualification rather than literal adoption. The manuscript does not add simultaneous control over all 112 decisions, because that was not the registered estimand; it states the per-decision scope. It does not invent a complete wall-time acquisition ledger where truth/control time was not measured. It also does not insert a fictitious anonymous URL. Finally, the paired diagnostic remains an attribution audit and is explicitly not a post-evaluation deployment selector.

## Main changes

- Added a full evidence-provenance table and machine-readable claim map.
- Standardized the policy vocabulary: fixed action, target-global calibration, TCP, and source one-rung.
- Defined Fixed-256's grid origin and freeze point.
- Defined target-global selection, tie-breaking, certification, fallback, and abstention.
- Added C/F/A counts and full 95% risk and p95 intervals to prospective tables.
- Declared the 112 decisions to be separately certified rather than simultaneously covered.
- Clarified that prospective confirmation and the paired audit share builds but use disjoint query roles.
- Added Figure 4 marker semantics and retained the hnswlib no-slack counterexample.
- Restored Deep1M certified recovery, TCP p95/p99 anchors, oracle headroom, and cost-interval caveats.
- Added hashed provenance for two p95 intervals derived from frozen response arrays; no new experiment was run.
- Rewrote the theory transitions around three operational takeaways.
- Removed internal stage codes from the main paper, ranking language, duplicated defensive text, and a manuscript-level tooling citation.
- Corrected a duplicate section label and standardized dataset, interval, and p95 formatting.

## Verification

- Main paper: 10 US-letter pages.
- Supplement: 5 US-letter pages.
- No overfull boxes, unresolved references, missing characters, or duplicate labels.
- All five main-paper figures were visually inspected after rasterization.
- The automated readiness audit is fail-closed and records PDF hashes.
- The anonymous artifact URL remains an external submission-system action; no URL is fabricated in this package.

## Tooling disclosure

The revision workflow used the writing guidance in Kassis et al., “Scientific Agent Skills: A Domain-Specific Library for AI-Assisted Research,” arXiv:2609.00065, DOI: 10.48550/arXiv.2609.00065. This is a tooling acknowledgment in the revision record, not scientific support for a manuscript claim, and is intentionally absent from the paper bibliography.
