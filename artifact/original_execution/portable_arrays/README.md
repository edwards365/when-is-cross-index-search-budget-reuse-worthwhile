# Profile CSV to frozen analysis arrays

The profile stage returns ordered CSVs. Analysis and the cache stage consume
NPZ arrays. This entry bridges that interface using the historical schema and
hit-count calculation, with independently validated row order, returned IDs,
native count range and frozen output identities. No ANN, statistical fitting,
bootstrap, qualification decision or timing measurement is performed.

```sh
python3.11 -m pip install numpy==1.26.4
python3.11 -m unittest discover -s artifact/original_execution/portable_arrays -p test_arrays.py -v
python3.11 artifact/original_execution/portable_arrays/materialize.py \
  --profile-adapter artifact/original_execution/portable_profiles \
  --truth-adapter artifact/original_execution/portable_truth \
  --input-adapter artifact/original_execution/portable_fresh_inputs \
  --prepared /path/to/new-prepared-inputs --truth /path/to/new-sift-truth \
  --profiles /path/to/new-sift-evaluation-profiles \
  --dataset sift --role target_evaluation --output /path/to/new-sift-arrays \
  --outstanding-growth-bytes 268435456 --authorize-materialization
```

Production encoding requires Linux/Python3.11/NumPy1.26.4. The command validates
the preceding new receipt and all eight frozen CSVs before producing one role
NPZ. `query_ids`, `action_grid`, `build_ids`, `hits`, `ndc`, `topk` retain their
historical ordering and dtypes. The final bytes must match `config.json`; a
mismatch preserves the failure and stops downstream work. No old audit file is
overwritten or presented as newly executed.

The bounded packaging/materialization plan is oneCPU2, AS8GiB,128MiB file limit,
CPU/wall900s, expectedRSS4GiB and256MiB growth. Existing200GiB projected disk,
128GiB total outstanding growth and RAM checks apply. All remaining allocations
must be included in the declared growth. This plan is for array serialization,
not a new scientific measurement or a modification of a frozen experiment.

For the cache entry, assemble the seven files under the relative names in
[`portable_cache/inputs.json`](../portable_cache/inputs.json): membership and
two qbins from prepared inputs, two evaluation truth files, and these two
evaluation profile arrays. All seven hashes must match before `cache_stage.py
check` succeeds. No dataset or generated truth is automatically downloaded.

Scope: 12 synthetic tests cover parsing, exact hit values, dtypes, output order,
ineligible IDs, malformed or incomplete grids and overwrite rejection. Full
original arrays were not recomputed during packaging. Positive native counts
are structurally checked, not independently remeasured. The graph-construction
dependency upstream of profiles remains unresolved by this serialization step.
