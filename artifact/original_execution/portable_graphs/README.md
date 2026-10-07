# Frozen fresh-query graph construction entry

This is the upstream dependency of the profile entry. It preserves the
historical train-only base read, raw-ID ordering, RandomState permutations,
float64 norm/raw-ID lexicographic order, M16/efConstruction100, seed and
single-thread insertion. It constructs one explicitly named graph per process,
not an automatic benchmark sweep. No source/target query outcome is consumed.

## Explicit source build

The public hnswlib0.8.0 source archive is hash pinned. All seven headers match
the original replay header commit. The historical installed Python extension
has no saved source-build provenance sufficient to attest its complete build;
the recipe below is an **explicit new source build**, not that missing record.
Build-tool choices are recorded in `config.json`, not described as historically
identical. Every resulting benchmark graph must match its frozen original SHA
before the entry reports success.

```sh
python3.11 -m venv graph-env
graph-env/bin/python -m pip install -r artifact/original_execution/portable_graphs/requirements-build.txt
graph-env/bin/python -m pip install --no-build-isolation --no-deps -r artifact/original_execution/portable_graphs/requirements-native.txt
graph-env/bin/python -m unittest discover -s artifact/original_execution/portable_graphs -p test_graphs.py -v
```

The Linux native test builds four tiny64-vector graphs (two metrics × two
insertion orders), verifies every retained vector/raw-ID association after
reload, and compares endpoint query results with float64 exhaustive references.
This is delivery-interface testing, not a rerun of the experiment's graphs.

## One original-data unit

```sh
graph-env/bin/python artifact/original_execution/portable_graphs/build_graph.py \
  --input-adapter artifact/original_execution/portable_fresh_inputs \
  --prepared /path/to/new-prepared-inputs --source /path/to/sift-128-euclidean.hdf5 \
  --dataset sift --seed 13 --history random --output-root /path/to/new-graph-panel \
  --outstanding-growth-bytes 51539607552 --authorize-graph-build
```

Registered seeds are13,83,197,2029; histories are random and norm_ascending.
Use the same new graph root for subsequent explicit units; a filesystem lock
prevents concurrent units, and any unfinished or failed unit blocks later work.
Existing indexes and unit receipts are never overwritten or retried. Both
datasets produce files in `indexes/` matching the profile entry's filenames.
Pass that directory to `run_profiles.py --graphs`.

Original resource conditions remain: CPU2, one library thread, AS24GiB,
8GiB per-file, CPU/wall3600s per unit, expectedRSS16GiB,48GiB panel growth,
200GiB projected disk floor and128GiB total outstanding growth. Declare the
whole remaining allocation, including other stages. Resource snapshots and
final checks are not continuous process-tree or aggregate-storage quotas.

Full-data construction has not been run for this delivery. Synthetic success
does not establish full serialized-graph equivalence on another compiler/CPU.
A graph hash mismatch remains a real failed reproduction and must not be
fixed by changing the expected hash, dropping a graph or trying multiple builds
until one matches. New construction times do not replace historical costs.
