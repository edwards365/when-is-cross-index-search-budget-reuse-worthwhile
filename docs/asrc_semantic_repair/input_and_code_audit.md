# ASRC input and code audit

Evidence label: `EXPLORATORY_REPAIR`. Frozen parent: `6a8cbcf7cf9f8f2f6734b05132e13d0f21e476bb`.

| Status | File / function / field | Finding |
|---|---|---|
| VERIFIED | `src/rebuild_portability_recovery/m0_m1.py:23-39`, `load`; fields `y`, `c` | A query with no persistent safe budget is encoded with `y=11` and `c=True`; censoring is preserved separately. |
| VERIFIED | `tests/graph_anns_positive_closure/run_crossfit_asrc.py:19-21`, `eval_metric` | Evaluation counts `(allocation < y) OR c`, i.e. the requested absolute event. |
| MISMATCH | same file, lines 33-34 and 43 | B1/B2/B5 maximum-residual calibration uses only `y-allocation`; it does not include `c`. |
| MISMATCH | same file, lines 52-56 | ASRC stage certification counts only `y > allocation`; endpoint-infeasible `c=True` is omitted. |
| MISMATCH | same file, lines 66-69 | Terminal B1 certification also omits `c`, while later evaluation includes it. |
| VERIFIED | same file, lines 27-29; frozen split manifest | Source train, source calibration, target sentinel, and target evaluation are pairwise disjoint within each cycle; all 48 recorded overlap checks are zero. |
| VERIFIED | same file, lines 48-70 | Target evaluation labels are used after action selection, not in candidate certification or the cost stop. |
| VERIFIED | same file, lines 52-56 | Candidate order is frozen `11 -> 0`; the first non-certified more aggressive step stops the sequence. |
| VERIFIED | same file, line 14 and `docs/graph_anns_positive_closure/asrc_theory.md` | Three stages use `alpha_j=0.05/3`; the written fixed-sequence/union-bound application matches this allocation. |
| MISMATCH | frozen report and `asrc_summary.csv` | The 35,988/36,000 figure measures repeat stability under dependent repeated sentinel orderings; it is not a direct independent-binomial test of the 5% PAC statement. |
| AMBIGUOUS | frozen B5 label | B5 is a target-trained proxy on cross-fit roles, not a timed full rebuild/retraining cost measurement. |
| NOT_ESTIMABLE | truth-generation cost | No auditable exact-truth timing log is present; total cost break-even must remain symbolic. |

The repair defines one shared function in `src/asrc_semantic_repair/safety_events.py`: `Z_abs=(allocation<required_budget) OR c` and `Z_rec=(allocation<required_budget) AND NOT c`. The frozen CSVs remain unchanged. All repaired outputs must carry `SEMANTIC_REPAIR`/`EXPLORATORY_REPAIR` labels.
