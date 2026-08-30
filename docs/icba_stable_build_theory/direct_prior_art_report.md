# Direct prior-art forensic report

## Gate conclusion

No verified paper met all four direct-prior predicates (construction intervention, cross-build budget-response objective, safety/certification theorem, multi-build evaluation). The strongest papers each cover one or two links. `DIRECT_PRIOR_ART_FOUND_REDEFINE` is not triggered, but several broad claims must be deleted.

## Fifteen highest-risk Level-A sources

### 1. Malkov & Yashunin — HNSW

Full 13-page paper inspected, including construction/search algorithms, neighbor-selection heuristic, experiments and discussion; no numbered theorem/proof. It defines randomized levels and incremental graph construction, and describes logarithmic scaling heuristically. It does not define rebuild pairs, minimum safe budget or a safety certificate. Backward trace: NSW/skip lists/RNG; forward trace: insertion-order studies, learned ef policies and deterministic implementations. **Delete:** “first robust/navigable graph construction.” **Keep:** budget-response stability is not its object.

### 2. Fu, Wang & Cai — NSG

Full 9-page paper inspected; no numbered theorem. NSG approximates MRNG with connectivity, low degree, short paths and a navigating vertex. Its pruning/search-aware design is a direct construction baseline. It does not optimize variability across legitimate rebuilds or certify a transferred policy. **Delete:** “first search-path-aware graph construction.”

### 3. Subramanya et al. — DiskANN/Vamana

Full 11-page proceedings paper inspected; no numbered theorem. Vamana’s alpha-RNG pruning and fewer SSD-critical hops are direct structural/cost baselines. The object is performance of one constructed index, not response diameter across builds. **Delete:** “first construction objective tied to query cost.” **Keep:** cross-build safe-budget/certification chain.

### 4. Singh et al. — FreshDiskANN

Full 19-page paper and appendices inspected; no numbered theorem. It explicitly evaluates recall stability over update cycles and uses FreshVamana/streaming merges. This is the strongest “stable ANN” systems precedent, but stability is temporal aggregate recall, not source-policy budget response or fixed-target certification. **Delete:** “first stable recall graph maintenance.”

### 5. Elliott & Clark — ordering/intrinsic dimensionality

Full text, methods, all experiments and limitations inspected; no theorem. It demonstrates up to 12.8 percentage-point recall variation under insertion ordering and studies LID/category orders. This directly establishes the phenomenon. **Delete:** first observation that HNSW insertion order matters. **Keep:** an algorithm targeting response diameter plus certification is absent.

### 6. Yang et al. — Revisiting PG construction

Full 16-page paper inspected. Theorem 4.1 links a minimax-rank path statistic to beam-search result preservation after pruning; Lemma 4.1/Theorem 4.2 analyze alpha-pruning under uniform infinite-space and independence assumptions; Theorem 5.1 is a Chernoff sampling estimate. This is the most dangerous theorem neighbor to T-SC5/T-SC10. It has neither multiple rebuilds nor `B_G`, but generic critical-path/pruning novelty is unavailable. **Keep only:** robust-trace-to-one-sided-safe-budget coupling with censoring and certification.

### 7. Yenen — MonaVec

Full HTML/preprint inspected; no theorem. It fixes seed, construction order and numerical choices, and gives a careful taxonomy of deterministic, byte-identical and cross-architecture reproducible behavior. It confirms that deterministic construction is an existing engineering objective. **Delete:** canonical determinism as a primary contribution.

### 8. Wang et al. — Steiner-Hardness

Full text and theorem framework inspected. It defines graph-native minimum query effort through a directed-Steiner connection and reports construction-order averaging. It is direct prior for graph-specific query hardness and trace/cost reasoning, but not build-to-build policy portability. **Delete:** first graph-native query-effort abstraction.

### 9. Wang et al. — ANNiE

Official 14-page paper inspected. Definition 5, Theorem 1 and Corollary 1 concern population-optimal conditional quantile cost prediction and recall on the training distribution. The paper explicitly notes index dependence, OOD limits and insertion-order cost variation. It does not guarantee transfer after rebuild. **Required comparison:** per-index retraining and the same-query cost-response curve.

### 10. Bae et al. — QBAT

Official 14-page paper inspected; no formal theorem. It profiles a dataset/index/target-recall response and recommends retraining/reprofiling after change; HNSW is preliminary. This is a direct autotuning/retrain baseline, not a stable-construction precedent. **Required comparison:** stable build plus small certification versus full target profiling.

### 11. Horchidan et al. — ConANN

Full text inspected. It uses conformal machinery for a fixed, calibrated IVF-style index and expected false-negative control. Recalibration on a rebuilt index can solve the fixed-target method problem if labels are affordable, but not source-only portability or build stabilization. **Delete:** first certified per-query ANN budget.

### 12. Chatzakis et al. — DARTH/DARTH+

Full method and guarantee language inspected; no theorem comparable to a distribution-free rebuild certificate. Learned termination is trained/profiled for a concrete index. Per-rebuild retraining is a strong method-subsumption baseline. It does not alter construction to contract response diameter.

### 13. Angelopoulos et al. — Learn-Then-Test

Theorem 1 and propositions/proofs inspected. Finite candidate selection with valid p-values/FWER directly supplies the independent certification module. It is not a construction theorem. **Delete:** new general finite-family certificate.

### 14. Bates et al. — RCPS

Theorems and proof appendices inspected. Monotone candidate families and one-sided risk bounds give a fixed-distribution certificate. T-SC4’s `gamma^-2` order is a classical application. **Delete:** new sample-complexity theorem absent graph-specific structural work.

### 15. Duchi et al. — multi-environment predictive inference

Theorems 1–5 and appendix inspected. It provides the closest outer-environment/inner-sample probability structure, but for predictive sets under exchangeable environments, not construction actions or ordered compute. **Delete:** first two-level environment/query guarantee. **Keep:** Graph-ANNS action/cost/censoring structure.

## Backward/forward synthesis

Backward citations show that navigation, graph pruning, greedy-path quality, deterministic randomized algorithms, risk calibration and reject options are mature components. Forward searches found dynamic deletion/repair, deterministic embedded indexes, query-hardness repair and more formal graph-ANNS analysis, but no verified work closing the response-diameter/safety/cost chain. The 2025 “Graph-Based ANNS Revisited” preprint was discovered as a potentially dangerous search-path/degree theorem; because complete proof verification was unavailable in this audit, it is Level C and marked `UNCERTAIN_FULLTEXT_REQUIRED`, not used to clear novelty.

## Surviving narrow claim

The surviving claim is not “first stable graph.” It is: *we define cross-build minimum-safe-budget response as a decision-relevant stability object, prove a restricted robust-trace sufficient condition for one-sided budget migration, and combine it with classical independent certification and a Graph-ANNS build/service Gate.*
