# P5 paper revision patch (complete edit list for the anonymous DOCX)

Every number below is traceable to `results/graph_anns_phase2_p{2,3,4}` artifacts on
branch `exp/graph_anns_phase2_constructive_closure`. No frozen number changes.

---

## R1. Abstract (replace two sentences, keep 204-word scale)

Replace:
> "Vamana-style experiments independently support the direction (11.37%–16.86%) under a stage-specific estimand."

Keep. Replace:
> "Fixing input order, seed, thread count, and toolchain eliminates measured transport risk, with 1.71×–3.52× build-time overhead."

With:
> "Fixing input order and single-threaded construction eliminates measured transport risk, with 1.71×–3.52× build-time overhead; order pinning alone halves response variation at no build-time cost. A max-over-source pooling baseline over 22 registered builds cuts incremental transport risk from 17.2–23.6% to below 1% at 1.34–1.45× the per-query-oracle cost, whereas select-then-certify finds no margin-separated certifiable action on any registered target."

## R2. Introduction — multi-replica motivation (rewrite of the opening motivation)

Insert after paragraph 1:
> "The reconfiguration we study arises in ordinary operation. A vector collection is frequently built more than once: serving replicas are (re)created on different machines with different insertion orders and parallel schedules; autoscaling adds replicas; failure recovery and blue-green deploys rebuild from the same data; library upgrades rebuild under new toolchains. A budget policy calibrated on one replica — a canary — is then reused across the replica set. We study the risk of this plausible deployment shortcut: whether the calibrated budgets remain safe on independently built replicas of the same collection. We make no claim that every operator reuses budgets, and cite no production incident; the setting is stated as a plausible, common-shape deployment pattern, and all conclusions are conditional on registered builds."

## R3. Introduction — three-layer evidence statement (replaces the predictor claim)

Replace any sentence implying a query-level predictor or stopping rule was measured with:
> "Our evidence addresses three layers with different strength. First, the query-level safe-budget *response* is strongly non-portable across registered rebuilds (17.17–23.60% incremental transport risk). Second, at the *global policy* layer we give a constructive answer: pooling 22 source builds into a per-query conservative action cuts risk below 1%, and certified fixed-action fallback is possible but only at the maximum registered budget. Third, whether a *learned query-level predictor* trained on one build transfers to another remains untested and is future work; the 17–24% figures are response-layer and policy-layer quantities, not the deployment failure rate of any trained predictor."

## R4. New Section 7.x "Constructive baselines and certification" (after 7.3)

Content (all values from `results/graph_anns_phase2_p2/`):
- Table 5 (six methods × two hnswlib cells): M1 naive 21.89/18.06%; M2 max-over-22 risk
  0.18/0.09% on deployable queries (overall unsafe-execution 0.18/0.08%; abstention 2.38/2.67%),
  DistComp 1.453/1.341×, LOBO max 2.13%; M3 fixed max-action certification at m=59
  certifies 70.8%/37.5% of targets (100 draws; P(pass|r)=(1−r)^59 with r=0.008/0.0126);
  M4a point-screen select-then-certify certifies 0/48; M4b Theorem-2 screening
  (selection-block CP upper bound ≤ δ) selects ef=120 (8/24) or ef=200 (16/24) and
  certifies 0/48 — no margin-separated action exists on the registered grid; M5 always-max
  0.80/1.26% at 4.09/5.14×; M6 oracle risk = endpoint mass (0.80/1.26%).
- Figure (fig_pooling_ladder): risk vs k pooled sources; k=1 reproduces the registered
  main results exactly (independent replay validation); k≥10 below 2.4%; p95 curves cross
  the 5% tolerance at k≈5–10.
- Figure (fig_decision_plane): risk–cost plane with the four-outcome semantics.
- Theorem-2 verdict paragraph: conditions (i),(ii),(iv),(v) satisfiable; (iii) fails for
  all 48 targets (`five_condition_instances.csv`); certified route collapses to
  max-budget-or-abstain. Explicitly conditional, not an impossibility claim.

## R5. Section 7.3 contract ablation (extend, values from `results/graph_anns_phase2_p3/`)

Add:
> "A descriptive chain ablation attributes the contract's effect: pinning the insertion order to a canonical order halves minimum-safe-action variation (68.3→34.1% SIFT, 63.2→30.8% Arxiv) at build-time ratio 0.80×/0.93× — i.e., free. Pinning the seed under 8-thread construction is nearly inert (−1.3/−4.3pp), and the six D2 builds with identical order and seed produce six distinct serialized indexes: parallel scheduling is a residual nondeterminism source that the exposed seed does not control. Single-threaded construction is therefore the necessary and sufficient registered clause for byte identity (3/3 identical, variation 0), and it carries the entire overhead (4.73×/1.86× relative to the pinned 8-thread tier; 3.52×/1.71× relative to D0C). The ablation is a chain, not a full factorial; effects are descriptive."

Rename D3 per definitions patch D7 ("hnswlib deterministic construction control").

## R6. Section 7.x economics matrix (from `results/graph_anns_phase2_p4/`)

Replace selected-setting cost reporting with the full 36-cell matrix table (6 cells × 5
components), statuses MEASURED / NO_FINITE_BREAK_EVEN / NOT_ESTIMABLE-with-reason. Note
SIFT hnswlib break-even is NO_FINITE (no online saving at the certified operating point)
and Arxiv is 11,832 (search-only) / 104,383 (wall-clock) queries at the 8-thread n=59
configuration.

## R7. Grid sensitivity paragraph (from `results/graph_anns_phase2_p4/grid_sensitivity*`)

> "Transport risk is grid-indexed: on registered subgrids (drop-min, drop-max, coarse
> 3-action) mean family risk stays between 10.3% and 23.8% — always above the 2%
> materiality gate — while coarser grids mechanically lower measured risk because the
> minimum safe action can only grow. We therefore claim phenomenon-level grid-robustness,
  not resolution-invariant risk levels, and keep native grids separate across
> implementations."

## R8. Definitions placement (apply `docs/graph_anns_phase2_p1/definitions_patch.md`)

D1/D2 where transport risk first appears (§3/§6); D3 variation formulas at §7.1; D4 global
ROM-NDC→DistComp rename (Tables 3/4 headers, §7.2, Appendices F/G); D5 certification
constants at §4.3/§5; D6 preregistration binding at §6 and Appendix I; D7 at §7.3; D8 at §8.

## R9. Related Work anchors for the six orphan references

- §2.1: "...construction cost and pruning [Prokhorenkova & Shekhovtsov 2020]; data-order
  effects on recall [Elliott & Clark 2024]; budget autotuning per index [Bae et al. 2026]."
- §2.2: "...adaptive HNSW exploration [Zhang & Miller 2026]."
- §4.1: "The Le Cam two-point reduction follows [Yu 1997]."
- §4.3: "Fixed-confidence selection sample complexity parallels best-arm identification
  [Garivier & Kaufmann 2016]."

## R10. Claim registry updates (Appendix H)

Add to permitted: pooling-baseline statement (registered sources, uncertified, four-outcome
semantics); contract-ablation attribution (descriptive chain); grid-robustness at
phenomenon level; Theorem-2 margin verdict (registered grid only).
Add to prohibited: "certification is impossible"; "order pinning makes rebuilds safe";
"resolution-invariant risk"; "learned predictors transfer"; any 1M-scale claim.

## R11. Limitations additions

(i) The constructive table is a retrospective replay on registered builds, not a
deployment study; pooling requires retaining 22 prior builds and their per-query records.
(ii) Theorem-2 margin verdict is grid- and data-conditioned. (iii) Contract ablation is a
descriptive chain. (iv) Vamana cost remains NOT_ESTIMABLE; Vamana pools untested.

## R12. Reproducibility statement addition

New artifacts: `results/graph_anns_phase2_p{0..5}`, scripts `scripts/graph_anns_phase2/*`,
tests with 27+16+16+7 deterministic checks (P2–P4), figures
`figures/graph_anns_phase2/*`; branch and commit pinned; no ANN search was invoked at any
point in this revision cycle.
