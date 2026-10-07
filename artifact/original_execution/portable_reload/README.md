# Fresh-process reload measurement

This isolated entry preserves the original clock boundary: construct the HNSW
object, load the saved graph, set one thread, then stop the timer. No query or
recall outcome is accessed. The input graph is hashed **before** loading, as in
the original protocol; the resulting measurement is OS-cache-unknown, not cold.

Use the source-built hnswlib environment from
[the graph entry](../portable_graphs/README.md). One invocation measures one
registered graph and repetition; each invocation is a separate process.

```sh
python -m unittest discover -s artifact/original_execution/portable_reload -p test_reload.py -v
python artifact/original_execution/portable_reload/run_reload.py \
  --input-adapter artifact/original_execution/portable_fresh_inputs \
  --graph-adapter artifact/original_execution/portable_graphs \
  --graphs /path/to/new-graph-panel --dataset sift --build seed13_random --rep 0 \
  --output-root /path/to/new-reload-panel --outstanding-growth-bytes 16777216 \
  --authorize-reload-measurement
```

The registered repetitions are 0,1,2 for each of eight graphs per dataset.
Select subsequent units explicitly and keep the same new panel root. A lock
prevents concurrent reload units; failed/unfinished units and existing output
keys prevent continuation. The panel retains a 7200-second wall deadline;
each unit has CPU/wall900 seconds, AS12GiB, file16MiB, CPU2 and one library
thread. The adapter declares expectedRSS8GiB and 16MiB maximum receipt growth,
and applies the existing RAM, 200GiB disk floor and128GiB outstanding-growth
checks. Declare all remaining project allocations, not only this minimum.

Eight synthetic tests cover the timer boundary, count mismatch, exact three-
repeat median, missing/duplicate samples, changed graph identity and invalid
durations. The Linux-only native test loads two new tiny graphs in separate
processes. It is neither one of the 48 benchmark reloads nor a performance result.

New receipts identify the source build and exact graph bytes and are not old
historical receipts. The historical extension's missing build provenance stays
missing. Repeated measurements do not repair or overwrite historical cost
values. Lifecycle reconstruction from saved components remains a distinct
published path; new measurement aggregation must retain its own time boundary.
