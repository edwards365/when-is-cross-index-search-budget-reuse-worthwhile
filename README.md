# Graph-ANNS Rebuild Portability

**Hidden build environments, safety limits, and certified recovery for query-adaptive search budgets**

This repository studies a deployment question that is usually hidden by fixed-index evaluation:

> Does a query-adaptive search-budget policy learned on one Graph-ANNS build remain safe and efficient after the index is rebuilt?

The current evidence says **not in general**. The minimum stable budget for a query is conditioned on the concrete index build, including construction history, seed, and implementation. Reusing a source-build policy on an unseen target build can therefore cause under-budget risk or force conservative over-allocation.

The project now focuses on three linked goals:

1. measure rebuild-induced budget-response changes;
2. characterize when source-only portability is information-limited;
3. design a simple rebuild-time protocol that safely chooses among reuse, target recalibration, retraining, and fixed-budget fallback.

## Current scientific status

**Latest sealed decision:** `THEORY_BOUNDARY_STRENGTHENED_METHOD_UNRESOLVED`

What is established:

- rebuilds can reshape per-query sufficient budgets and their ranking;
- a build acts as a hidden conditioning variable for budget decisions;
- source-only policies face a safety–conservatism trade-off when target builds are not identifiable from deployment observations;
- target evidence can restore **fixed-target** safety;
- simple history transfer and the current ASRC design have not shown a stable advantage over risk- and label-matched target recalibration.

What is not established:

- a deployable recovery algorithm with independent Pareto advantage;
- a 5% open-world meta-risk guarantee from the current nine builds per setting;
- a measured end-to-end break-even after exact-truth, calibration, retraining, and fallback costs;
- a general theorem whose novelty goes beyond classical testing, risk-control, and multi-environment inference tools.

The latest oracle-headroom estimates are design-only and are being re-audited for correct mixture, aggregation, and Pareto semantics. They must not be interpreted as deployable algorithm performance.

## Empirical scope

The frozen evidence base includes:

- 81 Graph-ANNS builds;
- 972,000 query–budget records;
- 648 directed source-to-target build pairs;
- SIFT-100K, GloVe-100K, and Arxiv-Nomic-100K;
- hnswlib, Faiss HNSW, and Vamana;
- multiple construction histories and seeds;
- query-level and build-cluster bootstrap analyses.

Important scope boundaries:

- the strongest actionable positive evidence is currently limited to hnswlib;
- GloVe contains endpoint-infeasible/right-censored settings and is not used as clean migration-failure evidence;
- current recovery results are fixed-target design evidence, not outer-build certification;
- validation-dev and formal-test remain sealed.

## Core problem formulation

For environment/build \(E\), query \(q\), ordered budget \(b\), and loss threshold \(\tau\), define the minimum stable sufficient budget:

$$
b_E^*(q)
=
\min
\left\{
b:
L_E(q,b')\le\tau
\text{ for every } b'\succeq b
\right\}.
$$

The stable definition accommodates small non-monotone fluctuations on a finite budget grid.

The central object is therefore not only query difficulty. It is the environment-conditioned response:

$$
(q,E) \mapsto b_E^*(q).
$$

A policy trained on source build \(E_s\) observes incomplete information about target build \(E_t\). When observationally similar builds require conflicting safe budgets, any environment-blind policy must pay through under-budget risk, conservative cost, or fallback.

The lower-bound machinery is Le Cam/testing based and is presented as a problem-specific application rather than a new generic testing technique.

## Theory status

| Component | Current status | Claim level |
|---|---|---|
| Build-conditioned stable budget | Established | Problem definition and empirical mechanism |
| Source-only safety–cost lower bound | Established under stated finite-grid assumptions | Le Cam-style application |
| Endpoint/transfer/certification decomposition | Established | Protocol lemma and evidence taxonomy |
| Fixed-target finite-sample certificate | Established | Classical CP/LTT/RCPS application |
| Query/build hierarchical distinction | Established as a scope limit | Nine builds do not certify a 5% outer tail |
| Active recovery label complexity | Partial | Classical threshold-testing rates only |
| Joint \(m,n,k,M\) recovery theorem | Open | No matched theorem yet |
| Safety–truth–search–fallback frontier | Open | Truth cost is not yet measured |

## Graph-ANNS small-closure tracker

A complete small-scope study is defined by six links:

| Link | Completion condition | Current progress |
|---|---|---:|
| Phenomenon | Cross-build budget changes and transfer failure | ~95% |
| Mechanism | Hidden build condition and information mixing | ~90% |
| Negative theory | Source-only safety–cost boundary | ~80% |
| Positive mechanism | Target evidence restores fixed-target safety | ~70% |
| Method | Certified reuse/recalibrate/retrain/fallback selection | ~20% |
| Independent validation | New queries, new builds, and total wall-clock cost | ~35% |

**Overall Graph-ANNS theory–method closure: approximately 60–65%.**

The remaining bottleneck is not additional evidence that rebuilds matter. It is a simple method with independent validation and complete deployment-cost accounting.

## Planned method: rebuild-aware certified selection

The next method stage is a rebuild-time selector, provisionally called **Rebuild-Aware Certified Selection (RACS)**.

Given a target rebuild, RACS considers a frozen candidate family such as:

- reuse the source policy;
- recalibrate it with target sentinels;
- profile or retrain a target-specific policy;
- use a fixed safe endpoint.

For candidate policy \(\pi_j\), a target certificate produces a risk upper bound \(U_j\). The eligible set is:

$$
\mathcal A=\{j:U_j\le\delta\}.
$$

For an anticipated workload \(N\), RACS selects:

$$
\widehat j
=
\arg\min_{j\in\mathcal A}
\left[
C_{\mathrm{setup},j}
+
N C_{\mathrm{online},j}
\right].
$$

If no candidate is certified, it falls back to the fixed safe endpoint.

RACS is a **planned method**, not a confirmed contribution. Its validation requires untouched queries, new builds, and measured truth/profiling/retraining/search costs.

## Key experimental stages

| Stage | Branch or commit | Main conclusion |
|---|---|---|
| Cross-index boundary | [`b82abf6`](https://github.com/edwards365/navigation-aware-resistance-hnsw/commit/b82abf6bab8aae54b23aee5ccce5cde0ba5a3412) | Operational cross-history effect does not generalize uniformly across implementations |
| Theory lock | [`exp/icba_theory_lock`](https://github.com/edwards365/navigation-aware-resistance-hnsw/tree/exp/icba_theory_lock) | Negative framework locked; one proposition restricted |
| Micro closure | [`exp/icba_micro_closure`](https://github.com/edwards365/navigation-aware-resistance-hnsw/tree/exp/icba_micro_closure) | Closed-world recovery does not imply open-world portability |
| Open-world autopsy | [`exp/icba_open_world_autopsy`](https://github.com/edwards365/navigation-aware-resistance-hnsw/tree/exp/icba_open_world_autopsy) | Support/identifiability failure remains after endpoint controls |
| Theory elevation | [`exp/icba_theory_elevation`](https://github.com/edwards365/navigation-aware-resistance-hnsw/tree/exp/icba_theory_elevation) | General theory strengthened; no deployable recovery channel |
| Positive recovery closure | [`exp/icba_positive_recovery_closure`](https://github.com/edwards365/navigation-aware-resistance-hnsw/tree/exp/icba_positive_recovery_closure) | Target recalibration works; history adds no stable value |
| Zero-overlap method closure | [`exp/graph_anns_positive_method_closure`](https://github.com/edwards365/navigation-aware-resistance-hnsw/tree/exp/graph_anns_positive_method_closure) | Earlier positive effect does not replicate as a new method |
| ASRC semantic repair | [`exp/asrc_semantic_repair`](https://github.com/edwards365/navigation-aware-resistance-hnsw/tree/exp/asrc_semantic_repair) | Fixed-target safety survives repair; method increment fails |
| Pareto/recovery audit | [`exp/asrc_pareto_recovery_boundary`](https://github.com/edwards365/navigation-aware-resistance-hnsw/tree/exp/asrc_pareto_recovery_boundary) | Theory boundary strengthened; method remains unresolved |

Each sealed stage retains its own report, decision manifest, derived tables, tests, and checksums.

## Next gates

The immediate sequence is:

1. re-audit randomized-mixture, environment-oracle, pair-oracle, and Pareto calculations;
2. stop ASRC if corrected headroom disappears;
3. if headroom remains, test a deployable early signal with active selection and an independent random certificate;
4. implement RACS only after the signal and cost gates pass;
5. evaluate on untouched queries and new builds;
6. record exact-truth, sentinel, certification, retraining, fallback, and online latency;
7. extend to a second Graph-ANNS implementation before making a general method claim.

A neural early-exit setting is a possible later second domain for a broader hidden-environment safe-compute theory. LLM budgeting is intentionally deferred because quality, monotonicity, and ground-truth costs are substantially harder to control.

## Reproducibility and evidence policy

- Positive and negative results are retained.
- Oracle lanes are labeled non-deployable.
- Design, calibration, evaluation, validation, and formal-test roles are kept distinct.
- Query-level resampling is not used as a substitute for independent build uncertainty.
- Missing costs are reported as `NOT_ESTIMABLE`.
- The legacy 123-item baseline checksum is only conditionally reproducible: 111 entries match, eight differ, and four untracked cache files are absent.
- Newer stages maintain their own checksums and do not overwrite frozen outputs.

## Historical origin

The repository began as a feasibility study of effective-resistance-guided graph rewiring. Those artifacts remain part of the project history, but they are no longer the active paper story. The current focus is rebuild portability and certified recovery of query-adaptive Graph-ANNS budgets.

## Current paper positioning

The strongest current route is a Graph-ANNS rebuild-portability systems paper:

- a new deployment problem and measurement;
- a carefully scoped information-limit explanation;
- endpoint-aware and build-aware statistics;
- certified target recovery baselines;
- complete rebuild-time cost accounting.

A broader hidden-environment safe-compute theory will be pursued only if a deployable recovery signal and a nonseparable theory beyond standard active testing and risk control are established.
