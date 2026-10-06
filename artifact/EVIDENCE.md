# Evidence map and interpretation

The paper's three questions are related but not interchangeable. The following files are saved outputs, not fresh measurements produced during repository publication.

| Paper question/location | Files under `data/` | Use |
|---|---|---|
| Summary constraints, §4 / mechanism figure | `summary_information_bridge/objectives.csv`, `coverage.csv`, `target_feasibility.csv`, `summary_aggregate.csv`, `budgets.csv` | Feasibility, singleton/mixed-cell coverage, and conditional empirical-optimum work |
| Candidate versus locked deployment | `summary_information_bridge/policy_bridge.csv` | Keeps actual failures and stable-tail violations separate |
| Quality–cost comparisons, §5 | `E1_report.json`, `E1_target_summaries.csv`, `E1_comparisons.json`, `operating_points_readable.csv`, `paired_intervals_readable.csv` | Saved operating points and original paired intervals |
| Qualification sensitivity, §5 | `summary_information_bridge/qualification_sensitivity.csv`, `qualification_aggregate.csv` | Fixed-candidate event/alpha sensitivity; retrospective, no new intervals |
| Conditional lifecycle, §6 | `E3_ledger.csv`, `E3_report.json`, `summary_information_bridge/fixed_cost_components.csv`, `cost_boundaries.csv` | Ledger-derived cost components, sharing and overhead boundaries |
| Valid-answer lookup, §6 | `E2_report.json`, `E2_lookup.csv`, `E2_memory.csv` | Static admission and a measured hit path, not a general cache service |

## Names and units

- `TCP` in saved output fields is the paper's **History-Max** policy, not the network transport protocol. Original field names are retained for traceability.
- `target_certification` is the historical qualification-query role. Its name alone does not confer a statistical guarantee.
- `ndc` is native distance-computation work in the specified implementation; it is not latency. `search_ns` measures the stated ANN API path, not complete service overhead.
- `fixed_cost_components.csv` uses the column `seconds` even when component identifiers end in `_ns`; those identifiers name original ledger fields, whose values have been converted to seconds.
- Empty objective values mean infeasibility/not-defined under the accompanying status columns, **not zero**.

## Comparisons that must be preserved

The vector, maximum-label and order-constrained optima use the same target, action grid, quality threshold, and query subset. Targets have equal weight. Conditional objectives renormalize query weights within each target's endpoint-passing subset. Full-query infeasibility and excluded-query proportions are retained separately. Target responses are known to these retrospective references; their differences are not deployment speedups or a prediction of generalization. Singleton coverage is substantive context, not an optional caveat.

Actual safety and stable-tail safety are distinct. In a finite grid, a finite stable tail exists exactly when the endpoint passes. A failed endpoint does not imply every smaller action fails. No off-grid finite solution is assumed.

Candidate failure, endpoint failure, their union, and locked-policy failure are different events. Raw/union equality in this panel is specific to History-Max; it must not be generalized to TG. Existing confidence intervals belong to their original operating points and do not transfer to changed sensitivity decisions. This is not a risk-matched causal estimate of the value of source information.

One lifecycle round is 8,000 requests. Fixed workflow charges include profiling and allocated operational work and are not asserted to be unavoidable minimum deployment costs. Unknown terms are policy-minus-baseline net costs. Shared setup, unchanged valid answers, and repeated requests are scenario assumptions; break-even is a model result, not measured end-to-end acceleration. Lookup excludes insertion and transport.

## Coverage not supplied by this snapshot

This entry does not yet reproduce all 100K panels, the historical multi-build diagnostic, original native runs, or all six paper figures. The public availability of these selected results must not be cited as proof that all paper inputs and commands have been delivered.
