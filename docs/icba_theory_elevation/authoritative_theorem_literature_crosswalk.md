# Authoritative theorem-to-literature crosswalk

## Audited text and method

The sole theorem text audited here is commit `6339c512d81abbe49ff11b526676ec4d6d571453`: `tow1_theorem.md`, `tow1_proof.md`, `hierarchical_risk_theory.md`, `tow3_revised_decomposition.md`, and `sample_complexity.md`. Summaries and later interpretations are not substituted for those files.

The crosswalk separates mathematical ancestry from application-specific modeling. “Not novel” below means the proof device or generic proposition is classical; it does not mean the Graph-ANNS empirical result is unimportant.

## T-OW1a

Authoritative claim: for two environments with common query law, finite ordered budgets, monotone safety loss and separated minimal safe budgets on a set of mass at least rho, every randomized Z0 policy obeys `U1+CF0 >= rho(1-TV(Q0,Q1))`, with a cost corollary under a uniform positive excess-cost gap.

Crosswalk: this is a direct Le Cam two-point/testing reduction implemented through maximal coupling and shared policy randomization. The generic blueprint “statistically close experiments with separated optimal decisions imply a risk/regret lower bound” is classical decision theory, documented by Le Cam and the standard Assouad/Fano/Le Cam literature. Brown and Low's constrained-risk inequality and Duchi–Ruan's general-loss extension are especially close in spirit: good performance at one distribution forces degradation at another. Selective-classification/reject-option work already formalizes error-versus-rejection or risk-versus-coverage tradeoffs.

Judgment: the inequality should be called a **Le Cam corollary for ordered safe budgeting**, not a new lower-bound principle. Potentially distinctive content is the one-sided under-budget event, conservative-cost/fallback split, and information-lane interpretation. These are modeling contributions unless a literature search establishes an identical safe-resource-allocation proposition.

Required correction: the theorem must state whether `Qj` is conditional on `x`. As written it is rigorous when `Z` is independent of `x` under each environment or when `Qj` denotes the relevant joint/conditional integrated experiment. The proof appendix notices this boundary, but the theorem statement should incorporate it. “Fallback” must have a stated action/loss/cost semantics, not merely be included by definition in `CF0`.

Recommended status: `FORMAL_PROOF_COMPLETE_CLASSICAL_COROLLARY`; novelty claim restricted to formulation and Graph-ANNS instantiation.

## T-OW1b

Authoritative claim: replace `Qj` by the k-probe transcript law; under iid probes, KL tensorizes and Pinsker yields `rho max(0,1-sqrt(k KL/2))`.

Crosswalk: product-experiment tensorization and Pinsker conversion are standard. This is the usual Le Cam sample-size refinement, not a distinct theorem family. The important project distinction—k reduces environment-identification error but cannot repair support or response misspecification—is correct conceptually and aligns with distributional-robustness work that requires an explicit ambiguity/support set.

Required correction: if probes are adaptive, `Qj^(k)` must denote the complete adaptive transcript and iid KL tensorization no longer follows verbatim; use a chain-rule KL bound under explicit conditional assumptions. Pinsker only supplies a possibly vacuous square-root expression. Any statement of exponential testing improvement needs Chernoff/Bretagnolle–Huber-type assumptions and a separate theorem; it does not follow from the displayed Pinsker bound alone.

Recommended status: `FORMAL_PROOF_COMPLETE_CLASSICAL_COROLLARY` for fixed/nonadaptive iid probes; `PROOF_SKETCH` for adaptive probes.

## T-OW2

Authoritative claim: safety on every observed build cannot imply a probability guarantee over unseen builds without an assumption relating observed builds to a meta-law.

Crosswalk: the counterexample is a basic no-free-lunch/non-identification argument. Hierarchical conformal and grouped prediction work similarly require exchangeability at the group/build layer before offering new-group coverage. Domain-generalization work likewise adds assumptions connecting source and unseen domains.

Judgment: logically correct and important as a scope theorem, but not a novel statistical impossibility theorem. Its strongest role is to prevent pseudoreplication and the promotion of fixed-design evidence to a population certificate.

Required correction: when no `Pi` is assumed, `Pr_{theta~Pi}` is not merely unbounded—it is outside the fixed-design model. State two alternatives: undefined without `Pi`, and arbitrarily bad uniformly over all `Pi` consistent with observed builds.

Recommended status: `FORMAL_PROOF_COMPLETE_SCOPE_LEMMA`.

## T-OW3

Authoritative claim: if deployment failure lies in the union of endpoint, support, probe and base-policy failure events, a sequential disjoint decomposition upper-bounds its probability.

Crosswalk: this is a partition plus union bound. The excess-risk telescoping observation is algebraic, and Shapley attribution is descriptive absent causal identification.

Judgment: retain as bookkeeping/protocol, not a “main theorem.” The conditional event definitions are useful, but mathematical novelty is absent.

Required correction: avoid using `P` for both probability and the probe-failure event. The displayed sequential terms are disjoint; if they exhaust the named union, their sum equals the union probability, while only the step from deployment failure to that union is an inequality.

Recommended status: `FORMAL_ACCOUNTING_IDENTITY_UNDER_EVENT_DEFINITIONS`; overall empirical instantiation remains `RESTRICTED_PROPOSITION`.

## T-OW5

Authoritative claim: n, m, k and M control different uncertainty layers; with zero failures, one-sided exact binomial upper bound is `1-alpha^(1/N)`, giving 29/59/299 units for delta 0.10/0.05/0.01 at alpha 0.05.

Crosswalk: the zero-event formula is the zero-success/failure specialization of the exact Clopper–Pearson binomial interval. The `log(M/alpha)` statement is a standard bounded-loss union-bound/Hoeffding scaling. The need for build exchangeability is standard hierarchical inference. None of these generic rates is new.

Judgment: the m/n/k/M separation is a useful problem-specific sample-complexity map, not yet a unified sample-complexity theorem. Only the zero-event calculations and non-implication statements are complete.

Required correction: name the Bernoulli unit and independence/exchangeability assumption every time the zero-event bound is used. For estimated bad-build labels, give an explicit nested confidence construction instead of saying classification error “must be controlled.” For M candidates, specify bounded loss, data reuse, and whether Bonferroni, sample splitting or a uniform class bound is used. For k, provide a channel-separation parameter and a target testing error before claiming a sample requirement.

Recommended status: `FORMAL_CLASSICAL_SUBRESULTS_PLUS_PROOF_SKETCH`.

## Claim-level decision

The current theory does not justify claiming five new statistical theorems. A defensible paper position is:

1. one new application framework, Hidden-Environment Safe Budgeting;
2. one Le Cam-derived ordered safety–conservatism corollary with explicit fallback and information lanes;
3. one scope lemma separating fixed-build and random-build inference;
4. one accounting decomposition;
5. one classical sample-size audit specialized to query/build/probe/model-selection layers;
6. a new frozen Graph-ANNS empirical witness set and negative Z1 control result.

Before publication, T-OW1 should be renamed and stated using the joint observation experiment; T-OW3 should leave the “main theorem” list; T-OW5 should either acquire a genuine nested finite-sample theorem or be presented as a design calculus.

## Primary and authoritative sources

- Lucien Le Cam, *Asymptotic Methods in Statistical Decision Theory* (1986), DOI: https://doi.org/10.1007/978-1-4612-4946-7
- Bin Yu, “Assouad, Fano, and Le Cam” (1997): https://link.springer.com/chapter/10.1007/978-1-4612-1880-7_29
- Lawrence D. Brown and Mark G. Low, “A Constrained Risk Inequality…” (1996): https://repository.upenn.edu/bitstreams/6c47aebe-667b-47b7-9754-81f412209ebc/download
- John Duchi and Feng Ruan, “A Constrained Risk Inequality for General Losses” (2021): https://proceedings.mlr.press/v130/duchi21a.html
- C. J. Clopper and E. S. Pearson, “The Use of Confidence or Fiducial Limits…” (1934), DOI: https://doi.org/10.1093/biomet/26.4.404
- C. K. Chow, “On Optimum Recognition Error and Reject Tradeoff” (1970), DOI: https://doi.org/10.1109/TIT.1970.1054406
- Ran El-Yaniv and Yair Wiener, “On the Foundations of Noise-free Selective Classification” (2010): https://jmlr.csail.mit.edu/papers/v11/el-yaniv10a.html
- Vojtech Franc, Daniel Prusa and Vaclav Voracek, “Optimal Strategies for Reject Option Classifiers” (2023): https://www.jmlr.org/papers/v24/21-0048.html
- Distribution-Free Prediction Sets for Two-Layer Hierarchical Models (2018): https://arxiv.org/abs/1809.07441
