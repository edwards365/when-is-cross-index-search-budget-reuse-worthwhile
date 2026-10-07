# New operational measurements at the original boundaries

This is a future execution entry, not a replacement for saved lifecycle timings.
Three original timed blocks are copied without scientific or timer changes into
`operational_core.py`; `assemble_operational.py` records their source identities.
The assembler is maintenance tooling requiring the source archive; consumers run
the assembled core, not the assembler.

| Kind | Timed boundary | Deliberately outside that timer |
|---|---|---|
| `roles` | Both datasets: receipt construction, raw HDF5 hashing, new role generation, full content firewall, compressed membership output and its identity | Prerequisite verification, directories, final receipt write |
| `profiles` | One dataset/role: query read, E1AQ0001 export and fsync, all eight graph-receipt and index checks, eight native subprocess waits including reload, per-graph receipts | Initial prerequisite verification and final receipt write; frozen CSV identity validation afterwards |
| `decision` | Both datasets: audited qualification-array hash/read/decompression, labels, candidate/endpoint checks, 16 locked decisions | Bound-input record creation, final decision-file write, expected-row comparison |

Profile timing is the original whole eight-graph phase, not the sum of unrelated
portable per-unit timings. Graph hashing remains within it. The decision timer
includes array loading and does not read evaluation arrays. The original
statistical rules are unchanged. Compatibility graph receipts bind newly built
indices to their frozen content identities; they do not claim to be old receipts.

## Requests

Every request needs `portable_fresh_inputs` pointing at that adapter directory.
All paths are explicit consumer-selected paths; outputs must be absent.

* `roles`: `kind`, `old_roles`, `old_exclusions`, `e1b_candidate`, `raw_sources`
  (mapping full dataset names to raw HDF5 paths).
* `profiles`: `kind`, `dataset` (`sift` or `arxiv`), `role`, `source`, `prepared`,
  `truth`, `native_build`, `portable_truth`, `portable_profiles`, and `graphs`.
  `graphs` maps all eight registered build IDs to `{receipt, index}`. Prerequisites
  are new successful preparation, independently checked exact truth, native build,
  and graph outputs. No prepared qbin substitutes for the timed query export.
* `decision`: `kind`, `arrays` mapping `sift` and `arxiv` to new qualification-array
  directories, and `portable_policy`. Both audited arrays must match frozen pins.

```
python measure_operational.py --request NEW_REQUEST.json --output NEW_DIRECTORY \
  --outstanding-growth-bytes 536870912 --authorize-new-operational-measurement
```

Linux x86-64, Python 3.11, NumPy 1.26.4, h5py 3.11.0 and SciPy 1.13.1 are required.
CPU 2, conservative memory/disk/iowait gates, inherited RLIMIT caps, stage wall
timeout, exclusive outputs, true subprocess exits and preserved failure records
apply. The declared growth must include all outstanding project growth, not just
this command. The aggregate output check is not a continuous filesystem quota.

The profile output is intentionally audit-pending. Run `materialize_operational.py`
with `--profiles NEW_TIMED_PROFILE_OUTPUT --prepared NEW_PREPARATION --truth NEW_TRUTH`
and the four `--input-adapter`, `--truth-adapter`, `--profile-adapter`,
`--array-adapter` directories, plus `--dataset`, `--role`, `--output NEW_ARRAY_DIR`,
`--outstanding-growth-bytes` and `--authorize-materialization`.
This explicit bridge checks new operational receipts and all frozen CSV pins,
then invokes the same full ordered returned-ID/recall/array construction functions
as portable_arrays. Its new array receipt is directly consumable by the decision
entry. It neither forges the old portable_profiles receipt nor independently
recomputes native distance counters. Profiles do not export returned distances.
These timing files can populate a **new** ledger scenario with the separately
measured graph/truth/reload components. They cannot overwrite historical ledger
values, establish equal hardware/cache conditions, or repair E8's unavailable
historical acquisition interval. Preserved operational boundaries are not a claim
of formal isolated benchmark conditions or minimum necessary deployment costs.

## Bounded tests

```
python -m unittest discover -s portable_costs -p test_operational.py -v
```

Six new synthetic tests check the operational-to-array receipt bridge, original timer starts, full 7,500-role
partitions using tiny 4-dimensional vectors, all eight profile subprocess waits
with mock child results, failure receipts with a real reported nonzero code, and
qualification-array reads between timer endpoints. They do not execute ANN or
the original datasets. Linux CI should run the same tests; native functionality
is separately covered by the portable profile adapter's tiny native tests.
