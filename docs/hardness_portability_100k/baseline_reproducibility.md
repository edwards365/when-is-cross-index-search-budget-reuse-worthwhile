# Frozen baseline reproducibility audit

This audit uses only the eight preregistered papers and links exposed by their arXiv records. It does not search for adjacent implementations and does not tune a reconstruction.

| Baseline | Status | Evidence and boundary |
|---|---|---|
| LID | `REPRODUCIBLE_FROZEN_LOCAL` | Exact squared-L2 k=100 MLE-LID is already frozen in `lid_order_manifest.json`. This reproduces the OCGT-v3 definition, but the earlier 10K predictor did not satisfy Recall noninferiority; no post-result 100K predictor fit is authorized. |
| Relative Contrast / nearest-distance gap | `REPRODUCIBLE_STATIC_DIAGNOSTIC_ONLY` | Deterministic from frozen exact neighbor distances, but no unique paper-prescribed mapping to the 12-point ef grid is available without fitting a new rule. |
| Steiner-hardness | `BASELINE_NOT_REPRODUCIBLE` | arXiv:2408.13899 defines a graph-native DST reduction but its arXiv record exposes no author-code link, pinned implementation, representative-graph construction, or solver configuration sufficient for a unique 100K run. |
| Adaptive-ef | `BASELINE_NOT_REPRODUCIBLE` | arXiv:2512.06636 describes a distribution-aware statistical model, but its record exposes no author-code link or pinned parameterization sufficient to map this frozen fixture to ef without discretionary reconstruction. |
| SHEAF | `OFFICIAL_BASELINE_NOT_REPRODUCIBLE`; `FROZEN_SHEAF_LIKE_NEGATIVE_AVAILABLE` | arXiv:2607.12229 defines answer-set flux from two probes but exposes no author-code link. The previously frozen OCGT-v3 SHEAF-like implementation is auditable and includes `C16+C24+Cpred`; it had negative net benefit and is not relabeled as the official implementation. |
| DABS | `BASELINE_NOT_REPRODUCIBLE` | arXiv:2505.15636 specifies a distance-adaptive stopping principle, but no author-code link or uniquely pinned practical HNSW mapping is exposed by the record. |
| DARTH | `BASELINE_NOT_REPRODUCIBLE` | arXiv:2505.19001 does not expose an author-code link or a unique frozen integration for this instrumented HNSW build. |
| Escape Hardness | `BASELINE_NOT_REPRODUCIBLE` | arXiv:2510.22316 does not expose a uniquely reproducible author implementation and cost configuration in the allowed evidence. |

No baseline was reconstructed or tuned after viewing the 100K results. `BASELINE_NOT_REPRODUCIBLE` is an evidence boundary, not evidence that the method is ineffective.
