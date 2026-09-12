# Phase P11 — gap-closure roadmap to 8/10 (structure, triage, acceptance gates)

Inputs: fourth "breakthrough" review (agent). Diagrams:
`results/graph_anns_phase2_p11/{research_structure,roadmap_to_8}.png`.

## 1. Critical triage of the breakthrough review (adopt / already-done / reject)

| Agent proposal | Our status | Decision |
|---|---|---|
| gamma sensitivity sweep | **DONE** (P8-B): margin passes at gamma<=0.01 on 16-21/24; cert power binds | already integrated (v4) |
| executive/takeaway table | **DONE** (v3/v4 Table takeaway) | keep |
| 2% gate rationale + probe-class abstract qualifiers + M2 cache/coverage honesty | **DONE** (v4) | keep |
| 10M cell | **RUNNING** (P10: deep-image 9.99M, forensics PASS, build 1 done at 49 min) | in flight |
| quantile pooling | **DONE** (P8-E: q0.9==max, median unusable) | keep |
| probe-feature exhaustion matrix (curve-shape, queue, latency, x-ef) | partial (P8-C did 2 families) | **ADOPT as A1** (pure code) |
| conditional distinguishability (I(build;T\|q) / per-query joint) | partial (P8-C runtime features ARE joint functions of (q,build); not framed as MI) | **ADOPT as A2** (pure code) |
| M2 serviceability under cold queries | flagged in v4 (replay-cache + coverage) but not quantified | **ADOPT as A3** (rho-sweep, pure code) |
| cross-build population risk (builds as sampling units) | not done | **ADOPT as A4** (exchangeable-build bound, pure code) |
| "profile without truth" hidden-risk baseline | not done — biggest loophole | **ADOPT as A5** (queue-saturation no-truth rule, pure code) |
| latency p95/p99 user-loss ledger + 3 origin-unlocated re-derivations | scheduled (P8-D) | **ADOPT as A6** |
| online M2 prototype on cold queries | not done; feasible cheap at 100K (rebuild 22 idx ~10 min; SIFT-1M test queries as fresh workload) | **ADOPT as B1** (decisive) |
| head-to-head vs profile-and-certify / always-max / contract | partially (Table e2e); needs measured online arm | **ADOPT as B2** |
| weighted (correlation) pooling | not done | **ADOPT as B3** |
| RAG end-to-end user loss | no LLM stack in env; Recall-to-task mapping would be synthetic | REJECT this cycle; latency/SLO loss accounting (A6) is the honest proxy |
| GitHub-issue ecology audit | no web API access from env; anecdotes are weak evidence | REJECT this cycle; keep as camera-ready/external item |
| Vamana re-run with aligned estimand | requires DiskANN binary + new builds | DEFER (post-deadline) |
| "stable 8 in 2 weeks" | agree with agent | NOT promised; target is reviewer-calibrated 7.5-8 with C2 |

## 2. Acceptance gates (pre-stated, per figure roadmap)

- A-lane gate: every number traces to frozen artifacts + committed tests.
- B-lane gate: identical workload (fresh SIFT-1M queries), identical certification level,
  pre-stated win condition for B2 — e.g., "online-M2 achieves risk <= 1% with >= 90%
  coverage at mean DistComp <= 2x oracle, versus profile-and-certify at 4.2-5.3x with
  47-63% pass probability" — evaluated as stated, win or lose.
- If B2 loses: the paper pivots to the strong NEGATIVE route (validated boundary +
  economics) — still a contribution, per the agent's own exit clause.

## 3. Execution order

A1 -> A2 (same loader) -> A5 -> A3 -> A4 -> A6 (all pure code, ~1 day) ->
B1 -> B2 -> B3 (one session, ~1h compute at 100K) -> C1/C2 writing -> v5.
P10 (10M) runs in parallel and lands as C2.

## Step 2 — A-series executed (pure code, frozen data; tests pending)

All six items ran. Headlines: (A1) exhaustive-stack classifier stays near chance
(median 0.55-0.56) - Theorem-1 probe-class conclusion survives exhaustion; predictor
R2~1 for truth-dependent families is within-query leakage, precisely locating the
layer-3 mechanism (signal locked behind truth-dependence). (A2) across-build variance is
29-37% of across-query variance for hit transcripts - conflict is query-dominated.
(A3) M2 degrades gracefully: effective risk interpolates M2<->M5 with repeat rate; even
0% coverage stays <=1.3% under max fallback. (A4) all 24 targets above the 2% gate, so
the exchangeable-build Hoeffding bound is trivially 1.0 - the population claim is
formalized as open. (A5) no-truth saturation rule degenerates to max-action (ef~200) -
"profiling without truth" == always-max, closing the loophole by measurement.
(A6) pooling p95/p99 below always-max. A5 script carried two small defects fixed
en route (missing DATA500 import; per-build visit curve loader).

## Step 3 — Build-farm population study complete (the breakthrough item)

200 builds (2 arms x 100) on SIFT-10K. Population: every one of 9,900 directed pairs
exceeds the 2% gate (mean 23.4%, p95 26.6%, max 31.4%); arms A/B statistically identical
(23.42% vs 23.45%) - scheduling noise does not amplify population risk. Theorem 3 on the
farm: exchangeability KS median 0.114/0.118 (uniformity holds after randomized
tie-breaking; the naive argmax rank gave a 0.47 tie artifact) and conformal coverage
2.53%/2.62% <= alpha=0.10 at k=9. A4's population claim is now measured, and Theorem 3
has premise-level plus guarantee-level empirical support on an independent farm.

Three defects fixed en route (boolean-matrix-as-counts, RandomState API, tie-handling);
all code-level, rerun clean.
