# Deep1M recovery execution entry

This is a separate historical panel, not the train-only fresh-query panel. It uses the first 1M Deep train vectors, cosine graphs (four seeds × random/norm-ascending), and three frozen 500-query roles from the HDF5 **test** member. The recovery grid is 200/300/400/600/800/1200. Original numerical function bodies and native counting runner are packaged unchanged. `check` regenerates role IDs without reading any dataset.

## Install and verify

Use Linux x86-64 Python3.11 and a C++17 compiler:

```sh
python -m pip install -r requirements.txt
python -m pip install --no-build-isolation --no-deps -r requirements-native.txt
python run_deep.py check
python -m unittest -v test_deep
```

The native test builds only two 64-vector cosine graphs, checks 12 synthetic queries at three actions against the Python native implementation, and checks endpoint IDs against independent float64 exact ranking. It is not a million-scale rerun or benchmark.

## Separate opt-in phases

Obtain `deep-image-96-angular.hdf5` from the URL in `config.json`; its full SHA is required. Each output must be new, and its parent must exist. Set `GROWTH` to the actual aggregate outstanding project growth in bytes, including all concurrent remaining stages; it must be at least12GiB and no more than128GiB. The projected free-space floor is200GiB. Production preflight retains CPU2, RAM/iowait checks, AS16GiB and finite file/CPU/wall limits. These are conservative new delivery resource bounds, not a claim about original operational measurements.

```sh
python run_deep.py prepare --dataset /path/to/deep-image-96-angular.hdf5 --output /new/root/prepared --outstanding-growth-bytes "$GROWTH" --authorize-new-execution --authorize-historical-test-member
python run_deep.py compile --output /new/root/native --outstanding-growth-bytes "$GROWTH" --authorize-new-execution
python run_deep.py build --dataset /path/to/deep-image-96-angular.hdf5 --seed 3011 --history random --output /new/root/graph3011random --outstanding-growth-bytes "$GROWTH" --authorize-new-execution
```

Run `build` separately for each of seeds3011/3203/3413/3617 and histories`random`/`norm_ascending`, with distinct outputs. The original input and graph hashes must match; a mismatch fails without repinning. Then supply all eight graph output directories:

```sh
python run_deep.py replay --prepared /new/root/prepared --native-build /new/root/native --graphs /new/root/graph3011random /new/root/graph3011norm /new/root/graph3203random /new/root/graph3203norm /new/root/graph3413random /new/root/graph3413norm /new/root/graph3617random /new/root/graph3617norm --output /new/root/replay --outstanding-growth-bytes "$GROWTH" --authorize-new-execution
python run_deep.py analyze --replay /new/root/replay --output /new/root/analysis --outstanding-growth-bytes "$GROWTH" --authorize-new-execution
```

`analyze` invokes the unchanged original source-slack qualification and5000-replicate analysis. It is never executed by import, `check`, or synthetic tests. Replay CSVs include newly measured wall times; their complete hashes are not expected to equal historical timed CSVs. New receipts bind all prerequisites and outputs. A newly compiled runner is not claimed byte-identical to the historical binary. The adapter does not establish that an untested future toolchain produces identical native responses; this is distinct from pinned graph/query/truth checks.

No original dataset, original graph, old scientific response, or old auditor was executed by preparation of this delivery. In particular, packaging does not lift the project's restriction on accessing historical test data: future full prepare explicitly requires the named authorization flag. This entry does not revise the frozen methods, role membership or paper results.
