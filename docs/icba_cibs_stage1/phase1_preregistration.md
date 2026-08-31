# ICBA CIBS-Fixed Stage-I Phase 1 preregistration

Status: `PHASE1_PREREGISTERED_BEFORE_TRUTH_OR_ACTION_OUTCOMES`  
Evidence: `EXPLORATORY_FIXED_TARGET_STAGE_I`  
Contract amendment: `31ca05fcc40eb2ec1705f51fb0a66a9e95052f85`

This freeze is outcome-independent. It materializes train-side query vectors and IDs only; it reads no exact truth, sentinel/evaluation/future-confirm outcome, historical action-result table, validation-dev, formal-test, certification-reserved, or sealed HDF5 member.

## Frozen population and roles

The inferential object is a frozen finite pool sampled without replacement from each dataset's `train` member outside base IDs `0..99999`. Known historical query source IDs from Gate-A development, hardness-portability, Cross-Index G1, and rebuild-tax are excluded. The report is conditional on this frozen finite query pool and one registered build portfolio, not a superpopulation claim.

Per dataset, 1,032 new source IDs are split by master seed `20260831` and NumPy PCG64 into 32 `cibs_design`, 256 `cibs_sentinel`, 500 `cibs_evaluation`, and 244 `cibs_future_confirm` queries. Every ordered source-ID payload, vector artifact, source, normalization rule, historical overlap, pairwise overlap, and access state is hashed in `manifests/icba_cibs_stage1_query_roles.json`. All pairwise source-ID overlaps must be zero. Design is only for fallback/instrumentation gates; sentinel opens only after build/fallback gates; evaluation opens only after the selected-action manifest is frozen; future-confirm never opens in Stage I.

## Frozen builds and actions

The portfolio is `K=3`: G1/G2/G3 use hnswlib v0.8.0 with build seeds `1009/1013/1019` and independently frozen 100K insertion orders from PCG64 seeds `2026083101/2026083102/2026083103`. All use squared L2, `M=16`, `efConstruction=100`, `k=10`, one build/query thread, GCC 9.4.0, C++17, `-O3 -DNDEBUG -DNO_MANUAL_VECTORIZATION -Wall -Wextra -Wpedantic`, and scalar distance evaluation. Failed builds are retained as failures and never replaced. Artifact hashes and resource measurements must be frozen in a build-realization manifest before sentinel access.

The raw grid is exactly `{10,16,24,32,48,64,96,128,192,256,384,512}`. Each of 36 actions is charged separately. Requested `ef`, exact NDC, actual expansions, wall-clock, raw Recall@10, endpoint, and `Z_abs` remain distinct fields. No recall monotonicity, envelope, interpolation, or right-censor success assumption is allowed.

## Certificate and selection

For each action and sentinel query, `Z_abs=1` when Recall@10 is below 0.90, the endpoint is infeasible, or execution fails. A one-sided exact Clopper-Pearson UCB at `alpha/M = .05/36` certifies only when UCB is at most `.05`. With `n=256`, at most three failures certify; a fourth forbids certification. The selected action minimizes sentinel mean NDC within the certified set, breaking ties by p95 NDC, raw `ef`, then build ID. An empty set invokes the already registered G1/`ef=100000` fallback only after all fallback gates pass.

The main baselines are B0 fixed-safe fallback, B1 G1-only fair certification at `alpha/12`, B2 registered G1/`ef=512`, B3 one frozen random build/`ef=512`, B4 CIBS-Fixed, and B5 the nondeployable post-hoc all-36 per-query oracle. Evaluation cannot reselect. Sentinel output is a `PROCEDURE_CERTIFICATE`; evaluation is a `HELD_OUT_RISK_DIAGNOSTIC`.

Paired-query bootstrap uses 5,000 replicates and seed 991. All primary/tail/cost/robustness fields, two truth-cost channels, workload sizes, minimum gates, promotion gates, and at least 24 machine checks are frozen in the machine preregistration. The K=2/L=12/n=128/M=24 zero-failure ablation may run only after the main K=3 analysis completes and cannot replace it.

Free space is recomputed before every build and must cover projected additions plus 5 GiB. Any firewall, resource, fallback, native/tracer, exact-top-k, CP, completeness, checksum, or replay failure stops the pilot under the corresponding registered failure state.
