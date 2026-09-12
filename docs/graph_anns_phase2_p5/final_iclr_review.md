# Final ICLR-standard review of the upgraded package, and the next optimization loop

Written 2026-09-12 after P0–P5 on `exp/graph_anns_phase2_constructive_closure`.
Scope: the paper AS IT WOULD BE after applying `paper_revision_patch.md` in full.
Score calibration: strict ICLR reviewer, calibrated against the two external review rounds
recorded in the handoff ("solid 5 / fragile 6" before this cycle).

---

## Part I — review of the upgraded package

### Summary of the submission (post-patch state)

The paper formalizes Graph-ANNS index rebuilds as algorithmic environments and shows that
query-level minimum-safe budgets and global budget policies do not transparently transfer
across registered rebuilds (17.17–23.60% incremental transport risk on four strictly
comparable hnswlib/Faiss cells; Vamana-style supporting evidence under a separate
estimand). It contributes a transcript-limited lower bound, a fixed-target recovery
theorem whose five conditions are now *empirically instantiated with a transparent
failure* (margin absent on all 48 registered targets), a certified audit (ICBA), a
deterministic-contract mitigation with a mechanistic ablation (order pinning free and
halving variation; single-threading necessary and sufficient, carrying the full
1.71–3.52× overhead), a constructive pooling baseline (22-source max-over-source: risk
0.09–0.92%, 1.34–1.45× oracle cost, grid-robust), a full 36-cell economics ledger, and a
four-outcome decision rule with explicit abstention semantics.

### Strengths (what a strict reviewer would credit)

S1. **The constructive gap is closed in the strongest honest form.** The pooling baseline
was the single hardest attack; it is now measured (not argued), dominates the certified
route on cost at equal-or-better risk, and its k-ladder reproduces the registered main
results at k=1 — which simultaneously validates the replay and the estimand.
S2. **Theorem 2 is no longer a template.** Five-condition instantiation with a per-target
verdict (48/48 fail at margin) converts the positive theory into a measured boundary —
rare and citable.
S3. **Mechanistic attribution of the mitigation.** The ablation proves seed pinning is
inert under 8 threads (six distinct hashes) and single-threading is the load-bearing
clause; this is actionable and falsifiable, and upgrades the contract from a recipe to a
finding.
S4. **Statistical hygiene is now a first-class contribution**: Faiss/Vamana overlap
forensics, four independent replays reproducing frozen numbers, byte-identical pure-code
replay, full NOT_ESTIMABLE disclosure with reasons.
S5. **Claim discipline**: three-layer evidence framing (response / policy / learned
predictor) removes the E6 overclaim; no open-world, cross-family, or deployable-algorithm
claims anywhere.

### Weaknesses (what a strict reviewer would still press)

W1. **Scale is 100K and profiling is cheap there.** The so-what now rests on the decision
table, but a reviewer can still ask whether the risk phenomenon persists where profiling
is genuinely expensive (1M–100M). Not fixable this cycle; must be a stated boundary with
a next-step commitment.
W2. **Learned-predictor layer untested.** The three-layer framing is honest but a reviewer
may want at least one representative predictor (e.g., a small GBM on query features) with
source-train → target-build degradation quantified.
W3. **Pooling requires 22 prior builds with per-query records.** The paper should state
the k-curve's practical reading: k≈10 captures most of the gain, which is plausible for a
replica set, but this is an assumption about operational history.
W4. **Theory novelty is classical-tool composition.** The lower bound is Le Cam; the
recovery theorem is LTT/CP composition. The measured-margin verdict is the novel part;
the writing must keep foregrounding it.
W5. **Vamana asymmetry**: supporting-only, no cost, no harmonized estimand; a hostile
reviewer may call it decorative. Consider moving both Vamana rows to a clearly-marked
boundary panel.
W6. **The pooling baseline is uncertified.** Its risk estimate is a bootstrap CI over
queries conditional on registered builds; the paper must not let "0.09–0.92%" be read as
a guarantee for unseen rebuilds.

### Score

| Dimension | Before cycle | After patch | Note |
|---|---|---|---|
| Soundness | 4/5 | 4.5/5 | four replays; margin verdict; only residual: uncertified pooling read carefully |
| Contribution | 2.5/5 | 3.5/5 | constructive table + mechanistic ablation lift it from diagnostic to prescriptive |
| Novelty | 2.5/5 | 3/5 | problem formalization + measured theorem boundary; tools classical |
| Clarity | 2.5/5 | 3.5/5 | definitions sealed; three-layer framing; DistComp rename |
| Significance | 2/5 | 2.5/5 | decision table + cheap mitigations; scale question remains |
| **Overall (ICLR 10-scale)** | **5 (solid) / 6 (fragile)** | **6 (solid) — realistic 6, optimistic 7 with flawless writing** | |

**Path to 8/10 (strict):** all of W1–W2 resolved with new evidence (one 1M cell + one
representative predictor), plus the probe-distinguishability instantiation of Theorem 1.
Each is a bounded, pre-scoped experiment; none is speculative. The mathematical ceiling of
the current framing is ~7 even with perfect execution, because the tools are classical and
the scale is 100K — the 8th point must come from evidence breadth, not more polish.

---

## Part II — next optimization loop (P6 proposal, ordered by expected score gain)

**P6-A. Scale cell: SIFT-1M hnswlib (highest gain).** 24 builds is unnecessary at 1M; use
8 builds × 6 actions × 500 evaluation queries + exact truth (feasible: ~8 × 80s build).
Deliverables: transport risk + variation at 1M; profiling cost re-measurement (does the
"profiling is cheap" premise survive?); pooling k-curve at 1M. Acceptance gate: clean
query/base forensics BEFORE any risk number is computed.
Estimated impact: +0.5–1.0 (kills W1, strengthens significance).

**P6-B. Learned-predictor transfer probe (second highest).** One representative model
(gradient-boosted trees on query features: norm, lid estimate, kth-NN distance) trained
on source builds, evaluated on target builds; report risk/cost delta vs per-build
recalibration. Framed as a probe, not a method. Impact: +0.5 (closes W2, completes the
three-layer story).

**P6-C. Probe-distinguishability instantiation (theory completion).** For the two most
similar registered builds, compute a transcript-based two-sample statistic against probe
budget m ∈ {1..200}; show whether any realistic m separates them. If a near-indistinguishable
pair exists, Theorem 1 gets its empirical object; if not, the theorem stays a warning with
a measured distance curve. Impact: +0.25–0.5 (strengthens the theory story).

**P6-D. Writing polish pass** (post-evidence): compress §8 ladder to one figure + one
table; move Vamana to a boundary panel (W5); add operational-history caveat for pooling
(W3); final PDF page-by-page render check.

Sequencing: A and B are parallelizable; C after A (reuse 1M builds as candidate pairs);
D last. Do NOT start a second implementation, a new algorithm, or an open-world variant.

**Hard stop conditions carried over:** no estimand reinterpretation, no frozen-result
edits, no future-role access without preregistration.

---

## Post-P6 addendum (2026-09-12, after the authorized evidence loop)

P6 executed all three proposed experiments. Status of the weaknesses:

| Weakness | P6 outcome | Status |
|---|---|---|
| W1 scale (100K only) | SIFT-1M cell: incremental risk 21.87% [21.52, 22.21]; variation decomposition replicates (98.4% finite-action vs 13.2% endpoint); identity contract byte-identical at 1M | **CLOSED** |
| W2 predictor layer untested | GBM probe: transfer risk 23.9%/21.2% vs naive 21.1%/17.3%; in-target CV equally poor; transfer R²=0.015 | **CLOSED** (negative result, cleanly measured) |
| Theorem 1 premise uninstantiated | transcript TV ≤ 0.25 at chance classifier accuracy across 552 pairs, coupled disagreement 45–57% | **CLOSED** (instantiated, probe-class-conditional) |
| W3 pooling needs 22 builds | sharpened: at 1M even k=7 leaves 10.4% — source requirement is scale-dependent | reframed as a finding |
| W4 theory novelty | Theorem 1 now has its empirical object; Theorem 2 its measured failure boundary | improved |

### Revised score

All three evidence gaps on the 8/10 path are closed with new, preregistered, forensically
clean experiments. The paper after P5 patch + P6 sections now has: phenomenon at two
scales and three implementations, both theorems empirically instantiated, a constructive
decision table with measured boundaries (pooling scale-dependence included), a mechanistic
contract ablation, a full economics ledger, and grid sensitivity.

Remaining residuals: single-implementation 1M cell (hnswlib only); predictor probe is one
model class; TV claim is probe-class-conditional. These are stated boundaries, not gaps.

**Updated assessment: 7 (solid) — 8 (achievable)** contingent on (a) integrating the P6
sections at the same writing standard as R1–R12, (b) the page-by-page PDF render check,
and (c) reviewers crediting the measured-boundary style (the honest-negative framing that
ICLR reviewers either reward or discount). The 8th point no longer requires new
experiments; it requires flawless presentation of evidence that now exists.

### P7 (next loop, presentation-grade)

- P7-A: write P6 into the paper (new §7.5 "Scale, predictor, and distinguishability";
  abstract sentence; limitations; claim registry rows).
- P7-B: DOCX application of R1–R12 + P6 sections; rebuild all figures incl. 1M rows.
- P7-C: exported-PDF page-by-page formula/table/reference check (the extraction-failure
  lesson); artifact manifest refresh.
- Stop rule: no new experiments in P7 unless a P6 number fails verification.
