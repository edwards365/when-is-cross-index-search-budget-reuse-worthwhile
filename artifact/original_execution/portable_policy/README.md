# Frozen History-Max qualification and evaluation entry

This entry connects **new** array-materialization receipts to the original
History-Max arithmetic. It does not select new policies, change risk rules,
run ANN, repeat old audits, or regenerate old analysis outputs during delivery.
TG/fixed-budget decisions and API timing remain separate interfaces.

`historical_policy.py` contains the unchanged original loading/label functions
and the certification/evaluation loops, placed in functions with caller-supplied
paths. The source, policy, arrays and extracted core are hash pinned. Original
target names and event definitions are preserved. `TCP` is the original field
name for History-Max; it is not a newly introduced method.

## Two explicit phases

Install `requirements.txt` in Linux Python 3.11, then test the interface:

```sh
python -m unittest discover -s artifact/original_execution/portable_policy -p test_policy.py -v
```

The tests generate small synthetic response arrays, including endpoint failure,
fallback, no-finite-tail and candidate/endpoint event disagreement. They never
read original benchmark arrays. To reproduce a stage with original inputs:

```sh
python artifact/original_execution/portable_policy/run_policy.py certify \
  --input-adapter artifact/original_execution/portable_fresh_inputs \
  --sift-array-root /path/to/new-sift-cert-array \
  --arxiv-array-root /path/to/new-arxiv-cert-array \
  --output /path/to/new-policy-lock --outstanding-growth-bytes 16777216 \
  --authorize-policy-stage
```

Inspect and fix the new `completed.json` identity in the evaluation invocation:

```sh
sha256sum /path/to/new-policy-lock/completed.json
python artifact/original_execution/portable_policy/run_policy.py evaluate \
  --input-adapter artifact/original_execution/portable_fresh_inputs \
  --sift-array-root /path/to/new-sift-evaluation-array \
  --arxiv-array-root /path/to/new-arxiv-evaluation-array \
  --lock /path/to/new-policy-lock --lock-sha256 NEW_LOCK_SHA256 \
  --output /path/to/new-policy-evaluation --outstanding-growth-bytes 16777216 \
  --authorize-policy-stage
```

Declare the full outstanding growth when other stages remain, not merely the
16 MiB minimum shown. Each output must be absent. CPU2/library threads1,
AS4GiB, file16MiB, CPU/wall600s, expectedRSS1GiB, original RAM/disk gates apply.
The lock SHA and policy identity are verified **before** either evaluation
array or its receipt is opened. Certification has no evaluation-input argument.

## Identity and interpretation

- New certification rows must match all 16 frozen reference rows: categorical
  and integer fields exactly, finite floats within absolute 1e-12. A mismatch
  stops dependent work; it never overwrites the expected rows or permits tuning.
- Receipts and operational elapsed time are new, not historical certification,
  old audit PASS, prospective-first-use evidence, or a replacement timing ledger.
- The original `cert_tcp_failures` and `eval_tcp_candidate_failures` fields count
  **candidate-or-endpoint union**, not necessarily raw candidate failures. Their
  equality for the historical History-Max evaluation is not a general identity.
- The original calculation checks endpoint eligibility, then candidate union
  eligibility. No simultaneous all-target or future per-query guarantee is added.
- Original evaluation code contains an endpoint proxy for an undeployable row.
  The wrapper rejects such evaluation: this fixed panel's reference lock contains
  only TCP/ENDPOINT decisions. It does not relabel an undeployable case as service.
- Full original-array execution has not been run for this delivery. Saved-output
  reproduction is already provided elsewhere; this is the new upstream interface.
