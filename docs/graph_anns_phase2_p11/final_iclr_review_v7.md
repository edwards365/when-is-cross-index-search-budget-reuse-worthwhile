# Strict ICLR review — v7 (R_D, post-P11 evidence cycle)

Calibration: same standard as R1/R2/R3 (the three external rounds) plus their stated
upgrade conditions. All numbers verified against frozen artifacts in
results/graph_anns_phase2_p{2,3,4,6,8,10,11} and committed tests
(16/24/27/16/7/22/17+14+P11 suite).

## Score-relevant changes since the last external review (v3/v4 state)

| External complaint | v7 status |
|---|---|
| R1-C1 h=10 artifact | CLOSED (P8: h=8 min 5.96% all cells; 10M flat 22.16–22.74%) |
| R1 5→6 condition | MET |
| R2-Q4 gamma sensitivity | DONE + wording synced at six sites (cert power binds) |
| R2-Q2 richer probes | DONE (probe exhaustion: F4 stack near chance; joint runtime 0.72 max; truth-locked mechanism identified) |
| R2-Q3 pooling aggregation | DONE (q0.9≈max; median unusable; corr-weighting BREAKS guarantee — new negative result) |
| R2-Q5 canonical order default | DONE (decision rule restated) |
| R3 page limit 9pp | ADDRESSED in structure (main 54.8k chars, 2 figs, 6 tables; needs Overleaf confirmation) |
| R3 M2 not serviceable for cold queries | CLOSED (B2: cold = 1.73s → measured, relabeled, tiered policy with rho-bound; graceful degradation measured) |
| R3 marginal-vs-joint TV | CLOSED (runtime probes are (q,build)-joint functions; conditional variance ratio quantified; caveats stated) |
| R3 margin wording inconsistency | CLOSED (six-site sync) |
| R3 estimand auditability | CLOSED (Eq.20 per-sample semantics; N1 digit-matched crosswalk) |
| Scale (all reviewers) | CLOSED (0.01M farm / 100K / 1M / 10M ladder; phenomenon 21.55→22.16%; population: 100% of pairs > 2%) |
| Constructive answer "self-undermining" | TRANSFORMED (Theorem 3: certified deployable policy, complete validity matrix 3 scales × 2 implementations; tiered composition with measured rho-interpolation; end-to-end ledger incl. profile-and-certify comparison) |
| Origin-unlocated aggregates | PARTIAL (matched-lane replaced by reproducible 2.93x/2.68x same-ef; two others still flagged in appendix — remaining) |

## R_D assessment (strict)

**Strengths (new since external rounds).**
S1. A certified deployable policy (Thm 3) with a *complete* validity matrix — three
scales, two implementations, farm depth k=49, counterexample row showing the premise is
load-bearing. The paper now delivers theory → algorithm → measured deployment semantics.
S2. Population-level evidence (200-build farm): every rebuild pair above the gate;
arms identical; exchangeability premise and coverage both hold — the population claim is
measured, not open.
S3. Scale ladder closed at 10M with the pooling boundary *measured degrading* — a
negative result that strengthens the decision rule (the certificate survives at
resolution; cheap uncached pooling does not).
S4. Honest engineering facts: no-truth calibration degenerates to always-max; cold-query
pooling is 6000x too slow; these close the "why not just X" family of attacks.

**Remaining weaknesses (unavoidable this cycle).**
W1. Theory novelty is still classical-tool composition; the new theorem is a rank
argument. The paper's defense (formulation + measured boundaries + certified policy) is
as strong as this framing allows — but a theory-first reviewer can still cap at 7.
W2. 1M/10M conformal cells are pool-resolution-limited (alpha>=0.125) — honest, but a
reviewer may note the certified operating points cluster at 100K/farm.
W3. Single-machine, no production trace; exchangeability across *operators* is asserted,
not tested (the farm tests it across one pipeline).
W4. Two historical aggregates remain origin-unlocated (flagged).
W5. Page count needs Overleaf confirmation; my estimator has twice been miscalibrated.

## Verdict

Score: **7/10 (clear accept band) with a credible path to 8** depending on reviewer
weighting: an AC who rewards measured-boundary rigor + a certified policy with complete
validity evidence sees an 7.5-8; a novelty-first reviewer sees a 6.5-7. The external
rounds' own stated upgrade conditions are now all met except the two perpetual items
(theory-tool novelty, production-scale trace) that no two-week window can buy.

**To consolidate 8:** (i) Overleaf compile confirming 9-page compliance; (ii) the two
remaining aggregates re-derived or deleted; (iii) optional: one-paragraph formal
statement of the tiered-policy composite guarantee as a corollary (pure writing);
(iv) rebuttal letter keyed to R1/R2/R3 conditions (drafting cost ~1h).
