# Phase 5 prospective fresh-query/new-build confirmation

Frozen before generating any Phase 5 query truth, target index, or search
result. Parent method commit: `6c8ea7f9be17a2eaabe0a4f87840f64faea5a743`.

## Inputs and untouched query rows

The source HDF5 files are already on data500 and are read-only inputs:

- SIFT: `data/raw/sift-128-euclidean.hdf5`, SHA-256
  `dd6f0a6ed6b7ebb8934680f861a33ed01ff33991eaee4fd60914d854a0ca5984`;
  old TCP/DARTH roles end at train row 994000. Phase 5 certification is
  `[994000,994500)` and evaluation is `[994500,995500)`.
- Arxiv-Nomic: `data/raw/arxiv-nomic-768-normalized.hdf5`, SHA-256
  `8be0993b978b0d0ef023d21d878251a5ed09e058adb25994553c08388d37d414`;
  old roles end at train row 103500. Phase 5 certification is
  `[103500,104000)` and evaluation is `[104000,105000)`.

The new rows are disjoint from every role in the frozen adapter ledgers. They
are chosen by contiguous ID ranges before any Phase 5 outcome is computed.
Only these rows and the base rows `[0,100000)` may be read. Existing
validation, certification, testing, validation-dev, and formal-test outcomes
are not inputs to this confirmation.

## Builds and method

- Frozen historical source builds for TCP: the first nine seeds in the prior
  order, `1103,1229,1361,1499,1621,1747,1877,1999,2131`.
- Prospective target insertion-order seeds: `2381,2503,2633`.
- Base snapshot, M=16, efConstruction=100, CPU implementation, metric, and
  actual efSearch grid `10,20,40,80,120,160,200` remain unchanged.
- Canonical TCP-HM9-TC and its stable-tail/BOT semantics are unchanged.
- Deployment order is TCP-HM9-TC, source-only global fixed ef, fixed-safe
  ef=200. All three policies use one-sided CP bounds at confidence
  `1-0.05/3` on the 500 fresh certification queries.

## Baselines and label fairness

- fixed endpoint ef=200;
- source-only global fixed ef selected on the nine historical source builds;
- target-only global fixed ef, using certification qid 0--249 for selection
  and qid 250--499 for independent certification;
- frozen official DARTH model, audited through the same safety/fallback rule;
- deterministic rebuild is represented by the same frozen insertion order and
  global fixed policy, without target adaptation.

TCP and source-only fixed use zero target-selection labels and all 500 target
labels for certification. Target-only uses 250+250. Evaluation contains 1000
fresh rows and cannot affect any policy, threshold, fallback, or hyperparameter.

## Gates and stopping

Per dataset, report all three target builds and the pooled result. Safety
requires selected-policy simultaneous UCB <=0.05 on every target build and
evaluation Recall@10 difference >=-0.001. Efficiency requires at least 5%
mean distance-computation reduction versus the best deployable baseline,
paired query/bootstrap interval below zero, and query-pooled p95 ratio <=1.05.
p99 is mandatory diagnostic. All leave-one-target-build-out directions must
remain favorable. Three new target builds are prospective pilot evidence, not
a precise outer-build population certificate.

If adapter hashes, role disjointness, native ef semantics, target index replay,
or endpoint certification fails, stop without interpreting method efficacy.
No result-dependent threshold, query range, build seed, source subset, policy
order, or baseline may be changed.

Large generated adapters, indexes, logs, and per-query outputs go only under
`/home/wlk/data500/tcp_sigmod_regular_closure/phase5_prospective_v1`.
