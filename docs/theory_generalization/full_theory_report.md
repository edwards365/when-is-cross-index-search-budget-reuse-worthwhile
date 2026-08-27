# Information-Constrained Budget Adaptation: theory generalization report

## Executive conclusion

ICBA unifies the project's positive Oracle signals and negative deployment results without forcing a new algorithmic success. The framework separates what an optimizer could achieve with target demand, what a source-summary policy can safely infer, what monotonicity additionally costs, what marginal risk can recover, and what finite calibration can actually certify. The final intended label is `GENERAL_FRAMEWORK_VALID_EMPIRICAL_SCOPE_HNSWLIB`.

## Evidence integrity

The analysis began from frozen Git objects, not mutable working-tree summaries. Cross-Index `b82abf6`, Tournament `80c505d`, RCRS Fast `01c491f`, and Signal Pilot `07ffc38` passed all selected checksum entries. Definitions and query splits were audited separately; results from distinct splits were not pooled. validation-dev and formal-test remained sealed. Existing untracked logs were preserved.

## Formal object

A budgeted-search system is `(Q,I,E,R,C)` with query q, environment/index I, ordered budget e, quality `R_I(q,e)`, cost `C_I(q,e)`, quality target tau, and allowed failure probability delta. The minimum stable sufficient budget is the first frozen budget after which every larger frozen budget satisfies tau; absence on the grid is a right-censored observation `B_I(q)>e_max`. The value `V_delta(G)` minimizes expected cost among policies measurable with respect to information class G subject to the stated risk constraint.

Pointwise safety, marginal population risk, conditional risk, design empirical risk, and certified population risk are different objects. All numerical conclusions retain this distinction.

## Theorem audit

- **T1—information ordering (`FORMALLY_PROVED`)**: inclusion of admissible measurable policy classes implies non-increasing optimal value. Target-static and target-sequential information do not have a universal order unless containment is supplied.
- **T2—source-summary safe envelope (`FORMALLY_PROVED`)**: the conditional essential supremum of target demand is the minimum zero-risk action in each source-information cell. Its excess cost over the target Oracle is the information-coarsening tax.
- **T3—least safe monotone majorant (`FORMALLY_PROVED`)**: on an ordered grid, tiewise maxima followed by prefix maxima give the unique pointwise-minimal safe nondecreasing allocation. This is a majorant problem rather than squared-error isotonic regression.
- **T4—rank-inversion matching lower bound (`PROOF_SKETCH_ONLY`)**: a vertex-disjoint matching of incompatible pairs yields a lower bound under the narrowed finite-grid/additive-gap assumptions. No inference from inversion rate alone to cost magnitude is allowed.
- **T5—risk-matched adaptation (`FORMALLY_PROVED`)**: a finite dynamic program allocates the global failure allowance across information cells; groupwise quantiles are not generally globally optimal. Delta zero recovers the safe envelope.
- **T6—certification power (`FORMALLY_PROVED`)**: exact binomial inversion defines the allowable failure count and certification probability for a prespecified finite family.
- **T7—signal/certification gap (`FORMALLY_PROVED`)**: ranking metrics do not determine threshold calibration or conditional tail risk.
- **T8—sequential escape (`FORMALLY_PROVED`)**: target-native filtrations define a different information class from source summaries, so source-only lower bounds do not rule out stopping policies. Prefix equivalence remains empirical and implementation-specific.

T2–T5 were checked against exhaustive finite cases for n=2–8 and 2–6 budget levels where applicable. Twelve tests passed. The finite search discovered no counterexample inside T4's narrowed scope, but T4 remains a proof sketch.

## Unified frozen-data results

The pipeline read all 81 frozen graph records and 972,000 query–budget rows. On the frozen 750-query design-evaluation portion, it evaluated 648 directed source→target pairs. Five tables separate unified metrics, risk frontiers, inversion bounds, censoring, and information-class values. Each main paired mean interval uses 5,000 query bootstrap replicates with seed 991.

Across the nine implementation×dataset groups, mean budget-change rates were 0.1370–0.6173 and mean inversion rates 0.0942–0.2351. The observed safe-monotone tax was positive in every group, with group means 1.0641–3.1297 relative to fixed NDC. These ratios can exceed one because a zero-risk envelope can be much more expensive than a fixed policy that is only safe on average. They do not imply a deployable loss for every query or environment.

Right censoring materially affects GloVe: mean rates are 0.0476 for hnswlib, 0.0567 for Faiss, and 0.0484 for Vamana. SIFT-hnswlib is 0.00059 and the other groups are effectively zero. For censored units, the observed maximum-grid cost is a clipped lower bound; without a cost-above-grid assumption the zero-risk upper endpoint is unbounded. In risk optimization, censored units consume mandatory failure allowance. This gives 1,632 exact cells, 424 exact cells conditional on that mandatory-failure convention, and 536 infeasible cells.

NDC is native and implementation-local. Cross-implementation plots compare normalized internal quantities or boundary directions; they do not assert equivalent hardware work.

## Certification power and signal gap

With n=256 and alpha=delta=0.05, k-star equals 6, 5, and 3 for M=1, 4, and 16 respectively. Thus multiplicity can make a genuinely useful family hard to certify. Exact certification probabilities were computed for n in {64,128,256,512,1024}, M in {1,4,16}, and p in {0.01,0.02,0.028,0.03,0.05}, then checked using 100,000 binomial Monte Carlo trials per cell with seed 991.

The continuous score experiment holds AUROC and AUPRC fixed under a monotone transformation while changing which queries cross a fixed numeric threshold. Unsafe-given-stop changes from 3.10% to 0.77%. This does not make AUC useless; it shows why a deployment certificate must be attached to the exact frozen operating policy.

## Literature and novelty

The targeted audit covers foundational HNSW and DiskANN/Vamana, adaptive ANN, Blackwell informativeness, conformal risk control and Learn-then-Test, exact binomial inference, optimal stopping, and adaptive ANN theory. General value-of-information ordering, conformal certification, and the distinction between ranking and calibration are prior principles and are not claimed as new. To our knowledge under the reviewed scope, no prior source jointly treats transported per-query ANN budgets after index rebuilding, source-summary envelopes, monotone inversion cost, risk relaxation, censoring, and controlled multi-implementation evidence. This is a qualified integration/specialization claim, not an unrestricted “first.”

## Empirical boundary and method interface

Cross-Index ended at `SHRINK_TO_HNSWLIB_IMPLEMENTATION_BOUNDARY`; Tournament at `NO_DEPLOYABLE_CANDIDATE_KEEP_BOUNDARY_STUDY`; Signal Pilot at `STOP_RCRS_NO_CERTIFIED_STOPPING_SIGNAL`. These outcomes support a general theory with a narrow current actionable scope. A future method must refine the information class using target-native sequential state, demonstrate exact resumability, include fallback and probe overhead, and precompute certification power before confirmation. This report does not authorize such an experiment.

## Optional pilot and limitations

The IVF-Flat method-family pilot was skipped to preserve the 10 GiB disk safety margin and core deliverables. Therefore empirical method-family generalization remains unvalidated. Other limitations are T4's proof-sketch status, finite budget grids, right censoring, implementation-local cost units, train/design-only evidence, and no validation-dev/formal-test access.

## Gate decision

T1 definition consistency, T2 proof validity with a narrowed T4, T3 risk alignment, T4 censoring, T5 empirical contact, T6 qualified novelty, and T7 method interface are satisfied at the report-draft stage. The correct decision is `GENERAL_FRAMEWORK_VALID_EMPIRICAL_SCOPE_HNSWLIB`; method derivation is conceptually allowed after this sprint, but algorithm execution requires a separate preregistration and authorization.
