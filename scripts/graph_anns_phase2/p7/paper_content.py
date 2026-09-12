#!/usr/bin/env python
"""P7: assemble the revised paper content (R1-R12 + P6 integrated) and build the DOCX."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_paper_lib import (para, heading, image, equation, table, package, MEDIA, OUT)

P = []

# ------------------------------------------------------------------ title block
P.append(para("When Safe Search Budgets Do Not Transfer Across Graph-ANNS Rebuilds",
              style="Title", space_after=160))
P.append(para("Anonymous Authors", b=True, align="center", space_after=40))
P.append(para("Paper under double-blind review", align="center", space_after=40, sz=18))
P.append(para("Anonymized artifact accompanies the submission.", align="center", sz=18, space_after=240))

# ------------------------------------------------------------------ abstract
P.append(heading(1, "Abstract"))
P.append(para(
    "Graph approximate nearest-neighbor systems rebuild indexes after data refreshes, maintenance, replica "
    "creation, and randomized construction, yet downstream search-budget policies are commonly reused across "
    "builds. We study when this transport is statistically justified. Each serialized build is modeled as an "
    "algorithmic environment with an implementation-native finite action set, an endpoint-aware failure event, "
    "and a categorical unresolved state. A transcript-limited two-environment reduction shows that, when an "
    "available probe transcript cannot distinguish builds requiring conflicting useful actions, any build-blind "
    "policy must incur unsafe execution, conservative computation, fallback, or abstention in at least one "
    "environment; we instantiate this premise by measuring that registered build pairs have near-chance "
    "transcript distinguishability (total variation at most 0.25) while their per-query responses conflict on "
    "45-57% of queries. A complementary fixed-target theorem gives sufficient conditions for safe recovery, and "
    "we measure where those conditions hold: on the registered grid the positive-margin condition fails for all "
    "48 targets, so certified recovery collapses to the maximum budget or abstention. Operationally, ICBA, a "
    "certified portability audit, and a deterministic-rebuild contract convert these findings into a decision "
    "rule. Across SIFT-100K and Arxiv-Nomic-100K, strictly comparable hnswlib and Faiss HNSW experiments exhibit "
    "75.87-91.07% finite-action safe-budget variation and 17.17-23.60% incremental transport risk, and the "
    "phenomenon replicates at SIFT-1M (21.87%, 95% CI [21.52, 22.21]). A max-over-source pooling baseline over "
    "22 registered builds cuts risk below 1% at 1.34-1.45x per-query-oracle cost, though its source requirement "
    "grows with scale; a learned query-level predictor fails to transfer across builds (risk 21-24%, transfer "
    "R-squared 0.015). Fixing input order and single-threaded construction eliminates measured transport risk "
    "with 1.71-3.52x build overhead; order pinning alone halves response variation at no build-time cost. "
    "Primitive profiling remains cheap at both scales, so we claim neither universal profiling cost nor "
    "open-world recovery.", align="justify", space_after=240))

# ------------------------------------------------------------------ 1 intro
P.append(heading(1, "1  Introduction"))
P.append(para(
    "Graph-based approximate nearest-neighbor search (Graph-ANNS) is often tuned as though an index were a "
    "stable substrate. After rebuilding with unchanged data and nominal hyperparameters, practitioners may reuse "
    "a global budget, query-level predictor, or stopping rule selected on an earlier index. The statistical "
    "premise behind this practice is rarely stated: the policy is assumed to remain safe and useful under a new "
    "realization of the construction algorithm. Reconfiguration can violate that premise through input order, "
    "randomized state, parallel scheduling, graph pruning, software version, or build configuration - even when "
    "the query and data distributions do not change.", align="justify"))
P.append(para(
    "The reconfiguration we study arises in ordinary operation. A vector collection is frequently built more "
    "than once: serving replicas are (re)created on different machines with different insertion orders and "
    "parallel schedules; autoscaling adds replicas; failure recovery and blue-green deploys rebuild from the "
    "same data; library upgrades rebuild under new toolchains. A budget policy calibrated on one replica - a "
    "canary - is then reused across the replica set. We study the risk of this plausible deployment shortcut: "
    "whether calibrated budgets remain safe on independently built replicas of the same collection. We make no "
    "claim that every operator reuses budgets and cite no production incident; the setting is stated as a "
    "plausible, common-shape deployment pattern, and all conclusions are conditional on registered builds.",
    align="justify"))
P.append(para(
    "This issue is not simply a drop in mean recall. Two builds can have similar aggregate quality while "
    "assigning different minimum safe actions to the same query. Reusing a source action can then under-budget a "
    "target build; choosing a uniformly larger action can avoid some failures while paying conservative "
    "computation. Existing adaptive search, cost prediction, and risk-control methods are valuable for a "
    "profiled target index, but their calibration does not automatically transport across an independently "
    "rebuilt index. Conversely, target profiling is not uniformly expensive: our primitive measurements are "
    "sub-second at 100K and 1M scale. The scientific gap is the validity and decision semantics of transport, "
    "not a blanket claim that profiling is prohibitive.", align="justify"))
P.append(para(
    "We formulate build reconfiguration as a finite environment-action problem. For each serialized build and "
    "query, the safe budget is the smallest registered implementation-native action satisfying a quality event. "
    "If no registered action succeeds, we retain a categorical unresolved symbol rather than imputing a larger "
    "numerical budget. Directed transport separates four outcomes that are frequently conflated: unsafe "
    "execution, conservative computation, certified fallback, and abstention. This separation turns an informal "
    "robustness concern into an auditable risk-cost object.", align="justify"))
P.append(para(
    "Our evidence addresses three layers with different strength. First, the query-level safe-budget response "
    "is strongly non-portable across registered rebuilds (17.17-23.60% incremental transport risk at 100K, "
    "replicated at 1M). Second, at the global policy layer we give a constructive answer: pooling 22 source "
    "builds into a per-query conservative action cuts risk below 1%, and certified fixed-action fallback is "
    "possible but only at the maximum registered budget. Third, whether a learned query-level predictor trained "
    "on one build transfers to another is probed directly: it does not (Section 7.5), completing a measured "
    "three-layer boundary rather than an extrapolation.", align="justify"))
P.append(para(
    "Our theoretical contribution separates impossibility from conditional recovery. The negative result is "
    "transcript limited and now empirically instantiated: registered build pairs are nearly indistinguishable at "
    "the transcript level (plug-in total variation at most 0.25 over all 552 pairs at every probe level we "
    "measure) while requiring conflicting actions on up to 57% of queries. The positive result is fixed-target "
    "and finite: endpoint feasibility, action-relevant information, a positive risk margin, independent target "
    "evidence, and a valid fallback or abstention rule suffice for safe screening and certification - and our "
    "per-target audit shows exactly which condition fails in practice (margin, on all 48 registered targets). "
    "The testing inequalities are classical; the contribution is their build-conditioned Graph-ANNS "
    "formulation, operational composition, and measured boundary.", align="justify"))
P.append(para(
    "We instantiate the theory in ICBA, a certified audit rather than a new traversal algorithm. ICBA validates "
    "action semantics and role separation, measures cross-build response heterogeneity, evaluates directed "
    "transport, and certifies only frozen fixed-target actions. The audit yields a cost-ordered, four-way "
    "decision rule: enforce and replay-check a deterministic build contract when feasible; otherwise pool many "
    "source builds when operational history permits; otherwise collect target evidence and certify a frozen "
    "action; if none yields a certified action, abstain. A certificate cannot create a useful action when the "
    "candidate family contains none.", align="justify"))
P.append(para(
    "The main empirical evidence comprises four strictly comparable HNSW data-implementation cells (hnswlib and "
    "Faiss on SIFT-100K and Arxiv-Nomic-100K), a preregistered SIFT-1M replication cell, and two Vamana-style "
    "supporting cells. Finite-action safe-budget variation is 75.87-91.07% at 100K (98.4% at 1M), and incremental "
    "transport risk is 17.17-23.60% with all confidence intervals above the preregistered 2% materiality "
    "threshold. Deterministic single-thread rebuilding reduces measured transport risk to zero in registered "
    "controls while increasing build time by 1.71-3.52x; a descriptive chain ablation attributes the entire "
    "guarantee to single-threading, showing order pinning alone halves variation for free and seed pinning under "
    "parallel construction is inert.", align="justify"))
P.append(para("Our contributions are:", space_after=60))
for c in [
    "We define build-reconfiguration portability using implementation-native actions, categorical unresolved endpoints, and four distinct deployment outcomes, with formal estimands for incremental transport risk and the variation families.",
    "We give a transcript-limited lower bound - whose near-indistinguishability premise we instantiate empirically - and a fixed-target conditional recovery theorem whose five conditions we audit per target, finding the margin condition systematically absent.",
    "We introduce ICBA as a certified diagnostic workflow and derive a deterministic-rebuild contract whose mechanistic ablation isolates the load-bearing clause (single-threading).",
    "We provide clean cross-implementation HNSW evidence at 100K and a preregistered 1M replication, constructive baselines (robust source pooling with measured scale boundaries; select-then-certify with its measured failure), a learned-predictor transfer probe, and supporting Vamana-style evidence, with estimand, uncertainty, and comparability boundaries stated explicitly.",
    "We organize extensive negative method evidence as a theory-guided falsification ladder, identifying whether each route fails at attainability, observability, certification, tail behavior, or economics.",
]:
    P.append(para("\u2022  " + c, space_after=40, indent_first=0, align="justify"))
P.append(para(
    "Figure 1 summarizes the setting. Section 2 positions the problem. Sections 3-4 define the model and theory; "
    "Section 5 presents ICBA and the mitigation contract; Sections 6-8 give the protocol, evidence, and "
    "falsification ladder; Sections 9-10 state limitations and conclusions.", align="justify"))
P.append(image("fig1_setting.png", 12.5,
               "Figure 1. Build reconfiguration induces a policy-transport problem. A source-calibrated action may "
               "under-budget the target build, while a uniformly large action may be safe but conservative. The "
               "build is hidden only relative to the available probe transcript; ICBA separates measurement, "
               "certification, and value."))

# ------------------------------------------------------------------ 2 related work
P.append(heading(1, "2  Related Work"))
P.append(heading(2, "2.1  Graph-based ANNS construction and search"))
P.append(para(
    "HNSW uses a randomized multilayer proximity graph and greedy candidate-list search (Malkov & Yashunin, "
    "2020). NSG approximates a monotonic relative-neighborhood structure (Fu et al., 2019), and DiskANN "
    "introduced Vamana-style robust pruning for memory- and disk-efficient search at scale (Subramanya et al., "
    "2019). Faiss provides an independent optimized HNSW implementation (Johnson et al., 2021). Incremental "
    "graph maintenance can avoid full rebuilding after updates (Xu et al., 2022), and recent work revisits "
    "proximity-graph construction cost and pruning from practice to theory (Prokhorenkova & Shekhovtsov, 2020). "
    "Insertion order and intrinsic dimensionality measurably affect HNSW recall (Elliott & Clark, 2024), and "
    "per-index budget autotuning is an active systems topic (Bae et al., 2026). These systems reduce "
    "construction or maintenance cost; our question is complementary: when a build does change, does a "
    "previously selected safety-critical search action transport to the realized graph?", align="justify"))
P.append(heading(2, "2.2  Query-adaptive search and cost prediction"))
P.append(para(
    "Learned early termination, adaptive exploration, conformal retrieval, and learned query-cost estimators "
    "improve efficiency for a concrete profiled index (Li et al., 2020; Chatzakis et al., 2025; Horchidan et "
    "al., 2025; Wang et al., 2026); distribution-aware adaptive HNSW exploration extends the family (Zhang & "
    "Miller, 2026). They establish that query difficulty is predictable within an environment. Unlike these "
    "methods, we do not propose another predictor; we test whether predictor or budget selected on one "
    "serialized build retains its risk and cost semantics after an independent rebuild - and our probe shows a "
    "representative regressor trained on 23 source builds transfers at chance level (Section 7.5).", align="justify"))
P.append(heading(2, "2.3  Risk control and safe selection"))
P.append(para(
    "Learn-Then-Test, conformal risk control, selective classification, and safe best-arm identification provide "
    "finite-sample tools for selecting or abstaining within a fixed candidate family (Angelopoulos et al., 2025; "
    "Bates et al., 2021; Angelopoulos et al., 2024; El-Yaniv & Wiener, 2010; Wang et al., 2022); the "
    "fixed-confidence sample complexity of such selections parallels best-arm identification (Garivier & "
    "Kaufmann, 2016). ICBA uses these classical tools only for a named target and frozen actions. Its distinct "
    "contribution is to expose when build-conditioned transport invalidates the premise of reuse, and to keep "
    "unsafe execution, conservative cost, fallback, and abstention as separate decisions.", align="justify"))
P.append(heading(2, "2.4  Distribution shift and algorithmic reconfiguration"))
P.append(para(
    "Domain adaptation theory shows that source performance need not determine target performance without "
    "support or structural assumptions (Ben-David et al., 2010; Johansson et al., 2019). Multi-environment "
    "predictive inference treats environments as higher-level sampling units (Duchi et al., 2025). Rebuilding "
    "an index is neither ordinary covariate shift nor a change in the underlying vector dataset: the query "
    "distribution may remain fixed while the algorithmic state changes. We therefore treat each serialized "
    "build and its replay semantics as an environment. This framing supports a precise fixed-target guarantee "
    "while making clear that query bootstrap conditional on registered builds is not an unseen-build confidence "
    "interval.", align="justify"))

# ------------------------------------------------------------------ 3 formulation
P.append(heading(1, "3  Problem Formulation"))
P.append(para(
    "Let E be a preregistered finite set of build environments. An environment E consists of a serialized index "
    "together with its implementation, construction configuration, input permutation, seed when meaningful, "
    "toolchain, and replay semantics. Each implementation has its own finite native action set A_E, and queries "
    "follow a frozen law q distributed as P_Q.", align="justify"))
P.append(para("For action a in A_E, define the endpoint-aware failure indicator and implementation-internal "
              "cost by", align="justify", space_after=60))
P.append(equation(1))
P.append(para("and the minimum observed safe budget by", align="justify", space_after=60))
P.append(equation(2))
P.append(para(
    "The symbol BOT is categorical and is never imputed as the largest action or a larger numerical budget. A "
    "policy observes a transcript T and query-side observables, then returns an action or abstains. Its "
    "absolute target risk is", align="justify", space_after=60))
P.append(equation(3))
P.append(para(
    "We use risk tolerance delta = 0.05, certification error probability alpha = 0.05, and safety margin gamma "
    "> 0 stated per experiment; the materiality gate 0.02 is a preregistered scientific threshold, not a "
    "utility function. \u201cPreregistered\u201d in this paper means frozen in a versioned manifest with commit hash and "
    "timestamp before the corresponding evaluation role was accessed; it does not refer to an external OSF "
    "registration. A rejection event is R. An action a_f is a fallback only if it has independent safety "
    "evidence under the same target and failure event; otherwise rejection produces abstention.", align="justify"))
P.append(para("The primary estimand of Section 7 is the stage-registered endpoint-aware incremental transport "
              "risk", align="justify", space_after=60))
P.append(equation(20))
P.append(para(
    "where the reference risk on the target follows the stage-registered reference construction; for the four "
    "HNSW cells this is the reference event of the repaired h=10 common estimand. Intervals are 95% "
    "query-bootstrap over 5,000 resamples (seed 991) retaining each sampled query's full vector of directed-pair "
    "observations, conditional on the registered build family. Heterogeneity is reported through two separated "
    "variation families,", align="justify", space_after=60))
P.append(equation(21))
P.append(para(
    "finite-action variation and endpoint-state variation; reported separately so response heterogeneity cannot "
    "be attributed to unresolved endpoints. We distinguish registered-grid unresolved, true endpoint "
    "infeasible, and right-censored queries. Current finite grids often cannot separate the latter two, so we "
    "report unresolved mass without promoting it to true infeasibility.", align="justify"))
P.append(table([
    ["Implementation", "Registered build environment", "Native action", "Semantic guardrail"],
    ["hnswlib HNSW", "seed x input order (24 builds/dataset)", "efSearch", "candidate-list control; not an expansion or distance-computation cap"],
    ["Faiss HNSW", "registered input permutation (24 builds/dataset)", "efSearch", "implementation-specific; not numerically equated to hnswlib"],
    ["DiskANN3 / Vamana-style", "registered permutation; fixed build options (12 builds/dataset)", "l_value, beam width fixed to 1", "list size; not equal to HNSW efSearch"],
], widths=[3.4, 5.0, 3.0, 4.5], aligns=["left", "left", "left", "left"],
    caption="Table 1. Implementation-native semantics. Raw action values and distance-computation counts are never compared across implementations."))
P.append(para(
    "Cost naming. ROM-NDC quantities in earlier drafts are renamed DistComp throughout: DistComp(x vs y) is the "
    "ratio of mean numbers of distance computations of x to y, computed only within one implementation. "
    "\u201cNDC\u201d alone is avoided to prevent confusion with NDCG. Per-action cost C_E(q,a) is implementation-internal.",
    align="justify"))

# ------------------------------------------------------------------ 4 theory
P.append(heading(1, "4  Theory"))
P.append(heading(2, "4.1  Main Theorem I: transcript-limited non-portability"))
P.append(para(
    "Consider two build environments E_0, E_1. Under E_i, a procedure observes T distributed as P_i^T and outputs "
    "an action through any randomized Markov kernel measurable with respect to T. Let D_i be the region of "
    "nontrivially acceptable actions in E_i, assume the regions are disjoint, and let the per-environment loss "
    "l_i satisfy l_i >= delta loss 1{a not in D_i} for some delta > 0.", align="justify"))
P.append(para("Theorem 1. Every transcript-based randomized procedure satisfies", space_after=60))
P.append(equation(4))
P.append(para(
    "The decision regions encode actions that avoid conservative cost in one environment and actions that avoid "
    "under-budget failure in the other. If the transcript available under the registered probe budget cannot "
    "identify which region applies, no transcript-measurable policy can uniformly avoid unsafe execution, "
    "conservative computation, fallback, or abstention. The statement quantifies over randomized policies but is "
    "conditional on the transcript laws; it neither claims that every build pair is indistinguishable nor "
    "forbids target probing.", align="justify"))
P.append(para(
    "For an adaptive transcript with m observations and KL divergence K_m between the transcript laws, the "
    "classical Bretagnolle-Huber and Pinsker inequalities give", align="justify", space_after=60))
P.append(equation(5))
P.append(para(
    "Le Cam reduction, total variation, KL chain rules, and the testing inequalities are classical (Yu, 1997); "
    "the domain-specific contribution is the reduction from a wrong build decision to the four Graph-ANNS "
    "deployment outcomes.", align="justify"))
P.append(para(
    "Empirical instantiation (Section 7.5). We measure this premise directly: over all 552 registered build "
    "pairs and probe levels k in {1,3,6} cheapest actions, a strong classifier attributes transcripts to their "
    "build at chance accuracy (median 0.49-0.51), and the exact plug-in total variation between transcript "
    "marginals never exceeds 0.25 - while the same pairs disagree on the per-query minimum safe action for "
    "45-57% of queries. Near-indistinguishability holds at the marginal transcript level; the conflict lives in "
    "the per-query coupling. Substituting TV = 0.25 into Theorem 1 bounds the unavoidable loss below by "
    "0.375*delta for such pairs. The claim is probe-class-conditional, exactly as the theorem requires.",
    align="justify"))
P.append(heading(2, "4.2  Main Theorem II: finite-class conditional recoverability"))
P.append(para(
    "Fix a named target E_t, a frozen family A of M actions, a declared P_Q, and the endpoint-aware loss. "
    "Suppose: (i) at least one action has risk at most delta - 2*gamma; (ii) the selection transcript "
    "distinguishes action-relevant alternatives in the registered class; (iii) a useful action has positive "
    "risk margin; (iv) selection and final certification use independent query roles and the candidate family "
    "is frozen before certification; and (v) rejection invokes an independently justified fallback or "
    "abstention. Let the simultaneous estimation event be", align="justify", space_after=60))
P.append(equation(6))
P.append(para("with probability at least 1 - alpha_sel. Screen actions by estimated risk plus epsilon_R at most "
              "delta, choose the minimum estimated-cost retained action, and certify only the frozen choice on "
              "independent data at level alpha_cert, with alpha_sel + alpha_cert at most alpha. Then",
              align="justify", space_after=60))
P.append(equation(7))
P.append(para(
    "On the estimation event, a minimum-cost safe action with margin is retained and its cost is within "
    "2*epsilon_C of optimal; a unique safe optimum with a larger cost gap is recovered exactly. This is a "
    "sufficient protocol plus necessary obstruction statements, not an if-and-only-if characterization. Section "
    "7.4 audits conditions (i)-(v) per target: (i), (ii), (iv), (v) are satisfiable on the registered grid; "
    "(iii) fails for every one of the 48 targets, because every non-maximal action's risk sits inside the "
    "margin band - a measured boundary, not a claim that certification is impossible.", align="justify"))
P.append(heading(2, "4.3  Certification scale and economic feasibility"))
P.append(para("Classical uniform concentration gives the sufficient order", align="justify", space_after=60))
P.append(equation(8))
P.append(para("With zero observed failures and per-action level alpha_l, exact one-sided Clopper-Pearson "
              "certification requires", align="justify", space_after=60))
P.append(equation(9))
P.append(para(
    "so 59 queries certify a single frozen action, but selection over M = 6 actions under Bonferroni requires "
    "94 - and zero-failure certification passes with probability (1-r)^m at true risk r, which is why the "
    "maximum-budget action (risk 0.008-0.013) certifies only 47-63% of the time at m = 59 in replay. Query "
    "count, environment count, action count, grid resolution, and service workload control different errors "
    "and are not interchangeable. For economics, let", align="justify", space_after=60))
P.append(equation(10))
P.append(para("If the per-query net gain is nonpositive, no finite workload breaks even; otherwise the "
              "threshold is", align="justify", space_after=60))
P.append(equation(11))
P.append(para("This is an accounting identity, not an efficiency theorem. Mean gain cannot imply p95 or p99 "
              "improvement.", align="justify"))
P.append(table([
    ["Result", "Core assumptions", "Guarantee", "Status of tools"],
    ["Transcript-limited lower bound", "conflicting useful regions; specified probe transcript laws", "risk-conservatism-fallback-abstention loss conditional on distinguishability", "classical testing; Graph-ANNS instantiation; premise measured (Sec. 7.5)"],
    ["Conditional recovery", "feasibility, identifiability, margin, independent target evidence, fallback or abstention", "fixed-target familywise safety and near-optimal safe cost", "new domain-specific combination; margin audited per target (Sec. 7.4)"],
    ["Certification scale", "finite frozen M, margin gamma", "sufficient sample order and zero-failure threshold", "classical concentration and exact binomial bound"],
    ["Economic gate", "complete auditable costs", "finite break-even iff per-query denominator is positive", "accounting identity"],
], widths=[3.2, 4.0, 4.2, 4.5], aligns=["left", "left", "left", "left"],
    caption="Table 2. Theoretical results, assumptions, novelty boundary, and their empirical instantiation."))

# ------------------------------------------------------------------ 5 ICBA
P.append(heading(1, "5  ICBA: Certified Audit and Actionable Mitigation"))
P.append(para(
    "ICBA receives registered source and target builds, implementation-native actions, disjoint "
    "design/selection/certification/evaluation roles, exact truth for authorized labeled roles, one "
    "endpoint-aware failure event, implementation-internal costs, risk parameters, and a frozen candidate "
    "family. It returns one of four scientifically distinct outcomes: certified reuse, target-specific "
    "recalibration/certification, execution of an independently justified fallback, or abstention. It never "
    "treats the maximum registered action as safe without evidence.", align="justify"))
P.append(para(
    "The procedure first validates role disjointness, replay, native action semantics, and cost fields. It then "
    "constructs the categorical safe-budget response without endpoint imputation and measures directed "
    "source-to-target transport. Any candidate selected using authorized target data is frozen before "
    "independent certification, with familywise control across the registered actions. Finally, ICBA audits "
    "mean cost, p95/p99 behavior, offline truth and control cost, fallback rate, and break-even separately. "
    "Missing costs remain not estimable rather than being silently replaced by a proxy.", align="justify"))
P.append(image("fig2_workflow.png", 12.5,
               "Figure 2. ICBA workflow. The procedure validates semantics before estimating transport, separates "
               "selection from certification, and treats fallback and abstention as distinct terminal outcomes."))
P.append(para(
    "A complementary mitigation removes, rather than learns, the build environment. The deterministic-rebuild "
    "contract fixes the input permutation, construction seed where exposed, implementation and toolchain, and "
    "requires single-threaded (or demonstrably deterministic-parallel) construction plus byte-level index replay "
    "and search-output identity checks. Under these registered conditions the contract mechanically reuses the "
    "same serialized environment; it is not an unseen-build guarantee and does not cover data refreshes, version "
    "changes, or hardware changes. ICBA therefore implements a cost-ordered decision rule: (1) enforce a "
    "verified deterministic contract when feasible; (2) otherwise deploy robust source pooling when the "
    "operational history retains enough prior builds (uncertified, risk below 1% at 100K with 22 sources; "
    "scale-dependent); (3) otherwise collect target evidence and certify a frozen action, accepting that on "
    "grids like ours only the maximum budget clears certification; (4) abstain. When pooling is unavailable and "
    "determinism is unaffordable, canonical-order pinning alone halves response variation at no build-time cost "
    "(Section 7.3).", align="justify"))

# ------------------------------------------------------------------ 6 protocol
P.append(heading(1, "6  Experimental Protocol"))
P.append(para(
    "We evaluate SIFT-100K (128-dimensional L2 vectors) and Arxiv-Nomic-100K (768-dimensional normalized "
    "embeddings under the registered L2/cosine-equivalent preprocessing) at Recall@10 with hit requirement "
    "h = 10, i.e., the returned top-10 must contain all ten ground-truth neighbors. hnswlib and the clean "
    "Faiss-100K experiments contain 24 registered builds per dataset and all 552 non-diagonal directed pairs; "
    "the Vamana-style stage contains 12 builds and 36 preregistered source-to-held-out-target directions. Each "
    "cell uses 750 evaluation queries. Native action grids are reported per implementation (hnswlib "
    "10/20/40/80/120/200; Faiss 16/32/64/128/256/512); raw efSearch and l_value values are never equated across "
    "systems. For Vamana, beam width is fixed to one, so its evidence is explicitly configuration conditional.",
    align="justify"))
P.append(para(
    "SIFT-1M replication cell (preregistered). Eight builds (4 seeds x 2 insertion orders; M=16, "
    "efConstruction=100, single-threaded, mirroring the registered 100K configuration), a 500-query evaluation "
    "role sampled with seed 991 from the ann-benchmarks test split, exact top-10 truth from the published "
    "ground truth, the registered 100K action grid, and all metrics frozen in a manifest committed before any "
    "build or search. A query/base content-overlap gate (zero required) passed before any risk number was "
    "computed; two additional same-configuration builds verified byte-identity of the contract at 1M.",
    align="justify"))
P.append(para(
    "Data hygiene. Evaluation queries are unique and content-hash disjoint from the indexed base and historical "
    "analysis roles in the clean Faiss-100K rerun; the Vamana-style stages receive the same audit in this "
    "revision: query/base ID, raw-content, and normalized-content overlap, internal duplicates, and "
    "cross-stage leakage against the hnswlib base are all zero on both datasets (historical-role raw-content "
    "overlap remains not estimable because role vectors were not retained; the Vamana base is a separately "
    "registered snapshot, consistent with never claiming cross-family numerical equality). Serialized-index "
    "replay, identifier mapping, and native/tracer agreement are checked before inference. No future-replication "
    "truth or outcome is used; any hash-only access status is retained in the artifact audit rather than "
    "promoted to a scientific claim.", align="justify"))
P.append(para(
    "Primary intervals use 5,000 query-bootstrap repetitions with seed 991 while retaining each sampled query's "
    "full vector of directed-pair observations. The intervals are conditional on the registered builds, not "
    "confidence intervals over unseen rebuilds. The primary estimand is the stage-registered endpoint-aware "
    "incremental transport risk (Eq. 20). For the four HNSW cells, the clean evidence supports a common "
    "source-action convention; the Vamana stage used a different reference construction, and its frozen records "
    "cannot reconstruct the fully harmonized HNSW estimand, so we report Vamana as supporting stage-specific "
    "evidence rather than merging all six cells into one numerical range.", align="justify"))

# ------------------------------------------------------------------ 7 results
P.append(heading(1, "7  Results"))
P.append(heading(2, "7.1  Strictly comparable HNSW transport evidence"))
P.append(para(
    "The clean hnswlib and Faiss experiments agree on the main conclusion. Across the four data-implementation "
    "cells, 75.87-91.07% of evaluation queries exhibit finite-action safe-budget variation across registered "
    "builds, whereas endpoint-state variation is only 0.53-2.67%. Incremental source-to-target transport risk "
    "ranges from 17.17% to 23.60% (Table 3). Every 95% query-bootstrap interval excludes the preregistered 2% "
    "materiality threshold. Thus the primary signal is switching among finite native actions, not a numerical "
    "artifact created by unresolved endpoints.", align="justify"))
P.append(table([
    ["Implementation", "Dataset", "Builds/pairs", "V_fin", "Incremental risk [95% CI]", "V_end", "Within-impl. cost"],
    ["hnswlib HNSW", "SIFT-100K", "24 / 552", "89.33%", "21.55% [20.76, 22.33]", "2.67%", "DistComp +19.45% [18.13, 20.77]"],
    ["hnswlib HNSW", "Arxiv-Nomic-100K", "24 / 552", "75.87%", "17.17% [16.33, 18.06]", "2.00%", "DistComp +14.88% [13.50, 16.18]"],
    ["Faiss HNSW", "SIFT-100K", "24 / 552", "91.07%", "23.60% [22.78, 24.39]", "0.53%", "N/E: batch-cumulative counter"],
    ["Faiss HNSW", "Arxiv-Nomic-100K", "24 / 552", "75.87%", "17.77% [16.86, 18.68]", "1.87%", "N/E: batch-cumulative counter"],
], widths=[2.6, 3.0, 1.8, 1.3, 3.6, 1.2, 3.0],
    caption="Table 3. Registered cross-family evidence at Recall@10 with h=10. HNSW rows share the repaired common "
            "estimand; the estimand crosswalk in Appendix F tabulates the coexisting registered values."))
P.append(image("fig3_crossfamily.png", 13.5,
               "Figure 3. Cross-family evidence. Bars show safe-budget response variation; points show incremental "
               "transport risk with 95% query-bootstrap intervals. Vamana marks (daggered in Table 4) retain their "
               "stage-specific estimand and are supporting rather than harmonized evidence."))
P.append(para(
    "Robustness checks do not alter this conclusion. Removing the eight queries with the largest hnswlib risk "
    "contribution leaves increments of 21.40% and 16.90%; deleting the top 1% of Faiss risk contributors leaves "
    "23.43% and 17.53%; all 24 leave-one-build estimates remain positive on every cell. These are robustness "
    "diagnostics conditional on the registered build family, not a population model for future rebuilds.",
    align="justify"))
P.append(heading(2, "7.2  Vamana-style supporting boundary"))
P.append(table([
    ["Implementation", "Dataset", "Builds/pairs", "Category var.", "Stage risk [95% CI]", "Mixed censoring", "Cost (descriptive)"],
    ["DiskANN3/Vamana-style\u2020", "SIFT-100K", "12 / 36", "71.07%", "16.86% [15.65, 18.10]", "0.27%", "~1.00% [-0.94, 3.04]"],
    ["DiskANN3/Vamana-style\u2020", "Arxiv-Nomic-100K", "12 / 36", "48.27%", "11.37% [10.20, 12.60]", "0.80%", "~1.11% [-1.05, 3.22]"],
], widths=[3.2, 3.0, 1.6, 1.8, 3.6, 1.6, 2.9],
    caption="Table 4. Vamana-style boundary panel (dagger: stage-specific estimand, beam width one, asymmetric "
            "directions; not harmonized with the HNSW estimand and not merged into its range)."))
P.append(para(
    "The Vamana-style stage reproduces the risk direction on both datasets under its original stage-specific "
    "endpoint estimand. It uses 12 builds, 36 asymmetric directions, beam width one, and a reference "
    "construction that cannot be harmonized exactly from the frozen event table. It therefore broadens the "
    "construction-family scope without supporting numerical equality to HNSW. Cost is even less universal: "
    "hnswlib shows resolved within-implementation DistComp penalties of 19.45% and 14.88%, whereas the "
    "Vamana-style estimates are near 1% with intervals crossing zero, and clean Faiss-100K distance-computation "
    "cost is not estimable because the exposed counter is batch cumulative.", align="justify"))
P.append(heading(2, "7.3  Deterministic rebuilding removes the registered environment"))
P.append(para(
    "We fix the input order, seed, thread count, implementation, and toolchain, and require byte-identical "
    "serialization and search replay. Three repeated builds per dataset satisfy all identity checks and have "
    "measured transport risk zero. Relative to the original multithreaded construction, the contract preserves "
    "Recall@10 within 0.0004, leaves p95/p99 safe budgets unchanged, changes mean safe budgets by ratios 0.976 "
    "(SIFT) and 0.999 (Arxiv), and increases build time by 3.52x and 1.71x. This is an actionable "
    "environment-elimination contract - a hnswlib deterministic construction control - not a recovery algorithm "
    "for changed data or software.", align="justify"))
P.append(table([
    ["Result", "SIFT-100K", "Arxiv-Nomic-100K", "Interpretation"],
    ["Deterministic transport risk", "0", "0", "registered same-data/toolchain contract"],
    ["Recall difference vs. original build", "+0.00027", "-0.00040", "within the registered 0.001 tolerance"],
    ["Mean safe-budget ratio", "0.976", "0.999", "descriptive common-feasible summary"],
    ["p95 / p99 budget ratio", "1.00 / 1.00", "1.00 / 1.00", "no measured tail change"],
    ["Build-time ratio vs. original", "3.52x", "1.71x", "determinism has offline overhead"],
    ["59-query primitive profiling", "HNSW 0.117 s; Faiss 0.017 s", "HNSW 0.994 s; Faiss 0.248 s", "100K profiling is cheap and operator dependent"],
], widths=[4.4, 3.6, 3.6, 4.3],
    caption="Table 5. Contract outcomes and primitive profiling economics (8-thread resident measurements; "
            "primitive operations only, not a deployment ledger)."))
P.append(para(
    "Chain ablation (descriptive). A four-tier chain - D0C (random order, 8 threads, random seeds), D1 (canonical "
    "order pinned), D2 (seed pinned), D3 (single-threaded) - attributes the contract's effect: pinning the "
    "insertion order to a canonical order halves minimum-safe-action variation (68.3 to 34.1% on SIFT; 63.2 to "
    "30.8% on Arxiv) at build-time ratios 0.80x and 0.93x, i.e., free. Pinning the seed under 8-thread "
    "construction is nearly inert (-1.3 and -4.3 points), and the six D2 builds with identical order and seed "
    "produce six distinct serialized indexes: parallel scheduling is a residual nondeterminism source that the "
    "exposed seed does not control. Single-threaded construction is therefore the necessary and sufficient "
    "registered clause for byte identity (3/3 identical, variation 0) and carries the entire overhead (4.73x "
    "and 1.86x relative to the pinned 8-thread tier; 3.52x and 1.71x relative to D0C). The ablation is a chain, "
    "not a full factorial; effects are descriptive.", align="justify"))
P.append(image("fig6_ablation.png", 14.0,
               "Figure 6. Deterministic-contract ablation (descriptive chain). Left bars: minimum-safe-action "
               "variation per tier; right line: median build time. Order pinning halves variation for free; "
               "single-threading removes all variation and carries the build overhead."))
P.append(heading(2, "7.4  Constructive baselines and certification"))
P.append(para(
    "We evaluate six policies on the hnswlib cells by retrospective replay over the frozen per-query records "
    "(roles 375/94/281 disjoint, seed 991; bootstrap as registered). Table 6 reports target-truth usage, risk "
    "under the four-outcome semantics, DistComp versus the per-query oracle, and certification outcomes.",
    align="justify"))
P.append(table([
    ["Method", "Target truth", "Risk (SIFT / Arxiv)", "DistComp", "Certification"],
    ["M1 naive source transport (k=1)", "0", "21.89% / 18.06%", "2.6x / 2.7x", "none"],
    ["M2 max-over-source (k=22)", "0", "0.18% / 0.09% (abstain 2.4% / 2.7%)", "1.45x / 1.34x", "uncertified; LOBO max 2.1%"],
    ["M3 frozen max-action CP cert. (M=1, m=59)", "59 q/target", "0.87% / 1.36% (eval set)", "4.16x / 5.28x", "certifies 71% / 38% of draws (P=(1-r)^59)"],
    ["M4a point-screen select-then-certify", "469 q", "-", "-", "0/48 certified (zero-failure violated)"],
    ["M4b Theorem-2 screen then certify", "469 q", "-", "-", "0/48; screens ef=120 (8/24) or 200 (16/24), margin too thin"],
    ["M5 always maximum action", "0", "0.80% / 1.26%", "4.09x / 5.14x", "not automatically safe (endpoint mass)"],
    ["M6 per-query oracle", "full truth", "endpoint mass only", "1.00x", "non-deployable reference"],
], widths=[4.6, 1.8, 4.2, 1.8, 3.5],
    caption="Table 6. Constructive decision table (hnswlib, registered grid, retrospective replay). M2 dominates "
            "on risk at 1.34-1.45x oracle cost but requires 22 retained source builds and is uncertified; "
            "certified routes collapse to the maximum budget."))
P.append(image("fig4_pooling.png", 14.0,
               "Figure 4. Robust source pooling: transport risk versus number of pooled source builds (mean and "
               "p95 over 50 draws; log scale). k=1 reproduces the registered naive-transport risks; k >= 10 "
               "falls below 2.4% at 100K. At SIFT-1M the decay is slower (k=7 still leaves 10.4%): the pooling "
               "requirement grows with scale."))
P.append(image("fig5_plane.png", 11.5,
               "Figure 5. Constructive decision plane (hnswlib). Risk versus DistComp against the per-query "
               "oracle; horizontal gates at 2% (materiality) and 5% (risk tolerance). M2 occupies the "
               "low-risk/low-cost corner without certification; certified M3 coincides with M5."))
P.append(para(
    "Theorem-2 verdict. Conditions (i), (ii), (iv), (v) are satisfiable on the registered grid; (iii) fails for "
    "all 48 targets: every non-maximal action's risk lies inside the margin band, so Theorem-2 screening passes "
    "(it selects ef=120 on eight targets and ef=200 on sixteen per dataset) but zero-failure certification then "
    "fails on every target. The certified route collapses to maximum-budget-or-abstain, and even the maximum "
    "action certifies only with probability 0.47-0.63 at m = 59 because its residual risk (0.008-0.013, "
    "concentrated in always-infeasible queries) violates the zero-failure requirement in roughly half the "
    "draws. This is a measured boundary of the recovery theorem on this grid - conditional, not an "
    "impossibility claim. Pooling is the constructive winner when operational history retains enough prior "
    "builds; its uncertainty remains a registered-family bootstrap, not an unseen-build guarantee.",
    align="justify"))
P.append(heading(2, "7.5  Scale, learned-predictor transfer, and distinguishability"))
P.append(table([
    ["Probe", "Result", "Boundary closed"],
    ["SIFT-1M cell (preregistered; 8 builds, 500 queries)", "incremental risk 21.87% [21.52, 22.21]; V_fin 98.4% vs V_end 13.2%; contract byte-identical; profiling 0.067 s (59q x 6 actions)", "phenomenon replicates at 10x scale (100K: 21.55%)"],
    ["Pooling at 1M", "k=7 leaves 10.4% risk (100K with 22 sources: below 1%)", "pooling's source requirement is scale-dependent"],
    ["Learned predictor (HistGB on ef=10 transcript features)", "transfer risk 23.9% / 21.2% vs naive 21.1% / 17.3%; in-target CV 24.1% / 22.2%; transfer R^2 = 0.015", "layer-3 (learned predictor) non-portability measured; B(q) dominated by build-specific structure"],
    ["Transcript distinguishability (552 pairs, k in {1,3,6})", "classifier accuracy 0.49-0.51 (chance); plug-in TV <= 0.25; coupled disagreement 45-57%", "Theorem 1's near-indistinguishability premise instantiated (probe-class-conditional)"],
], widths=[4.6, 6.5, 4.7],
    caption="Table 7. Preregistered P6 probes: scale replication, pooling boundary, predictor transfer, and "
            "transcript distinguishability."))
P.append(para(
    "The predictor probe deserves emphasis: a regressor trained on 23 source builds predicts the target's "
    "minimum safe action no better than chance (R^2 = 0.015), and even in-target cross-validation leaves 22-24% "
    "risk - the deployment-time transcript of the cheapest action carries almost no information about which "
    "build-specific neighborhood structure makes a larger budget necessary. The three-layer boundary is now "
    "complete: response labels are strongly non-portable (layer 1), global policies have a constructive bounded "
    "answer (layer 2, Section 7.4), and learned per-query predictors do not transfer on these features (layer "
    "3). We did not test richer probe features or model classes; the claim is feature-class-conditional.",
    align="justify"))
P.append(heading(2, "7.6  Economics ledger and grid sensitivity"))
P.append(table([
    ["Component", "hnswlib SIFT", "hnswlib Arxiv", "Faiss SIFT", "Faiss Arxiv", "Vamana (both)"],
    ["Build time (D3 median)", "12.9 s", "46.6 s", "N/E", "N/E", "N/E"],
    ["Profiling, resident 59q (8t)", "0.117 s", "0.994 s", "0.017 s", "0.248 s", "N/E"],
    ["Break-even, search-only", "NO_FINITE", "11,832 q", "N/E", "N/E", "N/E"],
    ["Break-even, wall-clock", "NO_FINITE", "104,383 q", "N/E", "N/E", "N/E"],
    ["Candidate-family replay / control", "N/E", "N/E", "N/E", "N/E", "N/E"],
], widths=[4.4, 2.3, 2.3, 2.3, 2.3, 2.3],
    caption="Table 8. Six-cell economics matrix (selected rows; the full 36-cell matrix with per-cell "
            "NOT_ESTIMABLE reasons is in the artifact). N/E = not estimable from frozen evidence; never imputed."))
P.append(para(
    "Transport risk is grid-indexed: on registered subgrids (drop-min, drop-max, coarse 3-action) mean family "
    "risk stays between 10.3% and 23.8% - always above the 2% materiality gate - while coarser grids "
    "mechanically lower measured risk because the minimum safe action can only grow. We therefore claim "
    "phenomenon-level grid-robustness, not resolution-invariant risk levels, and keep native grids separate "
    "across implementations.", align="justify"))

# ------------------------------------------------------------------ 8 ladder
P.append(heading(1, "8  Theory-Guided Falsification Ladder"))
P.append(para(
    "The transcript-limited lower bound identifies insufficient build information as one possible barrier, while "
    "Theorem 2 states what a fixed-target escape requires. We therefore organize method development as a "
    "falsification ladder rather than a performance tournament. A route advances only if its semantics, "
    "candidate attainability, observable information or structural bridge, independent certification, tail "
    "behavior, and deployment value survive in that order.", align="justify"))
P.append(table([
    ["Recovery family", "Strongest positive evidence", "Decisive limitation", "Inference"],
    ["Reuse and target recalibration", "target evidence restores fixed-target safety in selected designs; predictor probe now quantifies the negative side (R^2=0.015)", "no stable history increment; strict disjoint evaluation removes apparent gain", "fixed-target safety only"],
    ["Build selection and stable construction", "safe-selection theory remains valid; isolated mean/tail gains", "no CI-supported joint action on 72 frozen actions; structural proxies worsen recall or native budgets", "tested generator closed"],
    ["Multi-lane and portal rescue", "portal complementarity replicates after ID repair", "no truth-free trigger; 79.5-93.4% auxiliary-cost compression required", "mechanism only"],
    ["Certified auditor and fallback", "unsafe acceptance controllable; all 36 accepted decisions safe", "accepted decisions collapse to maximum budget; regret 470.34 [458.69, 482.03] / 684.49 [674.99, 694.26]", "diagnostic, not optimizer"],
], widths=[3.4, 4.6, 4.6, 3.2],
    caption="Table 9. Four recovery families and the first prerequisite falsified by sealed evidence; the "
            "16-route casebook is in Appendix G."))
P.append(image("fig7_ladder.png", 14.0,
               "Figure 7. Theory-guided falsification ladder. Each recovery family is pruned at its first "
               "unsupported prerequisite. Partial mechanism evidence is retained without being promoted to a "
               "deployable algorithm."))
P.append(para(
    "Target-only residual recalibration initially reduced mean distance computations by 29.40% (SIFT) and 26.17% "
    "(Arxiv) in a paired fixed-target design; history-assisted variants added only 0.90% [-8.73, 11.25] and "
    "-0.13% [-9.24, 10.26]; under strict disjoint-query cross-fitting the target-only effects became -7.35% and "
    "-12.49%. Build selection failed earlier: among 72 frozen build-budget actions, SIFT had no "
    "point-estimate-or-interval supported jointly feasible action and Arxiv had one point-estimate action with "
    "no interval support. One protected-edge repair preserved graph invariants yet reduced Recall@10 by 0.002 "
    "and worsened both endpoint families. Fixed portal sets showed genuine rescue complementarity (1,064 and "
    "727 additional hits; 426 and 348 threshold rescues) but cost 2.5-2.8x a matched native lane and remained "
    "3.3-4.8 recall points lower; eight preregistered truth-free triggers showed no positive validation "
    "advantage, and a shared-frontier bound implies 79.5-93.4% auxiliary-cost compression before viability "
    "(provenance for these aggregates is itemized in the artifact; three of them are recorded as "
    "origin-unlocated and are being re-derived from row-level records). Finally, the conservative auditor "
    "demonstrated safety without value across 60 retrospective decisions (4 direct reuses, 32 certified "
    "fallbacks, 24 abstentions; all 36 accepted decisions safe, every accepted action at the maximum registered "
    "budget).", align="justify"))

# ------------------------------------------------------------------ 9 limitations
P.append(heading(1, "9  Limitations and Scope"))
P.append(para(
    "Our primary evidence covers two 100K-scale datasets and four comparable HNSW cells, plus one preregistered "
    "1M hnswlib replication; the 1M cell is single-implementation and eight builds. The Vamana extension uses a "
    "different estimand, asymmetric pairs, and beam width one. We do not model future builds, data refreshes, or "
    "open-world safety. Scale, pruning, I/O, and hardware may change effect sizes; clean Faiss "
    "distance-computation cost and Vamana wall-clock/I/O are not estimable, precluding a universal cost claim.",
    align="justify"))
P.append(para(
    "The lower bound is conditional and probe-class-limited; our instantiation covers the registered hit-count "
    "transcript class, and other probe classes (latency, visited counts) may separate builds better. The "
    "recovery theorem requires a useful margin-separated action, which the falsification ladder and the "
    "per-target audit both reject on this grid; richer candidate families might restore it. The 2% gate is a "
    "preregistered scientific threshold, not a deployment utility function.", align="justify"))
P.append(para(
    "The deterministic contract eliminates registered same-data variation but costs 1.71-3.52x more build time "
    "and does not cover changed data, software, or operators; the ablation attributing its effect is a "
    "descriptive chain, not a factorial. At both measured scales primitive profiling is cheap; the decision "
    "rule, not profiling cost, carries the practical weight. The constructive table is a retrospective replay "
    "on registered builds: pooling requires retaining prior builds and their per-query records, and its risk "
    "estimate is an uncertified registered-family bootstrap whose source requirement grows with scale (k=7 "
    "leaves 10.4% at 1M). The predictor probe is one model class on one feature family. Any larger-scale "
    "advantage of reuse remains unverified until truth, control, latency, and I/O costs are measured end to "
    "end.", align="justify"))
P.append(para(
    "The historical baseline remains conditionally reproducible (111/123 matching entries). Later clean reruns "
    "do not erase this limitation. The artifact records hash-only role access, Vamana reference semantics, and "
    "the descriptive - not causal - status of construction-factor comparisons.", align="justify"))

# ------------------------------------------------------------------ 10 conclusion
P.append(heading(1, "10  Conclusion"))
P.append(para(
    "Safe search budgets are properties of a realized Graph-ANNS build, not only of a dataset and nominal "
    "recipe. Across two datasets, two HNSW implementations, and a preregistered 1M replication, rebuilds cause "
    "large finite-action variation and 17-24% incremental transport risk; a Vamana-style study supports the "
    "direction under a distinct estimand. The theory separates transcript-limited non-portability - whose "
    "near-indistinguishability premise we measure directly - from fixed-target recovery, whose margin "
    "condition we find systematically absent on the registered grid. Practically, the evidence orders itself "
    "into a decision rule: verify a deterministic single-threaded rebuild contract when feasible; otherwise "
    "pool many retained source builds, accepting an uncertified but measured risk below 1% at 100K and a "
    "scale-dependent source requirement; otherwise certify a frozen action with declared margin, expecting "
    "only the maximum budget to clear on grids like ours; otherwise abstain. Learned per-query predictors do "
    "not close this gap on deployment-time transcript features. The boundary between what transports and what "
    "must be re-established per build is now measured at every layer we probe.", align="justify"))

# ------------------------------------------------------------------ references
P.append(heading(1, "References"))
REFS = [
 "Angelopoulos, A. N., Bates, S., Candes, E. J., Jordan, M. I., & Lei, L. (2025). Learn then test: Calibrating predictive algorithms to achieve risk control. Annals of Applied Statistics.",
 "Angelopoulos, A. N., Bates, S., Fisch, A., Lei, L., & Schuster, T. (2024). Conformal risk control. International Conference on Learning Representations.",
 "Bae, J., Ham, T. J., Li, A., Chockchowwat, S., & Papakonstantinou, Y. (2026). QBAT: Model-based query budget autotuner for clustering-based approximate nearest neighbor search. Proceedings of the VLDB Endowment.",
 "Bates, S., Angelopoulos, A. N., Lei, L., Malik, J., & Jordan, M. I. (2021). Distribution-free, risk-controlling prediction sets. Journal of the ACM, 68(6), Article 43.",
 "Ben-David, S., Blitzer, J., Crammer, K., Kulesza, A., Pereira, F., & Vaughan, J. W. (2010). A theory of learning from different domains. Machine Learning, 79, 151-175.",
 "Chatzakis, M., Papakonstantinou, Y., & Palpanas, T. (2025). DARTH: Declarative recall through early termination for approximate nearest neighbor search. Proceedings of the ACM on Management of Data, 3(4).",
 "Duchi, J. C., Gupta, S., Jiang, K., & Sur, P. (2025). Predictive inference in multi-environment scenarios. Statistical Science, 40(3), 392-416.",
 "Elliott, O. P., & Clark, J. (2024). The impacts of data, ordering, and intrinsic dimensionality on recall in hierarchical navigable small worlds. arXiv:2405.17813.",
 "El-Yaniv, R., & Wiener, Y. (2010). On the foundations of noise-free selective classification. Journal of Machine Learning Research, 11, 1605-1641.",
 "Fu, C., Xiang, C., Wang, C., & Cai, D. (2019). Fast approximate nearest neighbor search with the navigating spreading-out graph. Proceedings of the VLDB Endowment, 12(5), 461-474.",
 "Garivier, A., & Kaufmann, E. (2016). Optimal best arm identification with fixed confidence. Proceedings of the 29th Conference on Learning Theory, 998-1027.",
 "Horchidan, S., Zeiher, F., Bostrom, H., Carbone, P. (2025). ConANN: Conformal approximate nearest neighbor search. Proceedings of the VLDB Endowment, 19(1), 29-42.",
 "Johansson, F. D., Sontag, D., & Ranganath, R. (2019). Support and invertibility in domain-invariant representations. Proceedings of the 22nd International Conference on Artificial Intelligence and Statistics, 527-536.",
 "Johnson, J., Douze, M., & Jegou, H. (2021). Billion-scale similarity search with GPUs. IEEE Transactions on Big Data, 7(3), 535-547.",
 "Li, C., Zhang, M., Andersen, D. G., & He, Y. (2020). Improving approximate nearest neighbor search through learned adaptive early termination. Proceedings of the 2020 ACM SIGMOD International Conference on Management of Data, 2539-2554.",
 "Malkov, Y. A., & Yashunin, D. A. (2020). Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs. IEEE Transactions on Pattern Analysis and Machine Intelligence, 42(4), 824-836.",
 "Prokhorenkova, L., & Shekhovtsov, A. (2020). Graph-based nearest neighbor search: From practice to theory. Proceedings of the 37th International Conference on Machine Learning, 7803-7813.",
 "Subramanya, S. J., Devvrit, Simhadri, H. V., Krishnaswamy, R., & Kadekodi, R. (2019). DiskANN: Fast accurate billion-point nearest neighbor search on a single node. Advances in Neural Information Processing Systems, 32.",
 "Wang, Z., Chatzakis, M., Wang, Q., Palpanas, T., Wang, P., & Wang, W. (2026). ANNiE: A learned query cost estimator for graph-based approximate nearest neighbor search. Proceedings of the VLDB Endowment, 19(11), 3820-3833.",
 "Wang, Z., Wagenmaker, A., & Jamieson, K. (2022). Best arm identification with safety constraints. Proceedings of the 25th International Conference on Artificial Intelligence and Statistics.",
 "Xu, Z., Zhao, W., Tan, S., Zhou, Z., & Li, P. (2022). Proximity graph maintenance for fast online nearest-neighbor search. arXiv:2206.10839.",
 "Yu, B. (1997). Assouad, Fano, and Le Cam. In Festschrift for Lucien Le Cam (pp. 423-435). Springer.",
 "Zhang, C., & Miller, R. J. (2026). Distribution-aware exploration for adaptive HNSW search. Proceedings of the ACM on Management of Data, 4(1).",
]
for r in REFS:
    P.append(para(r, sz=18, space_after=60, align="left", indent_first=-283))

# ------------------------------------------------------------------ appendices
P.append(heading(1, "Appendix A  Complete Notation and Semantic Contracts"))
P.append(table([
    ["Symbol", "Meaning", "Scope guardrail"],
    ["E (script)", "finite preregistered build-environment set", "no population over unseen builds"],
    ["E", "one serialized build environment", "includes replay semantics"],
    ["A_E", "finite native action set", "implementation specific"],
    ["Z_E(q,a)", "endpoint-aware failure indicator", "shared across selection, certification, evaluation"],
    ["B_E(q)", "minimum observed safe action", "registered grid only"],
    ["BOT", "unresolved registered endpoint", "never numerically imputed"],
    ["C_E(q,a)", "implementation-internal cost (distance computations)", "no cross-implementation raw equality"],
    ["Delta_{s->t}", "incremental transport risk (Eq. 20)", "registered-family conditional"],
    ["V_fin / V_end", "finite-action / endpoint-state variation (Eq. 21)", "reported separately"],
    ["DistComp", "ratio of mean distance computations", "within one implementation only"],
    ["delta, alpha, gamma, M", "risk tolerance 0.05; familywise level 0.05; margin; frozen family size", "preregistered per experiment"],
], widths=[3.0, 6.5, 6.4],
    caption="Table A1. Core notation and scope guardrails."))
P.append(para(
    "For HNSW, raw fixed efSearch is treated as a finite action rather than an assumed monotone stopping "
    "sequence. For Vamana-style search, l_value and beam width are distinct; beam width is fixed to one in the "
    "registered experiment. Native budget and cost counters remain implementation-specific.", align="justify"))

P.append(heading(1, "Appendix B  Proof of Theorem 1"))
P.append(para("Define an induced binary decision I: return 0 when the chosen action lies in D_0, return 1 when "
              "it lies in D_1, and assign actions outside both regions arbitrarily. Since the regions are "
              "disjoint, an action outside D_i incurs loss at least delta. Therefore", align="justify", space_after=60))
P.append(equation(12))
P.append(para("The minimum sum of binary testing errors equals 1 - TV; the maximum expected loss is at least "
              "half the sum, proving Theorem 1. Bretagnolle-Huber lower-bounds the error sum, and Pinsker "
              "yields the KL consequence. Substitution gives Eq. 5. For adaptive observations the chain rule "
              "gives", align="justify", space_after=60))
P.append(equation(13))
P.append(para("Data processing through the decision rule yields the stated testing consequence. The testing "
              "inequalities are classical; only the Graph-ANNS deployment-loss reduction is domain specific. "
              "The instantiation in Section 7.5 supplies the measured TV bound the premise requires.",
              align="justify"))

P.append(heading(1, "Appendix C  Proof of Theorem 2"))
P.append(para("On the estimation event every retained action satisfies the screened bound. If a minimum-cost "
              "safe action has margin, then", align="justify", space_after=60))
P.append(equation(14))
P.append(para("so it is retained; since the deployed action minimizes estimated cost among retained actions,", align="justify", space_after=60))
P.append(equation(15))
P.append(para("If every other safe action costs strictly more than the optimum plus 2*epsilon_C, these "
              "inequalities force exact selection on the event. Selection and certification roles are "
              "independent and the final action is frozen; a valid upper certificate plus a union bound gives "
              "the 1-alpha guarantee. On rejection the procedure executes only an independently valid "
              "fallback; without one it abstains. The endpoint obstruction (every in-family policy fails on "
              "the unresolved or infeasible subset), the identifiability obstruction (Theorem 1), the "
              "no-margin obstruction (risks delta-minus-epsilon and delta-plus-epsilon become "
              "indistinguishable as epsilon shrinks), adaptive selection bias, and rejection without a safe "
              "fallback are necessary obstructions, not an if-and-only-if theorem.", align="justify"))

P.append(heading(1, "Appendix D  Corollaries and Restricted Propositions"))
P.append(para("Reverse-pair symmetry: if every unordered pair appears in both directions with equal weight, "
              "each unequal pair contributes one under-budget and one over-budget direction, hence", align="justify", space_after=60))
P.append(equation(16))
P.append(para("a combinatorial identity; asymmetric source-to-held-out-target designs are still needed for "
              "directional portability claims. Endpoint decomposition: with eta_E the mass on which no "
              "registered action succeeds,", align="justify", space_after=60))
P.append(equation(17))
P.append(para("so eta_E > delta precludes in-family certification. Failure complementarity: with conditional "
              "rescue rate rho_S,", align="justify", space_after=60))
P.append(equation(18))
P.append(para("marginal auxiliary accuracy cannot replace the conditional rescue rate; shared queues, visited "
              "sets, truncation, or altered tie rules can invalidate the mechanical preservation condition. "
              "Structural bridges: the only generally valid bound retained is", align="justify", space_after=60))
P.append(equation(19))
P.append(para("Expansion-prefix arguments require fixed search semantics, preserved critical edges, priority "
              "margins, and bounded frontier intruders; they do not imply a theorem for raw efSearch or "
              "l_value without an empirical implementation bridge.", align="justify"))

P.append(heading(1, "Appendix E  Complete Experimental Protocol"))
P.append(para(
    "The registered unit is a serialized build, not a query row. The strict HNSW evidence uses 24 hnswlib and "
    "24 clean Faiss-100K builds per dataset and all 552 non-diagonal directed pairs; the Vamana-style analysis "
    "uses 12 builds and 36 preregistered directions; the 1M cell uses 8 builds, 56 directed pairs, and 500 "
    "preregistered evaluation queries. Every 100K cell contains 750 evaluation queries at Recall@10 with h=10. "
    "The clean Faiss query roles have zero ID, raw-content, and normalized-content overlap with the indexed "
    "base and historical roles; the Vamana stages carry the same audit at zero overlap with the caveats stated "
    "in Section 6. Native action grids and counters are never numerically equated across implementations.",
    align="justify"))
P.append(para(
    "The query bootstrap resamples query identities while retaining the complete vector of registered "
    "directed-pair observations; it quantifies query-distribution uncertainty conditional on the finite build "
    "family. Leave-one-build-out and leave-one-seed/order analyses test domination but do not define an "
    "unseen-build population. Top-contributor deletion removes 1% of evaluation queries under a frozen "
    "contribution rule (eight queries under the registered hnswlib ordering). The confidence intervals support "
    "registered-family conclusions only. An unresolved endpoint remains BOT in all categorical analyses. Mean, "
    "p95, p99, build cost, truth cost, control cost, and fallback cost are separate fields; missing items "
    "remain not estimable.", align="justify"))

P.append(heading(1, "Appendix F  Cross-Family Details and Estimand Crosswalk"))
P.append(para(
    "In hnswlib, same-seed cross-order inconsistency is 57.43% (SIFT) and 45.23% (Arxiv), substantially larger "
    "than same-order cross-seed inconsistency (13.25% and 12.62%); the comparison is descriptive because "
    "factors are not independently randomized across implementations. Faiss does not expose a reliable "
    "construction seed under the registered interface, so fixed input permutations define its 24 build "
    "environments; the clean 100K rerun removes query/base self-matches. DiskANN3/Vamana-style preflight "
    "establishes fixed-configuration replay and nonzero differences across registered permutations, but the "
    "frozen Vamana event table cannot reconstruct the harmonized HNSW source-action estimand; Vamana results "
    "remain stage specific. Finite-action and endpoint variation are reported separately (75.87-91.07% versus "
    "0.53-2.67%); unresolved mass is 0.072/0.167% (Faiss SIFT/Arxiv) and 0.767/1.067% (hnswlib SIFT/Arxiv).",
    align="justify"))
P.append(para(
    "Estimand crosswalk (hnswlib). The E4 primary oracle-transport estimand gives 21.57% [20.74, 22.40] (SIFT) "
    "and 17.12% [16.20, 18.06] (Arxiv) under crossed seed-query bootstrap; the original cross-family stage "
    "gives 21.57% [20.77, 22.35] and 17.12% [16.24, 18.00]; the repaired h=10 hit-count common estimand - "
    "adopted in Table 3 because the clean Faiss evidence exists only under hit-count semantics - gives 21.55% "
    "[20.76, 22.33] and 17.17% [16.33, 18.06]. All three coexist as registered values; the paper adopts the "
    "repaired common estimand for the four HNSW cells and does not modify any frozen number.", align="justify"))

P.append(heading(1, "Appendix G  Falsification-Ladder Casebook"))
P.append(table([
    ["Family", "Route", "First failed prerequisite"],
    ["Reuse/recalibration", "source-only global reuse", "nontrivial portability"],
    ["Reuse/recalibration", "target-only residual calibration", "disjoint-query replication"],
    ["Reuse/recalibration", "history-assisted calibration", "stable history increment"],
    ["Reuse/recalibration", "adaptive sentinel allocation", "matched-risk incremental value"],
    ["Selection/construction", "certified build selection", "jointly feasible candidate"],
    ["Selection/construction", "portfolio racing", "Stage-I feasibility"],
    ["Selection/construction", "protected-edge repair", "native recall/budget response"],
    ["Selection/construction", "behavioral operator search", "Pareto improvement"],
    ["Selection/construction", "critical-frontier stabilization", "structure-to-native-budget bridge"],
    ["Portal rescue", "fixed portal union", "absolute safety and cost"],
    ["Portal rescue", "per-query portal oracle", "deployable observability"],
    ["Portal rescue", "truth-free trigger", "positive validation advantage"],
    ["Portal rescue", "shared frontier", "realizable cost compression"],
    ["Auditor/fallback", "ordered certification", "native-action nesting semantics"],
    ["Auditor/fallback", "certified fallback ladder", "useful intermediate fallback"],
    ["Auditor/fallback", "unified ICBA decision", "decision regret and economics"],
], widths=[3.6, 5.6, 6.7],
    caption="Table G1. Sixteen route-level tests summarized by family and first failed condition. Three "
            "historical aggregates (the recalibration percentages, the protected-edge repair cost pair, and the "
            "exact matched-lane ratios) lack stored provenance and are flagged for re-derivation in the artifact."))
P.append(para("The ladder preserves three gaps: an oracle action may exist without an observable signal; an "
              "observable predictor may lack certification margin; and a certifiable action may have no mean, "
              "tail, or break-even value. Candidate attainability precedes all three.", align="justify"))

P.append(heading(1, "Appendix H  Claim Registry"))
P.append(para(
    "The final theory removes several overclaims: raw efSearch is not assumed to generate nested population "
    "failure events; structural similarity does not guarantee budget stability; query bootstrap is not "
    "build-level inference; a maximum registered action is not a safe fallback without evidence; mean savings "
    "do not imply tail savings; the negative result is transcript limited rather than an absolute hidden-build "
    "theorem; neither main theorem is a new general Le Cam, KL, Learn-Then-Test, or best-arm result.",
    align="justify"))
P.append(para("Permitted claims: registered-family HNSW evidence at 100K and the preregistered 1M replication; "
              "stage-specific supporting Vamana evidence; fixed-target certification semantics; the "
              "deterministic same-environment contract with its chain ablation; robust source pooling as an "
              "uncertified registered-family baseline with measured scale dependence; grid-robustness at "
              "phenomenon level; transcript-level indistinguishability for the registered probe class; "
              "operator-dependent cost. Prohibited claims: universal Graph-ANNS behavior; open-world recovery; "
              "unseen-build safety; native-budget numerical equivalence; universal profiling or "
              "conservative-cost conclusions; production/SOTA performance; resolution-invariant risk levels; "
              "learned-predictor transfer beyond the probed feature class.", align="justify"))

P.append(heading(1, "Appendix I  Reproducibility and Artifact Manifest"))
P.append(para(
    "The final evidence derives from frozen hnswlib, clean Faiss HNSW, and DiskANN3/Vamana-style result trees, "
    "plus the preregistered SIFT-1M cell whose manifest (design, seeds, orders, grid, roles, stop rules) was "
    "committed before any build or search; the forensics gate passed before any risk computation. Each stage "
    "records implementation version, build configuration, input ordering, query-role hashes, native action "
    "grid, estimand, confidence procedure, robustness deletions, and output checksums. The clean Faiss rerun "
    "verifies zero query/base content overlap and 48/48 frozen index hashes; the deterministic contract "
    "verifies byte-identical indexes and search outputs at 100K and 1M. The historical 123-entry baseline "
    "remains conditionally reproducible at 111 matching entries, eight content differences, and four "
    "unavailable unversioned cache files. The anonymous artifact omits identifying repository links and local "
    "paths; all revision-cycle numbers trace to committed result tables with deterministic test suites (16, "
    "24, 27, 16, 7, 22, and 17 checks per phase). Remaining code-audit boundaries - primitive rather than "
    "complete profiling cost, hash-only role-access status, and the three origin-unlocated historical "
    "aggregates - are recorded explicitly and are not used to strengthen the scientific claims.", align="justify"))
P.append(heading(1, "Reproducibility Statement"))
P.append(para(
    "The manuscript reports registered build families, native action grids, query-role separation, endpoint "
    "semantics, uncertainty units, and deterministic replay checks. The anonymous artifact contains scripts, "
    "compact result tables, manifests, and checksums without author-identifying paths. No future-replication "
    "truth or outcome contributes to the reported analyses; any metadata or hash-only access is separately "
    "disclosed in the artifact audit.", align="justify"))
P.append(heading(1, "AI Use Statement"))
P.append(para(
    "Generative AI tools assisted with organizing research artifacts, developing theory-experiment "
    "crosswalks, checking document structure, drafting and editing manuscript text, and supporting code and "
    "artifact validation. All mathematical statements, proofs, experimental results, citations, and AI-assisted "
    "content require final author review, and the author assumes responsibility for the submitted manuscript.",
    align="justify"))

# ------------------------------------------------------------------ build
media_files = ["fig1_setting.png", "fig2_workflow.png", "fig3_crossfamily.png",
               "fig4_pooling.png", "fig5_plane.png", "fig6_ablation.png", "fig7_ladder.png"]
out = package("".join(P), media_files)
print("built:", out, out.stat().st_size, "bytes")
