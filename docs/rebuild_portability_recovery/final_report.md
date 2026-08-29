# GRAPH-ANNS rebuild portability recovery Fast Gate

## Scope and evidence status

This is design-stage recovery feasibility on the frozen hnswlib SIFT-100K and Arxiv-Nomic-100K evidence, nine builds per dataset, 12 budget levels, master seed 991, and mutually exclusive sentinel/evaluation queries. It is not an outer-build certificate or confirmatory result. The conditional input audit verified the current 59-file Full Seal output set and recorded the inherited legacy mismatch (111/123 matches, eight derived CSV mismatches, four absent bytecode artifacts).

## Results

- Source policy: 18/18 independent source calibration gates passed using the fixed L2 logistic specification and permitted first-prefix fields.
- M0 Frozen Transfer: 144/144 directed pairs passed Gate S in this restricted design replay; savings ranged from zero to about 51%, with 16 SIFT directions at no more than 1% gain.
- M1 Target-Only: 144/144 passed at each \(k=32,64,128,256\); median saving was about 39.9% and did not materially vary with \(k\) in the frozen replay.
- M2 Historical: pass counts were 99/144, 102/144, 141/144, and 144/144 for \(k=32,64,128,256\). At \(k=256\), median saving was 56.3% on Arxiv and 58.5% on SIFT; minimum saving was 46.8% and 41.0% respectively.
- M3 Fingerprint-Gated: pass counts were 100/144, 103/144, 141/144, and 144/144. At \(k=256\), median saving was 50.6% on Arxiv and 58.3% on SIFT, but unsupported directions could fall back to zero gain.
- Same-history: 36/36 cross-seed directions passed. Top-1% deletion preserved safety in 144/144 M0 directions; positive gain remained in 72/72 Arxiv and 56/72 SIFT directions.

## Unified Gates

Gate S passes for M1 at every preregistered \(k\), and for M2/M3 only uniformly at \(k=256\). Gate B is `DESIGN_STAGE_BUILD_EVIDENCE` only: nine builds cannot establish a 5% outer-build guarantee. Gate V1 fails because M2/M3 do not reduce target truth by 50% relative to already-safe M1. Under free truth, M2's median break-even workload versus fixed-safe is about 458 on Arxiv and 437 on SIFT, with every direction below 1,000. Gate V2 is nevertheless `NOT_ESTIMABLE` because truth acquisition, certificate computation, and per-rebuild full-retraining costs were not measured. Gate V3 is not the primary value mode because M1 already accepts safely and M3 fallback does not establish additional unsafe-transfer detection value.

## Theory

R1 is a restricted fixed-target consequence of exchangeable one-sided residual calibration and certified monotone endpoints. R2 is a conditional support-gated proposition: accepted targets require an assumed local residual domination condition, while rejected targets inherit fixed-safe fallback safety. Neither result converts the nine-build replay into open-world outer-risk certification.

## Decision

`TARGET_ONLY_RECALIBRATION_SUFFICIENT_NO_NEW_METHOD`

M1 already solves the restricted design-stage query-safety problem. M2 offers an interesting efficiency hypothesis at \(k=256\), but it does not reduce truth and cannot pass the strict amortized-cost comparison with full retraining while key costs remain unmeasured. Formal implementation authorization is therefore withheld. Future work should preregister measured truth/retraining costs and acquire enough independent build environments before reconsidering M2.

## Firewall and resources

No validation-dev or formal-test access, no new index or graph construction, no GPU, no complex model search, and no post-hoc method/feature/threshold expansion occurred. Preserved `logs/rcrs_signal` remained untracked and untouched.
