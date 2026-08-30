# Implementation forensics

Parent: `exp/asrc_pareto_recovery_boundary@5f4d04f6e836059c98024b01f4929bcd406cdcc1`. Evidence: `EXPLORATORY_HEADROOM_REAUDIT`.

| Item | Status | File / lines | Finding |
|---|---|---|---|
| A | VERIFIED_BUG | `tests/pareto_compute.py:15-23` | Mixture `risk_ucb` and `p95_ndc` are direct convex interpolations of stage summaries, not recomputed from episode failures/query-cost distributions. |
| B | VERIFIED_BUG | `tests/pareto_compute.py:43-48` | H3 groups by target build but takes `safe.mean_ndc.min()` over individual rows; it does not choose one `(method,stage)` and aggregate all sources/cycles. |
| C | VERIFIED_BUG | `tests/pareto_compute.py:48-50` | H4 is assigned the same aggregate as H3; `pair_stage_oracle.csv` merely copies every candidate row and never executes pair-level argmin. |
| D | VERIFIED_BUG | `tests/pareto_compute.py:30-39` | NaN NDC is treated as satisfying the NDC comparison, so an incomplete B1-max reference can participate in dominance. |
| E | VERIFIED_BUG | `tests/pareto_finalize.py:12-14,25` | Active-sentinel tables say `NOT_RUN_NO_NEW_TRUTH`, while the manifest sets `active_sentinel_executed=true`. |
| F | VERIFIED_BUG | `tests/pareto_finalize.py:8-14` | Generic splits include certification sizes below59 and do not label them theoretically uncertifiable controls. |
| G | VERIFIED_BUG | `tests/pareto_compute.py:8-11` | `risk_ucb` is the arithmetic mean of per-row CP upper bounds, not a target-build cluster UCB from the underlying failure statistic. |
| H2 unit | AMBIGUOUS | `tests/pareto_compute.py:15-23` | Only an analytic summary is stored; no episode-level outcome-independent stage draw exists. |
| H3/H4 evaluation use | VERIFIED_BUG | `tests/pareto_compute.py:43-49` | The same evaluation summaries are used both to choose and report the optimistic oracle; no 3-cycle/1-cycle cross-fit is implemented. |
| B1-max NDC | NOT_ESTIMABLE | `tests/pareto_compute.py:12-13` | Parent explicitly writes `mean_ndc=NaN`; it is an incomplete reference and must be excluded unless reconstructed from frozen records. |
| bootstrap statistic | VERIFIED_BUG | `tests/pareto_compute.py` | No corrected H2 target-build bootstrap is computed in the parent script. |
| early signal | NOT_ESTIMABLE | `tests/pareto_compute.py:51` | Parent writes a placeholder without fitting or evaluating any deployable signal. |
| frozen replay sufficiency | AMBIGUOUS | frozen repair CSVs | Episode-level RM rows exist, but sealed query-level costs/actions needed for exact p95 mixture replay may require deterministic replay from frozen training/design records. |

The parent 39-item SHA256 verifies artifact stability only; it does not validate these statistical semantics. Parent artifacts remain unchanged.
