# SGDR three-day feasibility final report

## Decision

`STOP_ALGORITHM_PIVOT_TO_BOUNDARY_STUDY` (`FAIL_ORACLE_UPPER_BOUND`).

The study answered its 72-hour feasibility question at low cost and stopped at the
first failed implementation gate. No SGDR product implementation, Random/Shuffled
performance sweep, E1, BEP, validation-dev, or formal-test access was authorized.

## Evidence

The strict complete-policy oracle selected R4 only when its query-level Recall was no
worse than Original. It passed all nine runs: mean NDC theoretical improvement was
4.18–4.37% on SIFT, 3.73–4.05% on GloVe, and 8.47–9.03% on Arxiv. The R4-safe fractions
were 90.08%, 81.79%, and 93.39%, respectively, and removing the largest 1% savings did
not erase the signal. Query heterogeneity is therefore real rather than a single-seed
or extreme-query artifact.

The signal did not yield a viable mechanism. Full failure-then-Original fallback was
not cross-dataset feasible: across the 18 seed×ef cells per overhead value, GloVe
passed 0, SIFT 9, and Arxiv 12. The exact additive experiment then retained every
Original edge, added a frozen 10% R4-minus-Original delta budget, and evaluated nine
dataset×seed runs, 500 design queries, six existing ef points, five scale gates, four
depth gates, and Union-All—297,000 paired rows. No fixed scale/depth mode passed any
dataset in 2/3 seeds. High thresholds became Original with approximately zero gain;
active delta use added work. Union-All increased mean NDC by 2.616% (SIFT), 2.880%
(GloVe), and 2.445% (Arxiv), while mean Recall did not decline.

The phase summary is consistent with a cost-dominated mechanism: first delta use can
produce small positive average Recall changes, but every phase bucket carries positive
NDC overhead. Thus the experiment does not support the claimed far-field NDC gain;
it shows that additive edges avoid the old replacement Recall damage but do not pay for
their own inspection under the frozen budget and gates.

The prior repair Pareto boundary remains decisive. At 25% add-back, mean Recall-loss
recovery was 88.90% (SIFT), 66.00% (GloVe), and 91.44% (Arxiv), but retained NDC gains
were −1.831, −0.972, and −1.433. At budgets that retained at least half the NDC gain,
Recall recovery remained far below 80%. This empirically exposes the conflict between
far progress, near redundancy, and finite-beam queue interference.

## Required questions

1. **Can the old NDC signal become a useful oracle bound?** Yes: the perfect complete-policy selector has a stable 3.7–9.0% bound, but it is not realizable by the tested gate.
2. **Is far-delta/near-Original directly supported?** No. Exact stage diagnostics show small Recall gains coupled to positive NDC cost, not far-field cost savings.
3. **Does SGDR reduce NDC without material Recall loss?** No preregistered mode does so.
4. **Does it beat random/shuffled controls?** Not tested, because Gate O failed before those implementation experiments were authorized.
5. **Is it stable across datasets, seeds, and ef?** The oracle is stable; the realizable scale/depth benefit is absent across all of them.
6. **Do edge/gate costs erase benefits?** Yes. Even before wall-clock gate overhead, counted delta distance calls eliminate the benefit.
7. **Is there a fatal novelty collision?** No exact collision was found, but GATE, Ada-ef, DARTH/LAET, PEOs, and CRouting make the adaptive-routing neighborhood crowded.
8. **What next?** Stop this algorithm route. Package the counterexamples and empirical Pareto law as a negative HNSW topology/search boundary study; any future algorithm must introduce a new signal or avoid paying speculative delta-distance cost.

## Deliverables and integrity

The preregistration, Gate reports, theory, primary-source literature matrix,
reproducibility record, raw compressed per-query outputs, summary CSV/JSON, and four
figures are present under `manifests/sgdr_3day`, `docs/sgdr_3day`, and
`results/sgdr_3day`. Evidence hashes are recorded in `final_decision.json`. All native
equivalence checks passed, stderr logs were empty, and temporary indexes were deleted.
