# Final V3 detail-review disposition

Final V3 is a zero-new-experiment revision. It changes exposition, statistical labeling, evidence provenance, and reproducibility checks; it does not alter a frozen policy, query role, build, or reported experimental outcome.

## Closed before submission

- [x] Align every risk column with its stated 95% interval and inference unit.
- [x] Add candidate/fallback/abstention counts to prospective and paired-audit tables.
- [x] Define target-global selection, Bonferroni screen, tie-breaking, certification, fallback, and abstention.
- [x] Bind Fixed-256 to the registered Faiss grid and record that it was frozen before paired-audit access.
- [x] State that the 112 prospective decisions have per-decision certificates, not simultaneous campaign coverage.
- [x] Replace ranking language such as “dominates” with estimand-specific comparisons.
- [x] State that prospective confirmation and the paired audit share the same eight-build panel but use disjoint query roles.
- [x] Add Figure 4 marker semantics in its caption and legend.
- [x] Separate the retrospective paired audit from any post-evaluation deployment selector.
- [x] Add an evidence-provenance table and a machine-readable claim-to-record map.
- [x] Use semantic stage names in the main paper; keep internal S9 identifiers only in the supplement and artifact.
- [x] Define the fixed-machine protocol, repetitions, hardware, validity gates, amendment timing, and crossed bootstrap.
- [x] Account explicitly for target-global exact-truth labels and avoid an unsupported end-to-end economic claim.
- [x] Restore Deep1M certified-recovery results and the hnswlib no-slack counterexample.
- [x] Restore TCP p95/p99 anchors, lifecycle-cost intervals, and pairwise/shared-target meanings.
- [x] Mark the equal-information comparison as a post-hoc frozen-response sensitivity and add derived p95 intervals with input hashes.
- [x] Quantify oracle headroom and tie mechanism attribution to registered records.
- [x] Standardize dataset, policy, risk, p95, and interval terminology; remove the manuscript-level tooling citation.
- [x] Correct the duplicate section label and figure-count statement.
- [x] Compact the abstract/introduction and add reader takeaways after the three theoretical results.
- [x] Preserve negative and boundary evidence instead of converting it into a universal recovery claim.

## Deliberately not changed

- No new experiment, new build, new query access, tuning, or post-result policy choice was introduced.
- The main endpoint remains NDC where only NDC was measured; wall time is claimed only for the fixed-machine campaigns.
- Conditionality on registered builds, grids, query populations, and SLAs remains explicit.

## External submission action

- [ ] Insert or confirm the anonymous artifact URL in the submission system and, if venue policy requires an in-PDF link, replace the placeholder sentence only after the anonymous URL exists. Final V3 does not fabricate a URL.
- [ ] Recheck the uploaded PDF filename and metadata in the submission portal.

## Tooling disclosure

The revision workflow used the writing guidance in Kassis et al., “Scientific Agent Skills: A Domain-Specific Library for AI-Assisted Research,” arXiv:2609.00065, DOI: 10.48550/arXiv.2609.00065. This is a tooling acknowledgment for the revision record, not scientific support for a manuscript claim, and is intentionally absent from the paper bibliography.
