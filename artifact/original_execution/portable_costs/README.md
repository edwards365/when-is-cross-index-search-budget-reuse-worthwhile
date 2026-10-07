# Cost-component evidence and reconstruction

The 79 records connect the lifecycle ledger to its original graph builds,
fresh-process reloads, exact truth acquisition, full-grid profiles, role firewall,
decision lock, evaluation and independent audits. Each manifest entry records
both the original SHA and the delivered SHA. Only private path prefixes were
transformed; numbers and scientific fields were not changed.

```sh
python artifact/original_execution/portable_costs/components.py --output /new/path/component-check
python -m unittest discover -s artifact/original_execution/portable_costs -p 'test_components.py' -v
```

The standard-library entry regenerates all 12 fixed-component rows and compares
them with the paper's saved table, using a 1e-10-second tolerance for Decimal vs
historical float summation. It also exposes each of the 16 graph build times and
its median of three reloads. It performs no ANN, truth search, model training or
new timing. The complete curves, uncertainty and alternative-sharing analyses
remain in the [saved-result reconstruction](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-paper-v2).

## Meaning of the fixed components

- Exact-base acquisition and role truth read/search have separately recorded
  timers. Training-role profiles charge source-design, selection and qualification
  as the original process did, including preparation and serialized execution.
- Half the role-firewall wall time and half the decision computation are ledger
  allocations to each dataset. These are not claims of minimum deployment costs.
- Interfered graph-build and cache-unknown reload terms cancel only when both
  sides require the same eight graphs. They cannot support an isolated build
  benchmark or a single-graph deployment claim.
- Missing costs are never replaced with zero. The paper's net-overhead analysis
  remains a separate conditional model; E8 stays NOT_ESTIMABLE.

## New execution versus reconstruction

The [truth](../portable_truth/README.md), [profiles](../portable_profiles/README.md),
[policy](../portable_policy/README.md), [reload](../portable_reload/README.md) and
[API timing](../portable_timing/README.md) entries produce new measurements and
receipts. Their outer wrapper timers are not all identical to the old operational
boundaries: new preparation includes query exports; new policy computation omits
some input reads; profile query export is prepared earlier. This entry rejects
those new receipt types rather than relabeling their wall times as old components.
The [operational measurement entry](OPERATIONAL_MEASUREMENTS.md) now exposes
the original role, profile and decision timer boundaries on new outputs.
`materialize_operational.py` connects its verified profiles to the normal policy
and baseline entries. Graph construction separately offers the original
whole-unit timer through `portable_graphs --measure-operational-unit`.

The [new lifecycle bridge](NEW_LEDGER.md) consumes these typed measurements,
paired graph/reload receipts, locked evaluations, API timing and cache records.
It derives the original conditional cost equations without accepting caller-
supplied cost numbers. Missing whole-graph timing prevents standalone thresholds;
it does not prevent the matched eight-graph scenario where those costs cancel.
These are future execution interfaces and synthetic-tested integrations, not new
full-data measurements or replacements for the saved paper ledger.
