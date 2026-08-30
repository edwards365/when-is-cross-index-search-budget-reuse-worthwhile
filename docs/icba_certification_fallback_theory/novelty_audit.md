# Novelty and prior-theory audit

## Governing disposition

The closure does not introduce a new generic confidence interval, multiple-testing principle, active-testing lower bound, KL inequality, selective-classification frontier, or ANNS recall guarantee. The strongest permitted label is

`NEW_COMBINATION_OF_CLASSICAL_RESULTS`.

## Direct comparison

| Prior work | Verified contribution used here | Relation to this closure | Permitted disposition |
|---|---|---|---|
| Clopper--Pearson (1934) | exact binomial confidence limits | T-CF4 zero-failure threshold is the classical one-sided special case | `CLASSICAL_APPLICATION` |
| Angelopoulos et al., *Learn then Test: Calibrating Predictive Algorithms to Achieve Risk Control* | finite-candidate risk-valid selection through valid tests and FWER control | directly covers much of Bonferroni/gatekeeping certification logic | `STRONG_THEOREM_OVERLAP` |
| Bates et al., *Distribution-Free, Risk-Controlling Prediction Sets* | high-probability fixed-distribution risk control through inverted UCBs | direct fixed-target certificate module for ordered policies | `STRONG_THEOREM_OVERLAP` |
| Angelopoulos et al., *Conformal Risk Control* | finite-sample control for monotone losses under exchangeability | close ordered-risk calibration neighbor, but its expected-risk object is not this cost identity | `PARTIAL_THEOREM_OVERLAP` |
| El-Yaniv and Wiener, *On the Foundations of Noise-free Selective Classification*; classical Chow reject rule | risk--coverage/reject tradeoff | fallback and abstention are classical decision actions | `SAME_PROOF_TEMPLATE_DIFFERENT_OBJECT` |
| Naghshvar and Javidi, *Active Sequential Hypothesis Testing* | controlled sensing, dynamic programs, information/sample lower bounds | blocks any claim of new generic active certification theory | `STRONG_THEOREM_OVERLAP` |
| Garivier and Kaufmann, *Optimal Best Arm Identification with Fixed Confidence* | characteristic-time lower bound and Track-and-Stop | blocks any claim of new generic KL/active sample-complexity result | `STRONG_THEOREM_OVERLAP` |
| Wang, Wagenmaker, and Jamieson, *Best Arm Identification with Safety Constraints* | safe exploration plus identification lower/upper bounds | close to purchasing evidence while respecting safety | `STRONG_THEOREM_OVERLAP` |
| Classical cost-sensitive decision theory | Bayes action and cost-weighted regret | T-CF1/T-CF2 are specialized accounting and action comparison | `IDENTITY_OR_DEFINITION` |
| Wang et al., *ANNiE: A Learned Query Cost Estimator for Graph-Based Approximate Nearest Neighbor Search* | per-query cost prediction and population quantile-loss statement on a concrete index; explicit index dependence | direct method neighbor, but no source-policy rebuild portability certificate | `PARTIAL_STRUCTURAL_OVERLAP` |
| Bae et al., *QBAT: Model-based Query Budget Autotuner for Clustering-based Approximate Nearest Neighbor Search* | per-query budget autotuning after index/workload profiling; no formal finite-sample safety theorem in the verified paper | direct method neighbor and required retraining/profiling baseline | `EMPIRICAL_ONLY_OVERLAP` |

Key sources:

- Learn Then Test: https://doi.org/10.1214/24-AOAS1998
- RCPS: https://doi.org/10.1145/3478535
- Conformal Risk Control: https://openreview.net/forum?id=33XGfHLtZg
- Track-and-Stop: https://proceedings.mlr.press/v49/garivier16a.html
- ANNiE: https://doi.org/10.14778/3836663.3836728
- QBAT: https://doi.org/10.14778/3836663.3836675

## Theorem-by-theorem claim boundary

- T-CF1: `IDENTITY_OR_DEFINITION`. Claim only that the identity exposes the certification/fallback tax relevant to this project.
- T-CF2: `RESTRICTED_DOMAIN_PROPOSITION`. Break-even algebra is not a new economic theorem; the useful contribution is the locked Graph-ANNS action/cost interface.
- T-CF3: `NEW_COMBINATION_OF_CLASSICAL_RESULTS`. The combination of ordered absolute failure, independent target certification, legal rung transfer, and fallback is useful but built from classical multiple testing and empirical-process tools.
- T-CF4: `CLASSICAL_APPLICATION`. CP, Hoeffding, and Bernoulli-KL rates are classical.
- T-CF5: `NEW_COMBINATION_OF_CLASSICAL_RESULTS`. The ladder's safety and value condition specialize reject-option accounting to ordered Graph-ANNS budgets.
- T-CF6: `RESTRICTED_DOMAIN_PROPOSITION`. It is a conditional Lipschitz transfer implication, not a discovered graph metric.

## Safe claims

1. A fixed-target ordered recovery policy can be certified with finite independent target evidence under explicit nesting/independence assumptions and a valid terminal safe action.
2. Positive oracle headroom is insufficient; deployment additionally requires a positive post-selection, post-certification, post-fallback cost margin and enough workload.
3. Query-level nested failures permit a DKW simultaneous band without a `log L` union-bound factor and permit valid fixed-sequence testing.
4. Fallback ladders are valuable only when expected saved fallback gap exceeds amortized evidence and control costs.
5. Stable-by-construction can reduce certification burden conditionally on a validated source--target risk metric.

## Forbidden claims

- new general active sequential testing theory;
- new general KL or characteristic-time lower bound;
- first safe budget certification method;
- first rebuild-portable ANNS method;
- unconditional or distribution-free open-world recovery;
- validated deployable source--target graph distance;
- p95 guarantee derived from the mean identity;
- experimental confirmation of the method template;
- ANNiE or QBAT portability across rebuilds without new profiling/calibration.
