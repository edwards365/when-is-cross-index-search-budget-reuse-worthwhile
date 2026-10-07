# Native single-query timing entry

This entry ships the unchanged `e1a_runtime_native.cpp`, a new build/test wrapper,
and an opt-in one-graph timing command. It uses the headers, license, 1,000-query
profile source and 32-vector fixture in the sibling `portable_profiles` directory;
their byte identities are pinned in `config.json`. Build the sibling entries from
the same artifact release. No historical timing receipt is manufactured.

## Build and synthetic verification

Linux x86_64, Python 3.11, NumPy 1.26.4 and a C++17 `g++` compiler are required.
From the artifact root:

```sh
python -m unittest discover -s original_execution/portable_timing -p 'test_*.py' -v
python original_execution/portable_timing/build_native.py \
  --profiles original_execution/portable_profiles \
  --output /path/to/new-timing-build \
  --authorize-build-and-synthetic-tests
```

The native test builds new 32-vector L2 and IP graphs, obtains reference responses
with the unchanged profile program, independently checks endpoint IDs against
float64 distances, then validates all 77,000 timed rows per metric. It uses the
complete 11-action, 1,000-query, seven-repetition protocol on these tiny graphs.
This verifies transport, clocks, ordered-ID comparison and row coverage; it does
not benchmark or reproduce the original million-vector measurements. Windows
runs skip the native test. No historical executable-byte identity is asserted.

## Execute one new production timing unit

First complete the input, graph, profile and qualification-lock entries. Pass the
SHA of the already-created qualification receipt explicitly. The timing command
checks that lock before reading evaluation inputs. Original graph, query and
reference-response hashes remain mandatory.

Arrange exclusive use of the measurement host before opting in. The receipt
records this caller assertion. A shared advisory lock on the native-build receipt
serializes this entry's units; it cannot exclude other host workloads. No forced
page-cache reset is performed. Run only after prior graph/profile/reload work has
finished, as in the original timing protocol.

```sh
python original_execution/portable_timing/run_timing.py \
  --input-adapter original_execution/portable_fresh_inputs \
  --policy-adapter original_execution/portable_policy \
  --policy-lock /path/to/new-qualification-lock \
  --policy-lock-sha256 QUALIFICATION_COMPLETED_JSON_SHA256 \
  --prepared /path/to/new-prepared-inputs \
  --profiles /path/to/new-sift-evaluation-profiles \
  --graphs /path/to/new-graph-build/indexes \
  --native-build /path/to/new-timing-build \
  --dataset sift --build seed13_random \
  --output /path/to/new-sift-seed13-timing \
  --outstanding-growth-bytes 1073741824 \
  --authorize-new-timing --assert-isolated-host
```

Use each of the eight registered build IDs on each dataset exactly once in a new
reproduction campaign. Each output must be a new directory. Retain failures; do
not retry failed measurement keys or use new measurements to overwrite sealed
results. No pilot, action-subset, seed-selection or repetition-count option exists.
The caller's outstanding-growth value must include other remaining campaign
growth, not just this unit. CPU2, 12 GiB address-space, 1 GiB per-file/output growth,
1,800-second native wall timeout, original CPU limit, 200 GiB disk floor and
128 GiB outstanding-growth ceiling are retained. RAM/I/O admission gates come
from the pinned input adapter; admission telemetry is not continuous isolation.

## Clock and aggregation boundaries

The unchanged native interval includes `searchKnn` and ordered top-10 extraction.
It excludes `setEf`, graph loading, warm-up, result verification and CSV I/O.
The source warms the first 50 queries per action, shuffles query order each
repetition, and shuffles actions per query using the original derived seed.
The seed includes the original full dataset name, graph ID and schedule seed 991.

`timed.csv` retains every wall/process-CPU observation and ordered ID list.
`DATASET_BUILD.npz` uses the original axes `(repetition, action, query)` with
`query_ids`, `action_grid`, `wall_ns`, `cpu_ns`. New timings are hardware and load
dependent and are not required to match historical time-array hashes.

`timing.mean_service(wall_ns, action_indices)` first takes the arithmetic mean of
the seven repetitions and then selects one locked action per query. It does not
take medians, discard slow repetitions or generate bootstrap intervals. The
returned vector can enter the frozen downstream paired analysis as **new timing
input**, retaining its new provenance; it must not replace the saved-input paper
reconstruction. Per-query process CPU values may be zero/coarse; wall time is the
primary measure. No network, cache-cold, concurrent-serving or end-to-end latency
claim follows from these measurements.

## Validation status

`validation.json` records the local synthetic result. Linux native verification
is additionally reported by the release's CI run. Full original-data timing was
not executed as part of delivery. Methods, saved timings and manuscript remain
unchanged.
