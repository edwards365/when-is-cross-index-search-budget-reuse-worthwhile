# GSC operator-level prior-art delta

The review treats each operator as a mechanism, not as a pre-certified contribution. “No close prior found” is bounded by the directed search and does not justify a first-of-kind claim.

| Operator | Closest prior art (up to five) | Shared mechanism | Main difference / retained scope | Overlap |
|---|---|---|---|---|
| O1 deterministic construction | HNSW; NSG; DiskANN/Vamana; FreshDiskANN; deterministic/reproducible graph-construction work | fixed or reproducible insertion/build procedure | reproducibility is a control condition, not budget-response stabilization | `STRONG_COMPONENT_OVERLAP` |
| O2 trace-guided bridge overlay | MARGO; Steiner-Hardness; Graph-Based ANNS Revisited; path/entry-point analyses; NSG | use navigational/path structure to repair connectivity | trace-derived proposal tied to cross-build budget response is unverified and must be measured | `PARTIAL_MECHANISM_OVERLAP` |
| O3 budget-response local repair | ANNiE; QBAT; DARTH/DARTH+; Ada-ef; ConANN | optimize recall/cost response or stopping behavior | acts on graph construction rather than only query-time control; no prior theorem of safety transfer | `STRONG_COMPONENT_OVERLAP` |
| O4 response-weighted robust pruning | HNSW/NSG pruning; Vamana/FreshDiskANN; robustness-aware graph construction; MARGO | alter edges using graph/search utility | response-weighted criterion and endpoint-aware certification are a new combination only after implementation | `DOMAIN_SPECIFIC_NEW_COMBINATION` |
| O5 multi-build consensus | algorithm portfolios; SATzilla; ensemble/multi-index ANN; correlated-arm BAI; CIBS | aggregate information across candidate configurations | first version deploys one build and uses consensus only for candidate diagnostics; no generic ensemble claim | `PARTIAL_MECHANISM_OVERLAP` |
| O6 response-aware insertion schedule | HNSW insertion-order sensitivity; FreshDiskANN; dynamic graph maintenance; workload-aware indexing; algorithm configuration | choose construction order based on workload/graph properties | target-response-driven order with independent certification is not established by prior work | `DOMAIN_SPECIFIC_NEW_COMBINATION` |
| O7 two-operator combination | O2–O6 component families; LTT/RCPS; SafeBAI; Track-and-Stop | compose construction and certification | no direct seven-condition method found; efficacy remains empirical | `DOMAIN_SPECIFIC_NEW_COMBINATION` |

## Seven-condition direct prior check

No checked work jointly offers active Graph-ANNS construction, cross-build query-budget response optimization, explicit Recall/endpoint safety, independent target certification, full build/truth/certification/fallback accounting, and one deployable index plus fixed search action. ANNiE, QBAT, DARTH, Ada-ef and ConANN cover query-time response or risk modules; graph-construction works cover build mechanisms; LTT/RCPS/BAI cover selection. Their composition is a threat to generic theory novelty but not a verified direct method precedent.

## Citation requirements for a future paper

Any operator paper must cite the graph-construction family it modifies, ANNiE/QBAT/DARTH/Ada-ef/ConANN for query response or budget control, and LTT/RCPS/SafeBAI/Track-and-Stop for certification or selection. The wording must say “proposed operator combination evaluated under a fixed-target certification protocol,” not “first stable/safe/rebuild-portable construction.”

