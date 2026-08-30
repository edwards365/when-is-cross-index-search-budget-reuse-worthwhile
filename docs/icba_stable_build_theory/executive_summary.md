# Executive summary

## Decision

**Final label: `STABILIZE_THEN_CERTIFY_TEMPLATE_AUTHORIZED`.** This authorizes a falsifiable pilot, not a production method or a top-ML novelty claim.

No A-level prior simultaneously modifies Graph-ANNS construction, minimizes cross-build minimum-safe-budget variation, and proves a safety/certification guarantee. The closest threats split the chain: Elliott and Clark establish insertion-order sensitivity; ANNiE makes query cost index-instance dependent; Yang et al. connect pruning to search-path rank under restrictive assumptions; FreshDiskANN studies recall stability under updates; deterministic systems address reproducibility; LTT/RCPS/CRC provide classical fixed-target certification. The remaining idea is therefore a **Graph-ANNS-specific combination**, not a new generic statistical theory.

## What is proved

- T-SC1 is a deterministic-program identity.
- T-SC2 gives a correct coupling/union-bound migration inequality after grid rounding, endpoint infeasibility and upward-closed success are made explicit.
- T-SC3 turns budget shift into search-cost bounds only under separate pathwise cost regularity; no mean-to-p95 inference is allowed.
- T-SC4 is a classical fixed-target concentration/KL application using the effective safety margin.
- T-SC5 proves critical-path disruption probability at most `h rho` without independence and derives a budget bound only with a robust trace certificate and bounded frontier interference.
- T-SC6 is a Hoeffding-plus-union-bound edge-frequency result; it does not imply budget stability.
- T-SC7 gives a two-environment minimax safety/compute/reject bound and a Lipschitz diameter corollary for an explicit loss.
- T-SC8 is a build/service break-even identity.
- T-SC9 contains 16 verified finite counterexamples.
- T-SC10 proves that edge overlap/local structure cannot universally control budget response, then gives a restricted sufficient certificate for deterministic beam search.

## Route decision

Primary: **Stabilize-then-Certify with a critical-path/frontier construction core**. It uses design queries only to weight robust trace edges and backups, independently calibrates the structural-to-budget relationship, and uses target certification for the final safety claim. Fallback: **Consensus-Stabilized Construction with protected bridges**, because it is measurable and simpler but has no direct budget guarantee. Canonical deterministic construction remains a baseline, not a fallback innovation.

The main structural interface

\[
d_B(G,G')\le L\,d_\Phi(G,G')+\varepsilon
\]

is **false for general graphs and generic structural metrics**. It is valid only in the restricted trace-certificate model defined in T-SC10, where `d_phi` counts certificate-edge failures and priority intruders. Those quantities can be approximated on design/calibration queries, but uniform open-world validity is not observable from the current frozen evidence.

## Pilot authorization and limits

A small hnswlib pilot on SIFT-100K and Arxiv-Nomic-100K is authorized under the frozen experiment contract. It must test the entire chain `structure -> B_G -> risk -> total cost`, maintain disjoint design/calibration/evaluation queries, report endpoint infeasibility and p95 separately, and stop if recall non-inferiority, diameter reduction or finite break-even fail. No validation-dev/formal-test access is authorized.
