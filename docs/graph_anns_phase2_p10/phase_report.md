# Phase P10 report — 10M-scale real-data cell (user-authorized)

## Goal
Close the final scale gap (R_B/R_A 7-point condition): a >=10M real-data cell answering
whether the phenomenon and the pooling boundary extend an order of magnitude beyond 1M.

## Step 1 — gates (all passed)
- Authorization recorded (user, 2026-09-12).
- Data source located: ann-benchmarks deep-image-96-angular.hdf5 (HTTP 200 direct,
  3,848,008,288 bytes; 18.5 MB/s measured). REAL deep-image embeddings, 9,990,000 x 96,
  angular/cosine space, 10K queries with top-100 truth.
- Resources: RAM 235GB available (index+base ~9GB in memory); disk 15GB free with the
  preregistered delete-as-you-go storage protocol.
- Preregistration COMMITTED BEFORE any download/build/search (git: "[Phase P10]
  preregistration frozen...").

## Step 2 — execution (running)
- run_10m.py: resumable per-build CSV; 8 builds (4 seeds x 2 orders) + 2 identity builds;
  single-threaded M=16 efC=100; registered grid 10..200; 500 eval queries seed 991;
  h=10 event vs provided truth; sanity gate hits@ef200 > 8.5; forensics gate PASSED
  (query/base raw overlap = 0); stop rule on free disk < 3GB.
- Two launch defects fixed en route (hnswlib space name angular->cosine; a broken
  relaunch compound command) — code-only, no data touched.
- Expected wall: ~35-60 min/build -> completion overnight; analysis (preregistered
  metrics: variation, incremental risk + CI, h-sensitivity, pooling k-curve, identity)
  runs after all 8 builds finish per the blinding rule.
