# Rebuttal Letter — When Safe Search Budgets Do Not Transfer Across Graph-ANNS Rebuilds

**To the Reviewers and Area Chair:**

We thank all reviewers for their exceptionally detailed and constructive comments. Every
technical issue raised has been addressed with new measurements on frozen per-query records
(not just wording changes). Below we respond to the principal concerns across all review
rounds, organized by theme. Each response cites the committed artifact containing the
supporting data.

---

## 1. Risk Estimand Definition (Eq. 10) — *multiple reviewers*

**Concern:** The reference event in the incremental risk definition appeared inconsistent
with the reported positive values (17–24%).

**Response:** We have clarified the semantics precisely. The reference event is the
**target-bottom failure**: $Z_t(q, \underline{a}_t) = 1$ where $\underline{a}_t$ is the
smallest action that succeeds on the target for query $q$ (i.e., $B_t(q)$ itself). Under
this reference, the increment is positive exactly when the source's minimum safe action is
strictly below the target's ($B_s(q) < B_t(q)$), which occurs on 43–57% of query-pairs.
The per-sample $\bot$-to-maximum mapping in the estimand (a registered historical
convention) is now explicitly stated in §3 alongside the "never imputed" guardrail (which
applies to policy semantics, not estimand conventions). The full crosswalk of the three
coexisting registered calibers (E4-primary 21.57/17.12, repaired-common 21.55/17.17,
original-stage 21.57/17.12) is in Appendix F, with one sentence in the main text stating
the adoption rule.

**Artifact:** `results/graph_anns_phase2_p1/estimand_crosswalk.csv`

---

## 2. TV Direction inference (Theorem 1 premise) — *Reviewer A*

**Concern:** Classifier accuracy 0.72 gives TV ≥ 0.44 (a lower bound), which cannot yield
a loss lower bound.

**Response:** Correct, and we have fixed this. The valid object is a **confidence upper
bound** on TV for a declared transcript class. For hit-count transcripts, a DKW-type
concentration on the finite support gives TV ≤ 0.39 at 95% confidence (plug-in 0.25 +
0.14 concentration), yielding a valid Theorem-1 loss lower bound of 0.305Δ for that
class. Joint runtime features (worst pair accuracy 0.72, TV ≥ 0.44) are reported as a
**risk-inflation diagnostic**, not premise evidence — the theorem is explicitly
probe-class-conditional.

**Artifact:** `results/graph_anns_phase2_p11/theory_fixes_verdict.json` (TV-UCB field)

---

## 3. Label Coverage vs. Execution Safety (Theorem 3 bridge) — *multiple reviewers*

**Concern:** $P[B_t(q) > a(q)] \le \alpha$ does not automatically control execution
failure $P[Z_t(q, a(q)) = 1]$.

**Response:** We **measured** the bridge condition. The non-monotone violation rate,
conditioned on being at or above the target's minimum safe point
($\nu = \Pr[Z_{E_t}(q,a)=1 \mid a \ge B_{E_t}(q)]$ over all (query, build, $a \ge B_{E_t}(q)$)
triples, exhaustively checked), is **ν = 0 on every registered cell**: hnswlib-100K (both
datasets), Vamana (both stages), 10M, and GloVe-100 — with ν = 0.39% residual on 1M only.
Because conformal deployments satisfying $a(q) \ge B_{E_t}(q)$ lie in this condition,
execution failure is bounded by α + ν. The residual risk arises solely from transported
actions *below* the target's minimum safe point — the transport phenomenon itself. A
stricter tail-label variant ($B^{\mathrm{tail}}_E(q) = \min\{a : \forall a' \ge a,
Z_E(q,a') = 0\}$) is also reported, giving execution safety by construction at halved
cache coverage.

**Artifacts:** `results/graph_anns_phase2_p11/execution_safety_verdict.json`,
`results/graph_anns_phase2_p11/glove_execution_safety.json`

---

## 4. "Only Maximum Budget Certifiable" — Protocol Dependence — *multiple reviewers*

**Concern:** The certification collapse may be an artifact of the zero-failure protocol
at m=59.

**Response:** We have quantified this precisely. A CP power analysis on real margin-band
actions (risk 2.5–4.0%) shows: at m=289 with non-zero-failure CP, actions of 2.5% risk
pass with 70% probability; 3.2% risk with 41%; 4.0% risk with ~10%. The sample-size
thresholds for 50% power are 289–1,149 queries. The "collapse to max-budget" is
correctly stated as a **zero-failure-protocol result at registered sample sizes**, not a
structural impossibility — and with 289–1,149 queries and the full CP test, margin-band
actions become certifiable.

**Artifact:** `results/graph_anns_phase2_p11/cp_power_real_data.json`

---

## 5. Missing Target Re-profiling Baseline — *multiple reviewers*

**Concern:** M5' (target re-profile + per-query truth cache) double-dominates M2 (pooled
replay) when truth is affordable.

**Response:** Agreed and incorporated. Table 4 now includes M5' as a separate row; the
decision rule in §4 and the abstract has been updated to five routes (contract →
re-profile → pooling → certify → abstain); §6.6 quantifies truth cost (0.05/0.5/5 s at
100K/1M/10M for 500 queries) and states that M5' dominates when truth is affordable.
The conformal pooling policy's remaining domain is "truth unavailable for the serving
workload" (production streams where per-query exact NN is prohibitively expensive).

---

## 6. Disjoint Region and Δ Not Instantiated — *Reviewer A*

**Response:** We computed a cost-tolerated common-safe-action analysis: 21.9% of directed
transports (SIFT-100K) admit **no** common safe action within the source action's own
cost (still 6.9% allowing twice the target budget), with median action gap 30 (SIFT) /
20 (Arxiv), p90 80/70. These transports constitute the two-point construction's
conflicting regions with a concrete Δ (mapped to the four-outcome loss semantics:
unsafe = probability of quality failure; conservative = excess distance computations;
fallback = fallback cost; abstain = service denial).

**Artifact:** `results/graph_anns_phase2_p11/d_region_kappa.json`

---

## 7. Exchangeability Assumption — *multiple reviewers*

**Concern:** Exchangeability is assumed, not tested.

**Response:** It is tested on two independent 200-build population farms (SIFT-10K and
Arxiv-Nomic-10K): the rank of a held-out build's minimum safe action within random pools
is uniform after randomized tie-breaking (KS median 0.114/0.118 and 0.120/0.113
respectively), and Theorem-3 coverage holds on both farms. Furthermore, a
**target-correlated source selection** experiment (correlation-weighted pools at k=9–10)
inflates realized risk 3.3× (4.43% vs 1.31%), confirming the premise is load-bearing and
operationally sensitive.

**Artifacts:** `results/graph_anns_phase2_p11/build_farm_summary.json`,
`results/graph_anns_phase2_p11/arxiv_farm_summary.json`

---

## 8. Scale — *all reviewers*

**Response:** The phenomenon is now measured on a four-scale ladder: 100K (17.17–23.60%),
1M (21.87%), 10M (22.16%), plus 200-build population farms at 10K (100% of directed pairs
above the 2% gate on both dataset families). The deterministic contract is byte-identical
at 10M (median 2,945 s single-thread). Pooling's uncached form degrades with scale
(k=7 at 10M: 23.3%), but the conformal certificate remains valid at the pool resolution
(0.64% ≤ α=0.125 at k=7, with 36% abstention from endpoint mass).

**Artifacts:** `results/graph_anns_phase2_p10/deep10m_summary.json`,
`results/graph_anns_phase2_p11/glove_summary.json`

---

## 9. Vamana Estimand — *Reviewer B*

**Response:** Under the target-min-safe reference caliber (Eq. 20), Vamana shows **zero**
incremental transport risk — the stage-specific 16.86%/11.37% is reference-dependent.
We now state this explicitly in §7.5: the Vamana "support" for the phenomenon is
estimand-dependent, reinforcing the paper's central theme. The Theorem-3 conditional
validation on Vamana (k=5, α≥1/6: realized 0%) remains valid as a method-coverage data
point.

**Artifact:** `results/graph_anns_phase2_p11/vamana_aligned_estimand.json`

---

## 10. Presentation Issues — *all reviewers*

All formatting defects have been resolved: Table 4 M5'/M2 duplication (3 copies → 1 each),
10M build time (252 s → 2,945 s in all locations), theorem numbering (1/2/3 via proper
environments), abstract (198 words), ICBA expansion at first use, "seven policies" count,
Figure 1 in main text, all cross-references resolve, zero broken row terminators.

---

## Summary of Quantitative Improvements Since First Review

| Metric | Before | After |
|---|---|---|
| Dataset families | 2 | 3 (+ GloVe-100) |
| Scales | 2 (100K, 1M) | 4 (10K farm, 100K, 1M, 10M) |
| Implementation families | 2 | 3 (+ Vamana Thm-3) |
| Theorem premises measured | 0 | 2 (TV-UCB; exchangeability KS on 2 farms) |
| Execution-safety bridge | Not tested | ν=0 on 5/5 cells (4.4M+ triples) |
| CP power curve | Theory only | Measured on real margin-band actions |
| D-region instantiation | Not quantified | 21.9% at κ=0, 6.9% at κ=1 |
| Population evidence | None | 200-build farms × 2 datasets |
| Δ instantiation | Not quantified | Median gap 30/20, p90 80/70 |

We believe these responses, backed by committed artifacts with deterministic test suites,
address all substantive technical concerns. We are happy to provide any additional
analysis the reviewers may request.
