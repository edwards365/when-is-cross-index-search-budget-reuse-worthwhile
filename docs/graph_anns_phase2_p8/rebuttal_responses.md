# Rebuttal responses (P8 evidence cycle)

Two reviews: R1 (5/10, confidence 4), R2 (6/10, confidence 4). All new numbers below are
machine-verified in results/graph_anns_phase2_p8/ (tests 12/12).

## To Reviewer 1

### C1 / Q1 — quality-threshold sensitivity (your explicit 5->6 condition)
We computed h in {8,9,10} for every cell including those lacking registered h-rows
(`h_sensitivity.csv`), using the same family-risk estimator as the grid-sensitivity
section (P4):

| cell | h=8 | h=9 | h=10 |
|---|---|---|---|
| hnswlib SIFT (registered S1) | 15.60% | 19.10% | 22.03% |
| hnswlib Arxiv (registered S1) | 9.36% | 13.39% | 17.60% |
| clean Faiss SIFT (new) | 10.56% | 16.81% | 23.67% |
| clean Faiss Arxiv (new) | 5.96% | 10.32% | 17.93% |
| SIFT-1M preregistered (new) | 19.77% | 22.55% | 27.95% |

Risk decreases monotonically as the threshold relaxes, but the MINIMUM over all cells and
h=8 is 5.96% - three times the 2% materiality gate. The phenomenon is not an artifact of
the exact-retrieval event. We will add this table to Section 7.

### Q3 - origin-unlocated aggregates
The three flagged aggregates are quarantined in Appendix G's footnote and the artifact;
re-derivation from row-level records is in progress (two of the three have candidate
derivations already computed in the audit CSVs); if a re-derivation disagrees with the
quoted value, the sentence will be rewritten around the reproducible number or dropped.

## To Reviewer 2

### Q2 / W4 - richer probe features (your requested preliminary experiment)
We re-ran the two-sample distinguishability test with three feature families
(`rich_probe_distinguishability.csv`, 120 pairs, seed 0):
- F1 hit-count transcript (registered class): median 0.49-0.51, max 0.56 - chance, as
  reported;
- F2 runtime features (visited nodes, candidate/result queue stats, median latency at
  ef=10): median 0.56-0.58, max 0.72;
- F3 combined: same as F2.

Runtime features carry weak-to-moderate build signal on a minority of pairs. We will
qualify the Theorem-1 instantiation accordingly: near-indistinguishability is a property
of the hit-count transcript class; for runtime probes the worst measured pair implies
TV >= 2*0.72-1 = 0.44, and the theorem's residual-loss bound becomes 0.28*Delta - the
deployment-loss conclusion survives quantitatively, the "indistinguishable" wording does
not. We consider this an improvement to the paper's precision and thank the reviewer.

### Q4 - gamma sensitivity of the margin verdict (your key question)
Recomputed per target on the same frozen 375-query selection block
(`gamma_sensitivity.csv`):
- gamma = 0.005: 16/24 (SIFT) and 21/24 (Arxiv) targets HAVE a non-maximal action with
  selection risk <= delta - 2*gamma;
- gamma = 0.01: 16/24 and 8/24;
- gamma = 0.02: 0/24 on both.

So the margin condition is NOT absolutely absent - it passes point-estimate-wise at small
gamma. What fails everywhere is the CERTIFICATION step: the margin-band actions carry
3-4% risk, and zero-failure certification at m=94 succeeds with probability
(1-r)^94 ~ 2-6%. We will restate the Section 7.4 verdict as "certification power, not
margin existence, is the binding constraint at registered sample sizes" - a sharper and
more accurate sentence than the current one.

### Q3 - pooling with correlated sources / non-max aggregation
We evaluated quantile pooling (q in {0.5, 0.9, 1.0}; `quantile_pooling.csv`):
- q=0.9 at k=22: 1.07% risk / 45.5% conservatism (SIFT) vs max 0.96% / 48.4% - nearly
  identical; there is no cheaper aggregation point;
- median pooling cuts conservatism to 16-22% but leaves 13-21% risk - unusable.
The response diameter is driven by outlier sources, so order-statistics beyond the 0.9
quantile buy nothing. Exploiting inter-source response correlation is a legitimate open
direction; within the order-statistic family there is no free lunch.

### Q5 - canonical order as default
Quantified in the ablation: order pinning leaves 34.1%/30.8% response variation
(residual transport risk nonzero by construction) at 0.80x/0.93x build time, while the
full contract leaves 0% at 3.52x/1.71x. We will state this trade-off explicitly in the
decision rule: canonical order is the recommended DEFAULT for cost-sensitive settings;
the full contract is required when near-zero transport risk is needed.

### Q1 - deployment-cost quantification
Latency/DistComp quantiles for M1/M2/M5 policies are computable from the frozen per-query
latency columns; this ledger (P8-D) is the next scheduled item and will be added to the
economics section. The current paper's economics matrix already reports the measured
break-even structure: SIFT is NO_FINITE at the certified operating point and Arxiv is
11,832 (search-only) / 104,383 (wall-clock) queries.

### W6/W7 - presentation
We accept both: a scenario -> route -> measured-boundary takeaway table will be added
after the abstract; the hedging density will be consolidated into the claim registry with
single pointers; the 2% gate rationale and the grid-indexed nature of absolute risk
levels will be stated in the abstract's final sentence.
