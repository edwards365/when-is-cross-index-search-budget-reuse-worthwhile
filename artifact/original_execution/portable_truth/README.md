# Exact-truth execution entry

This stage connects the fixed fresh-query input preparation to exact top-10
truth. It does not run ANN, select a strategy, change a role, or overwrite an
old result. The four historical role sizes, base order, raw float32 vectors,
SIFT squared-L2 and Arxiv inner-product metrics remain unchanged.

## Native dependency identity

The original environment's **32 package and bundled-library payload files**
match the public Linux x86-64 CPython 3.11 `faiss-cpu 1.8.0.post1` wheel in
`native_lock.json`. Its Python module reports `1.8.0`. Install the exact wheel
URL and SHA in `requirements.txt`, not an arbitrary Faiss 1.8.0 package.
The lock records a present-day byte comparison, not a retrospective loaded
library attestation. Historical receipts did not save the selected SIMD module.
The entry retains automatic dispatch, records the selected native module, and
rejects explicit dispatch overrides. It requires every regenerated truth NPZ
to match its frozen historical SHA. A mismatch stops the chain; changing CPU
dispatch and retrying or replacing the expected hash is not an approved repair.

```sh
python3.11 -m venv truth-env
truth-env/bin/python -m pip install -r artifact/original_execution/portable_truth/requirements.txt
truth-env/bin/python artifact/original_execution/portable_truth/run_truth.py check-native
truth-env/bin/python -m unittest discover -s artifact/original_execution/portable_truth -p test_truth.py -v
```

The tests use a tiny synthetic HDF5 with only `train`, check both metrics against
float64 reference calculations, and exercise rejection paths. Native tests are
Linux/Python3.11 only; other hosts skip them and cannot establish native success.
`check-native` hashes and imports the library; it performs no search.

## Explicit original-data command

First generate new prepared inputs using the sibling
[`portable_fresh_inputs`](../portable_fresh_inputs/README.md) entry. Use original
SHA-pinned datasets obtained through the public dataset instructions. Its new
completion receipt is accepted as a new receipt, never as the old prospective
firewall or independent audit. This command has not been executed on original
datasets during artifact delivery.

```sh
truth-env/bin/python artifact/original_execution/portable_truth/run_truth.py generate \
  --input-adapter artifact/original_execution/portable_fresh_inputs \
  --prepared /path/to/new-prepared-inputs \
  --dataset sift --source /path/to/sift-128-euclidean.hdf5 \
  --output /path/to/new-sift-truth \
  --outstanding-growth-bytes 268435456 --authorize-exact-truth
```

For Arxiv use `--dataset arxiv`, its registered source, and a separate new output.
The outstanding-growth argument must include all remaining project allocations,
not merely this stage if other work is pending. The historical plan requires
CPUs4–19, 16 library threads, AS24GiB, a128MiB single-file limit, CPU/wall7200s,
expectedRSS16GiB and256MiB stage growth. Project gates retain160GiB available
RAM,200GiB projected disk reserve and128GiB aggregate growth. Limits inherited
from the launcher are never relaxed. Resource snapshots and end-of-stage checks
are not a continuous RSS or aggregate-disk quota.

Outputs: four `{dataset}_{role}.npz` files, `start.json`, and either
`completed.json` or `failure.json`. Matching frozen truth bytes is required for
completion, including retained raw IDs and public scores. A separate float64
raw-vector calculation checks every returned score using the historical
tolerance; it does not independently repeat exhaustive global top-10 search.
New measured times
are regeneration records, not replacements for the paper's historical costs.
Partial outputs survive failures; no automatic resume, fallback or overwrite.

## Downstream boundary

This is not yet the complete profile chain. The historical profile script also
expects its historical independent truth audit, native replay binaries and sixteen graph
receipts. The new score-check receipt and those identities must be explicitly connected;
do not feed the new receipt into an archived launcher by deleting its gates.
The sibling cache entry can accept frozen evaluation truth bytes, but its
profile inputs still require their own original-execution integration.
