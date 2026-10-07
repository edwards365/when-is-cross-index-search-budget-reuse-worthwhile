# Standalone historical E2 cache measurement entry

This directory extracts the static answer-cache measurement from the frozen
multi-stage campaign. It does not run E0/E1/E3, ANN search, a model, or the old
campaign entry point. The source supplement remains available at
[artifact-sources-v1](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-sources-v1).

## What is preserved

`historical_cache.py` retains the original complete-key concatenation, Python
bytes dictionary lookup, resident-object accounting, static capacities
0/100/500/1000, visits 1/2/10/50/100, cyclic/shuffled sequences, seed 991,
seven repetitions, 100-query warmup and both timing loops. `provenance.json`
lists the exact I/O substitutions and unchanged function hashes. The removed
`final.json` read assigned an unused variable. The full response array remains
loaded during measurement, including its original memory-footprint context.

Input checks replace the old whole-campaign E0 prerequisite, not its scientific
outputs: seven files must match frozen SHA256/size; query bytes, membership,
truth and profile query order and shapes are validated. No checksum is disabled
or silently recomputed for a different input. Historical result CSVs and timing
values are never overwritten. New timings, if explicitly run by a reproducer,
are new host measurements and are not expected to equal the paper numerically.

## Environment and non-measuring validation

The measurement path requires Linux, Python 3.11 and NumPy 1.26.4. Input checks
and synthetic tests also work on Python 3.12. No native ANN library is needed.
Create a new environment of your choice, then:

```sh
python -m pip install -r requirements.txt
python -m unittest -v test_cache_stage
python cache_stage.py check --input-root /path/to/prepared-inputs
```

`check` only reads and validates; it does not write results or call the timer.
The tests use synthetic arrays and never invoke the historical E2 measurement.

## Required inputs and upstream boundary

Keep the relative paths specified in `inputs.json` below a selected input root:

- `tcp_fresh_roles_v1/membership.npz`;
- `tcp_fresh_profiles_v1/{sift,arxiv}_target_evaluation/queries.qbin`;
- `tcp_fresh_truth_v1/{sift,arxiv}_target_evaluation.npz`;
- `tcp_fresh_profiles_v1_ops/audited_arrays/{sift,arxiv}_target_evaluation.npz`.

Membership and audited response arrays are covered by the previously published
saved-response material. Query vectors and exact-truth inputs are **not bundled
here**. Obtain vectors under the original data provider's terms and use the
fresh-query preparation/true-answer pipeline in the source supplement. That
upstream pipeline is still being made portable; this entry does not close it.
It accepts the frozen prepared files, not arbitrary newly compressed NPZs with
different identities. `inputs.json` supplies all seven expected identities.

## New measurement command (not executed during delivery)

Run only with authorization for a new measurement, in a fresh output directory:

```sh
python cache_stage.py measure --input-root /path/to/prepared-inputs \
  --output /path/to/new-cache-measurement --authorize-new-timing \
  --outstanding-growth-bytes 805306368
```

The last value is the historical stage growth (768 MiB); use the **total**
remaining project growth including concurrent work if larger. The 128 GiB
aggregate ceiling and 200 GiB projected free-space floor remain enforced.
The historical resource preflight requires at least 160 GiB available RAM,
its RSS/64 GiB reserve check, I/O wait below 15%, and available logical CPU 4.
Measurement pins the process to CPU 4, sets libraries to one thread, applies
the original 4 GiB address-space, 128 MiB per-file and 1800s CPU/wall limits
(retaining stricter inherited limits), and checks final thread affinity.
The directory must not exist or overlap inputs. Failures retain their evidence;
there is no automatic retry. These are the recorded project's conservative
resource conditions, not minimum cache-algorithm requirements or a promise of
machine isolation. The wrapper does not install dependencies or acquire data.

Outputs are the original summary/memory/raw-block/correctness CSV/JSON and
per-call NPZs under `records/`, plus wrapper `start.json` and `completed.json`
or `failure.json`. A completed function is not substituted for an observed
external process exit. The caller should retain the command's real exit status.

## Interpretation

Batch timing includes full-key construction and lookup of preloaded exact
answers. It excludes insertion, transport, parsing, misses requiring acquisition,
and a full serving stack. Full capacity and intermediate static capacities do
not implement an adaptive cache. Cost ledgers and Figure 6 continue to use the
historical saved measurements, not the adapter tests.

Current verification is recorded in `validation.json`. Standalone input wiring
is tested; no new cache performance run or upstream ANN execution is claimed.
