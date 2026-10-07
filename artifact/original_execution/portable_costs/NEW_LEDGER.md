# New-measurement lifecycle bridge

`new_ledger.py` connects **future new measurements** to the original lifecycle
equations. It is separate from `components.py`, which verifies saved paper
components. Neither tool replaces historical measurements. New full-data runs
remain explicit opt-in; none were run to prepare this bridge.

## Measured inputs, not supplied cost numbers

Every request leaf is a reference of the following form:

```json
{"directory":"/path/to/NEW-completed-stage","sha256":"SHA256_OF_COMPLETED_JSON"}
```

Only receipt references are accepted. The request cannot provide setup seconds,
lookup time, profile time, chosen actions, or a favorable break-even threshold.
The reader verifies completion status, absence of failure, receipt SHA, referenced
payload hashes, dataset/role/graph identity, query order, frozen response arrays,
and lock-to-evaluation relationships. Provenance in the derived report contains
logical labels and file hashes, not private machine paths.

Top-level fields:

| Field | Required new producer |
|---|---|
| `roles` | `measure_operational.py`, kind `roles` |
| `decision_measurement` | Same entry, kind `decision`; original timed certification block |
| `policy_lock` | `portable_policy/run_policy.py certify` |
| `policy_evaluation` | `portable_policy/run_policy.py evaluate`, bound to that lock |
| `baseline_lock` | `portable_baselines/run_baselines.py lock` |
| `baseline_evaluation` | Its `evaluate` stage, bound to that lock |
| `cache` | `portable_cache/cache_stage.py measure` |
| `datasets` | Both `sift` and `arxiv`, each with the fields below |

Each dataset object contains:

| Field | Structure and producer |
|---|---|
| `prepared` | One `portable_fresh_inputs` completed receipt |
| `truth` | One `portable_truth` completed receipt, with all four role outputs |
| `graphs` | Map of all eight build IDs to `portable_graphs` completed receipts |
| `reloads` | Map of each build ID to exactly three `portable_reload` references, reps 0/1/2 |
| `profiles` | Map of all four role names to `measure_operational.py` kind `profiles` |
| `arrays` | Same four roles, from `materialize_operational.py`; bound to those measured profiles |
| `timings` | All eight builds, from `portable_timing/run_timing.py` |

The four role names are `source_design`, `target_selection`,
`target_certification`, and `target_evaluation`. Build IDs are the eight entries
in `operational_config.json`: seeds 13/83/197/2029 crossed with `random` and
`norm_ascending`. Each map must be complete; duplicate or missing coverage is
rejected. Expected query counts remain 500/500/500/1000 and roles are disjoint.

## Future phase order

1. Produce new role-firewall/prepared inputs, exact truth and all eight graphs.
   Use `portable_graphs/build_graph.py --measure-operational-unit` for the
   original full graph-unit timing boundary. A successful final completed
   receipt after frozen graph-byte checks is required; the intermediate
   `operational.json` is not sufficient.
2. Measure source, selection and qualification profiles at their original
   process boundaries; materialize each through `materialize_operational.py`.
3. Measure and lock certification before evaluation. The measured decision and
   portable policy lock must have identical semantic rows. Lock TG/fixed decisions
   from selection and qualification arrays. These decision operations do not
   execute ANN or replace measured profile costs.
4. Measure/materialize evaluation profiles, then evaluate both locked policies.
   Time the same evaluation graph/query pairs with `run_timing.py
   --operational-profiles`. Its optional `--operational-policy-lock` accepts the
   timed certification lock. The ledger accepts that prior lock or the matching
   portable policy lock; it requires the measured evaluation profile origin.
   This path does not require running a duplicate profile panel for timing.
5. Measure the original cache workload at the declared independent boundary.
   Its full-capacity, cyclic, 100-visit batch-lookup mean is the E3 comparator.
6. Bind each completed receipt in the JSON request and run:

```sh
python portable_costs/new_ledger.py --request NEW-ledger-inputs.json \
  --output /path/to/NEW-ledger --authorize-new-derived-ledger
```

Requires NumPy 1.26.4. This last command reads saved new outputs and performs
algebra; it does not launch native processes, time operations, contact remote
hosts, or invoke any old analyzer. Inputs are unchanged. Output must be a new
directory outside all input evidence trees. Failure is retained and cannot be
overwritten under the same path.

## Exact model correspondences

The implementation records the SHA identities of the three original formula
sources: `analyze_tcp_fresh_lifecycle_v1.py`, `lifecycle_campaign_v1.py`, and the
`e3`/`threshold` functions in `minimal_route_20261004_v1.py`. It does not execute
their historical drivers or fabricate the old status fields they require.

- **Per target:** arithmetic mean across seven timing repetitions, selected
  action per query, endpoint comparison; reload is the median of three fresh
  process measurements. Query-history acquisition is exact query read/search
  plus export plus seven source process costs, each net of its reload proxy and
  clipped at zero, divided by 1000. Both one-eighth setup allocation and a
  standalone target paying all eight graph/setup costs are reported.
- **Paired eight-target campaign:** identical graph build/reload costs are charged
  to both arms and cancel algebraically. Non-graph setup retains exact base
  acquisition, design/selection/qualification truth and profile costs, half the
  role-firewall time and half the measured decision time. The latter are the
  original operational allocations, not minimum unavoidable deployment costs.
- **Acquisition scenarios:** acquire separately only for targets locked to TCP;
  acquire separately for all targets; or acquire truth/export once and profile
  the union of required source graphs once. Search actions remain unchanged.
- **Alternative models:** TCP, deduplicated TCP, endpoint2400, fixed1600, TG500,
  TG1000 and full exact-answer cache. Fixed1600 uses qualification only; TG500
  uses half of the two 500-query role cost measurements; TG1000 uses both full
  roles. These remain full-grid allocation proxies, not selected-action timers.
  A method with incomplete deployment coverage is not zero-filled or silently
  compared on fewer targets.
- **Paired sensitivity:** original Q=100/1000/10000, V=1/2/10/50/100, fixed extra
  net cost 0/1/10/100 seconds, plus equal-sunk-assets comparisons. Q other than
  1000 is explicitly an extrapolation, including cache capacity/service scaling.

For each comparison, the identified contrast is `B - V*D`. For `D>0` the first
strictly profitable full round is `max(1, floor(B/D)+1)`. Original nonpositive-D
semantics are retained: no threshold for `B>=0,D<=0`; round 1 for `B<0,D=0`.
For `B<0,D<0`, the original broad initial-region label is refined to integer
visits: `finite_initial_region_only` applies only if `B/D>1`, with last strict
profitable round `ceil(B/D)-1`; otherwise no positive integer round is profitable.
This boundary refinement does not alter any saved paper calculation. It is not
eventual sustained break-even. With zero deployed TCP targets, deduplicated
query-specific acquisition is zero; fixed setup remains separately visible.
The report also gives the fixed +100-second threshold and `D/(8*1000)` per-request
net overhead that eliminates positive campaign savings. Unknown signed net cost
`U` is not measured or assigned an empirical bound by this calculation.

The lifecycle quality checks distinguish actual selected recall failures from
the candidate-or-endpoint union event used by the policy evaluation receipt.
Both are reported and neither is silently substituted for the other.

## Output and interpretation

`lifecycle.json` contains two datasets, per-target components, three campaign
scenarios, complete-covered method ledgers, and paired sensitivities. With all
four baseline methods covered, there are 605 paired rows per dataset. Its typed
status is `NEW_MEASUREMENT_DERIVED_CONDITIONAL_LIFECYCLE_COMPLETE`;
`completed.json` binds the report SHA.

If graph receipts lack a true `whole_unit_ns` with
`operational_unit_measured=true`, standalone target thresholds are explicitly
`NOT_ESTIMABLE_WHOLE_GRAPH_UNIT_TIME_ABSENT`. The sum of substage timers is shown
as a subtotal, never substituted for that interval. Matched campaign contrasts
remain computable because those common terms cancel by graph identity.

New graph measurements are **not** labeled with the historical orphan diagnostic
interference. Nor does absence of that old label establish host isolation. Reload
page-cache state stays unknown; cross-component hardware equivalence must be
checked from the supplied run environments. Cache lookup includes key creation
and value access, not insertion/transport. TG decision time, serving control,
network and maintenance remain unknown net costs. No confidence intervals,
matched-risk advantage, formal end-to-end acceleration, or repair of historical
E8 `NOT_ESTIMABLE` is claimed.

## Verification performed for this entry

```sh
python -m unittest discover -s portable_costs -p test_new_ledger.py -v
```

Synthetic tests cover algebra, exact strict thresholds, no positive saving,
initial-only benefit, identical graph cancellation, missing whole timers,
nonnegative reload proxy, partial coverage, actual-versus-union failure,
invalid measurements, receipt tampering/failure and rejection of caller cost
numbers. A full synthetic receipt-chain integration uses both dataset roles,
eight targets, four disjoint query roles and all producer schemas; it derives
both ledgers and rejects an altered timing-lock link. Fourteen tests pass locally.
They do not execute datasets or constitute new empirical results.
