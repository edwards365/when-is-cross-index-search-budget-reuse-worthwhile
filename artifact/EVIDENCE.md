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

## Whole-paper reproduction coverage

The map distinguishes numerical reconstruction from saved-output inspection and original measurement. **READY** means a supplied runnable saved-record path; **PARTIAL** means some evidence is supplied but the listed upstream reconstruction is absent; **OPEN** means no executable path is provided by this artifact entry. An unavailable command is explicitly marked, never replaced by an old host launcher.

Run figure-statistic routes with `python artifact/reproduce_paper.py --output paper-reconstruction`, or select `--parts F02`, `F04`, `F05`, or `F06`. See [the paper-statistics runbook](paper/README.md). Figure 3 retains [its original release command](RUNBOOK.md). The [narrative runbook](narrative/README.md) supplies archive-download and new-output commands for the two additional runners below. READY is always qualified by its input layer; it does not imply original ANN reproduction.

| Paper result | Input / retained evidence | Script and command | Expected output | Status and remaining boundary |
|---|---|---|---|---|
| Figure 1, conceptual overview | No measured input | Not a statistical reconstruction | Three information/deployment/cost relations | PARTIAL: editable figure/paper bundle is separate from this numerical release |
| Figure 2, §4.1 transfer/reference means and intervals | 96 original saved grid CSVs; `paper/inputs/graph_only_query_clusters.csv` | `reproduce_grid.py` then `reproduce_paper.py --parts F02 --output f02-output` | Raw-to-cluster identity, `F02_intervals.csv`, four groups / 12 intervals | READY from recorded hits/recall through all 3,000 clusters to intervals; no new truth/ANN measurement |
| §4.1 finite-label variation, 75.87–91.07% | Same 96 grid CSVs | `reproduce_grid.py` with pinned archive and new output | `query_labels.csv`, `finite_variation.csv` | READY: all 750 queries in each denominator; distinct finite first-passing labels across builds |
| §4.1 million-scale transfer and 100K/million refresh extensions | Direction counts; paired 100K failures; 16 million-refresh hit arrays/locks | `reproduce_narrative.py --parts refresh extensions` with archive and new output | `million_transfer.csv`, `refresh100k.csv`, `million_refresh.csv`, four original refresh intervals | READY at declared saved-record levels; transfer query-level extraction and 100K locked-policy extraction remain upstream |
| §4.2 594/648 demand-mixing diagnostic | Independent nine-combination `confirm` query labels | `reproduce_narrative.py --parts diagnostic` with archive and new output | All 648 cell-mixing rows | READY from saved labels, not original recall-to-label generation; source no-finite-tail encoding retained |
| §4.2 Vamana zero-cost cases | Query labels and original pair-cost table in narrative archive | Same `--parts diagnostic` command | `diagnostic_zero_cases.csv`: 18 pairs per dataset, 750 identical actions each | READY for action-identity explanation of zero difference: both sides use the same recorded query/action cost. Not an independent NDC measurement or reconstruction of nonzero historical cost curves |
| §4.3 propositions and measured-cost objective | Definitions and proofs in paper; `reference/summary_analysis.py` for finite computation | Nine-table runbook; inspect `objective` implementation | Common-action objective and ordered dynamic program | READY for supplied finite computations; not a proof of future-query safety |
| Figure 3, §4.4 same-condition costs / coverage / 69-of-72 observation | Response v1 NPZs and decisions | `reproduce_summary.py --archive summary-analysis-inputs.zip --output summary-output` | `objectives.csv`, `coverage.csv`, `target_feasibility.csv`, aggregates | READY, all targets/summaries/safety criteria retained |
| §5.1 fresh-panel raw/union/deployed counts | Response v1 evaluation profiles and lock | Same nine-table command | `policy_bridge.csv` | READY; does not cover the separate 100K/Deep panels |
| §5.2 100K prospective validation and Deep1M recovery | 100K locked cells and timing means; all 72,000 Deep1M action rows | `reproduce_narrative.py --parts recovery deep` with archive and new output | Points, decisions, four 100K risk/time and two Deep risk/work intervals | READY; Deep source selection and qualification reconstructed; 100K decision generation and seven-repeat extraction upstream |
| Figure 4, §5.2–5.3 fresh-panel points and paired uncertainty | `paper/inputs/*_paired.npz` | `reproduce_paper.py --parts F04 --output f04-output` | Ten operating points, 24 paired intervals, LOTO checks | READY from locked-policy matrices; raw seven-repeat timing extraction and original selection reconstruction remain upstream |
| §5.3 100K fixed/target-global baseline comparison | All nine arms' locked paired cells, decisions and recorded timing means | `reproduce_narrative.py --parts recovery` with archive and new output | `recovery_points.csv`, `recovery_decisions.csv`, SIFT action-256 identity check | READY for reported point estimates; does not create new baseline intervals or recompute original qualification selection |
| §5.3 qualification sensitivity | Response v1 qualification/evaluation profiles and baseline decisions | Nine-table command | `qualification_sensitivity.csv`, `qualification_aggregate.csv` | READY; fixed candidate choices, no new sensitivity intervals |
| Table III fixed components | Response v1 lifecycle/ledger records | Nine-table command | `fixed_cost_components.csv` | READY as ledger decomposition, not minimum required deployment cost |
| Figure 5, §6 curves and overhead boundaries | `paper/inputs/component_ledger.csv` | `reproduce_paper.py --parts F05 --output f05-output` | 320 curve rows, four threshold/boundary rows | READY as conditional arithmetic; original component measurement is upstream |
| §6 alternative-policy cost comparison | SHA-pinned `paper/inputs/component_ledger.csv` | `reproduce_narrative.py --parts cost` with archive and new output | `alternative_costs.csv`, 14 paired component comparisons | READY as conditional ledger arithmetic; unknown net overhead excluded, not measured as zero |
| Figure 6 lookup / memory | `paper/inputs/cache_raw_blocks.csv`, `cache_memory.csv` | `reproduce_paper.py --parts F06 --output f06-output` | 80 lookup means / 560 blocks; plotted lookup and memory values | READY for batch means; memory is saved object-size measurement, not remeasured |
| §3 native coverage, Faiss identity/counter/timing scope | Seven path-redacted historical closure/implementation records | Inspect `native_evidence/README.md` and linked records | Identities, role checks, inclusion/exclusion and measurement scope | PARTIAL: summaries now public; full raw audits, binaries, source/config and original execution remain incomplete |
| Tables I/II/IV | Protocol definitions and synthesis, rather than new estimates | Inspect paper, these rows and `EXECUTION_SCOPE.md` | Panel navigation, information conditions, implications | PARTIAL: saved-record paths explicit; full original protocol/source integration remains incomplete |
| Full original ANN execution | Datasets, versions, build/search/train protocols and bounded resources | No unified portable command supplied | Original response arrays and measurement records | OPEN: requires licensed acquisition, dependencies, source/config integration and execution runbook |

This update supplies saved-record reconstruction for the numerical figures and the listed narrative panels. The Vamana zero-cost example is checked by per-query action identity, not by remeasuring NDC. Full native audit/source payloads and original data acquisition/response-generation workflows remain incomplete. [Execution scope](EXECUTION_SCOPE.md) enumerates those dependencies rather than offering a host-bound launcher as a portable command. Replotting a saved mean is not recomputing an interval, and neither is remeasuring ANN.
