# GSC theory inheritance report

## Three-stage architecture

`Generate` proposes graph candidates; `Stabilize` optimizes a measured budget-response objective on proposal/validation data; `Certify` freezes the final finite build×raw-`ef` family and uses an independent target sample. Only the last stage carries a distribution-free fixed-target safety certificate.

## Directly inherited modules

| Module | Inherited result | Scope preserved |
|---|---|---|
| hidden build environment | Oracle–Observable/Open-World theory | latent build affects response; no free inference |
| information collision | two environments can share observables but differ in safe action | lower-bound/counterexample scope |
| fixed-target independent certification | CIBS T-CIBS1/2, LTT/RCPS | finite registered family and target query distribution |
| fallback accounting | Certification–Fallback theory | costs are measured in declared units |
| break-even | T-CIBS5 | realized mean saving only; no p95 implication |
| fixed-target/open-world boundary | T-CIBS7 | no unseen-build or query-shift claim |
| classical testing lower bounds | Le Cam/Bernoulli-KL/BAI | CIBS observation channel specialization |

## Adaptation needed for GSC

Adaptive generation is permitted before certification only because sample splitting places all generation decisions in a proposal/validation sigma-field and keeps the certification sample independent. The final candidate family must be frozen and its size or simultaneous-control rule fixed before certification. This is a conditional application of sample splitting, not a new adaptive-inference theorem.

Stabilization adds (D_Z,D_C), endpoint disagreement, and rank-reversal diagnostics. These are new objects for the Graph-ANNS design, but no automatic implication from (D_C) to (D_Z) is valid. A transfer inequality can use disagreement directly:

\[
r(G',e)\le r(G,e)+P_q[Z_{G,e}(q)\ne Z_{G',e}(q)],
\]

which is an event decomposition, not a structural stability theorem.

## Explicit non-inheritances

GSC does not inherit raw-`ef` monotonicity, stage-as-budget order, edge-overlap-to-risk stability, high-AUROC safety, one-intruder/one-`ef` correspondence, paired-query deployment validity, or CIBS empirical candidate feasibility.

## Novelty ceiling

The defensible delta is `NEW_COMBINATION_OF_CLASSICAL_RESULTS`: adaptive graph proposal plus measured response diagnostics plus independent finite-family certification. A Graph-ANNS-specific method claim requires actual operator implementation and independent evaluation; theory alone cannot pre-authorize it.

