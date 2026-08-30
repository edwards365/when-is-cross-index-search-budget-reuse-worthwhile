# NeurIPS / database red-team review

| Criticism | Valid? | Theory response | Experimental response | Claim reduction if unresolved |
|---|---|---|---|---|
| Fixed order is obvious engineering. | Yes. | T-SC1 labels it an identity. | Include as baseline only. | Remove novelty claim for canonicalization. |
| Edge overlap is not search stability. | Yes. | CE01/CE02 and T-SC10 impossibility. | Report the full `d_phi -> d_B` calibration. | Do not use edge overlap as success. |
| Theory is Le Cam/PAC/concentration recombination. | Mostly. | Statistical results are explicitly classical; novelty is restricted trace structure. | N/A. | Claim Graph-ANNS-specific combination only. |
| Stable construction may sacrifice recall/efficiency. | Yes. | Optimization has non-inferiority constraints, not a theorem that they are feasible. | Recall, endpoint, mean/p95 Gates. | Stop pilot or report negative result. |
| Multiple builds cost more than service savings. | Yes. | T-SC8 gives `N*` and no-finite-break-even. | Measure build/memory/evidence/fallback cost. | No deployability claim. |
| hnswlib and 100K are too small. | Yes for a paper. | Pilot authorization is not external validity. | Expand only after two-dataset Gate; add Faiss/Vamana later. | Call it pilot, not system validation. |
| Critical paths overfit training queries. | Yes. | T-SC10 limits scope and requires independent calibration. | Disjoint queries, tail deletion, workload-shift split. | Fixed-workload scope only. |
| This is existing pruning/repair. | Serious. | Yang et al., NSG, Vamana and Ponomarenko are cited; new object is cross-build budget/certification. | Compare same build cost/degree and ablate stability term. | Avoid “first path-aware construction.” |
| Build change is not distribution shift. | Terminological. | Use “algorithmic build environment,” with a defined build law; do not rely on semantic equivalence. | Treat build as cluster/unit. | Avoid generic domain-shift novelty. |
| No wall-clock or p95 result. | Yes. | T-SC3 forbids mean-to-tail inference. | Query-pooled p95 and hardware protocol. | No latency claim. |
| No outer-build certification. | Yes. | Fixed-target and outer-build scopes are separated. | Future independent build-level calibration. | No open-world positive guarantee. |
| Stability is only reproducibility. | False for the proposed object, true for canonical baseline. | Eight-object taxonomy and `B_G` definition. | Show response diameter and risk/cost chain. | If `d_B` does not improve, revert to reproducibility baseline. |

## Overall reviewer risk

The most likely NeurIPS rejection is that the only general results are classical and the nonclassical structural theorem is too restricted/empirically unverifiable. The most likely SIGMOD/VLDB rejection is that the pilot does not demonstrate a meaningful build/service break-even across implementations and realistic scales. A database-first submission becomes plausible only after a concrete repair algorithm, cross-build response reduction, tail non-inferiority and systems-cost accounting close together.
