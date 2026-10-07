# Simple fixed-budget and target-calibrated baseline entry

This entry exposes the frozen retrospective simple-baseline arithmetic with a
separate calibration lock and final evaluation. It runs no ANN search, timing,
bootstrap, training, or historical auditor. The historical analysis remains a
retrospective comparison; the new execution separation does not change that status.

## Inputs and rules

Use the new `portable_arrays` completion directories for both datasets. Every
receipt must identify its dataset and role and every NPZ must match its frozen
SHA and size. Eight builds and all eleven budgets retain their registered order.

* TG500 uses the first 250 selection queries and first 250 qualification queries.
* TG1000 uses all 500 selection and all 500 qualification queries. TG500 is a
  nested subset, not a different draw.
* Selection tests raw failure (`hits < 10`) with CP error `0.05/11`. Among eligible
  actions it minimizes mean selection NDC, with grid order breaking ties. If none
  pass, the candidate is the endpoint. No monotonic-cost assumption is added.
* Candidate and endpoint qualification each use raw failure and CP error 0.025.
  An ineligible endpoint makes the target undeployable; otherwise use a qualifying
  candidate or fall back to the endpoint.
* Fixed-1600 always proposes grid index 9, uses 500 qualification queries, and has
  zero selection cost in the historical record. The unchanged function also emits
  descriptive `eligible_actions` from the selection array; that metadata does not
  choose or modify its candidate.
* Endpoint-2400 is an unqualified reference, not a deployment certificate.

The extracted `cp` and `simple_decision` functions are unchanged. The lock checks
all 64 method/target semantic records against `expected_decisions.json`; integer,
action, role-count and decision fields are exact, floating CP values use absolute
tolerance 1e-12. A mismatch stops dependent work; expected values are not repinned.

## Run

Install the two pinned Python dependencies in Linux Python 3.11. Sibling adapters
`portable_fresh_inputs` and `portable_policy` must have their pinned source bytes.
Use fresh output paths on a volume satisfying the declared RAM/disk gates. The
commands below are an executable handoff for a new reproduction, not instructions
to rerun an already sealed project experiment.

```sh
python -m pip install -r artifact/original_execution/portable_baselines/requirements.txt
python artifact/original_execution/portable_baselines/run_baselines.py lock \
  --input-adapter artifact/original_execution/portable_fresh_inputs \
  --policy-adapter artifact/original_execution/portable_policy \
  --sift-selection /path/to/new-sift-selection-array \
  --arxiv-selection /path/to/new-arxiv-selection-array \
  --sift-qualification /path/to/new-sift-qualification-array \
  --arxiv-qualification /path/to/new-arxiv-qualification-array \
  --output /path/to/new-baseline-lock \
  --outstanding-growth-bytes 16777216 --authorize-baseline-stage

python artifact/original_execution/portable_baselines/run_baselines.py evaluate \
  --input-adapter artifact/original_execution/portable_fresh_inputs \
  --policy-adapter artifact/original_execution/portable_policy \
  --lock /path/to/new-baseline-lock --lock-sha256 SHA256_OF_COMPLETED_JSON \
  --sift-evaluation /path/to/new-sift-evaluation-array \
  --arxiv-evaluation /path/to/new-arxiv-evaluation-array \
  --output /path/to/new-baseline-evaluation \
  --outstanding-growth-bytes 16777216 --authorize-baseline-stage
```

The lock phase cannot accept evaluation inputs. Evaluation verifies the prior
lock SHA and semantic records before opening evaluation arrays, cannot accept
selection/qualification inputs, and does not revisit choices. Undeployable targets
have null metrics, not endpoint or index-zero proxy results. Evaluation reports
raw failures and mean NDC. API times and paired confidence intervals belong to
their separately delivered measurement and saved-output analysis paths.

Each stage uses CPU 2, one numerical-library thread, AS 4 GiB, file cap 16 MiB,
CPU/wall cap 600 seconds, expected RSS 1 GiB, and 16 MiB output growth. Existing
200 GiB projected free-space and 128 GiB outstanding-growth gates remain active.
The supplied outstanding-growth value must cover all other remaining concurrent
project work as well as this stage; increase the example where necessary.

## Verification boundary

```sh
python -m unittest discover -s artifact/original_execution/portable_baselines -p 'test_*.py' -v
```

Tests use synthetic arrays only. They cover CP endpoints, minimum NDC and tie
breaking, nested roles, all deployment branches, role overlap, raw evaluation,
undeployable handling, identity checks and lock-before-read structure. Full original
arrays are not executed by these tests. A passed synthetic suite is not a new
measurement, full reproduction, or new statistical guarantee.
