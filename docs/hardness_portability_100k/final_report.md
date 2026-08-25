# Query Hardness Is Not Portable — 100K final report

## Decision

`KEEP_BOUNDARY_STUDY_REALIZABILITY_GAP`

The phenomenon scales beyond the 10K mechanism fixture and persists under two non-LID, query-independent construction histories. The available frozen adaptive baselines and the single-prefix diagnostic do not establish a deployable method satisfying the Recall and net-cost gate, so this study supports a measurement/boundary claim rather than a completed adaptive algorithm.

## Protocol and data integrity

All three fixtures contain 100,000 base vectors and 1,000 independent scale-dev queries drawn from the frozen `train` member, with a seed-20260915 250/750 train-design/confirmatory split and exact top-10 truth. Queries have zero base and prior-query overlap. OCGT-v3 and earlier evidence were not modified or rerun. This phase accessed neither validation-dev nor formal-test.

Gate R passed for nine graph configurations with two deterministic repetitions: 216,000 physical rows / 108,000 unique query-ef cells, exact top-10/Recall/NDC/native-tracer agreement, exact repeated graph hashes, and no missing cells. The primary core contains 27 graphs and 324,000 rows; realistic histories add 18 graphs and 216,000 rows. Thus the confirmatory study contains 45 unique graph configurations and 540,000 primary rows, plus the Gate-R repetition evidence.

## 100K core results

| Dataset | Oracle headroom (95% CI) | Omega (95% CI) | Cross-order minus same-order regret (95% CI) | Rank-correlation drop | Core gate |
|---|---:|---:|---:|---:|---|
| Arxiv | 25.93% (23.70–28.02) | 0.270 (0.238–0.305) | 0.1127 (0.1063–0.1195) | 0.2426 | O/C/P pass |
| GloVe | 63.62% (61.17–66.08) | 0.100 (0.089–0.111) | 0.0342 (0.0322–0.0362) | 0.0842 | Oracle pass; C/P below threshold |
| SIFT | 33.12% (30.28–35.64) | 0.288 (0.255–0.323) | 0.1536 (0.1443–0.1632) | 0.2654 | O/C/P pass |

All three Oracle datasets pass. Arxiv and SIFT pass the robust Conditionality and Portability rules, satisfying the preregistered requirement of at least two datasets. GloVe is a useful boundary case: large Oracle headroom but weaker interaction and transfer effects, empirically illustrating that Oracle headroom, Omega, and migration regret are not equivalent.

## Realistic construction histories

After globally calibrating the transferred source budget, residual regret relative to random cross-seed transfer remains positive for all datasets and both histories:

| Dataset | Natural excess regret (95% CI) | Cluster-block excess regret (95% CI) |
|---|---:|---:|
| Arxiv | 0.1326 (0.1211–0.1451) | 0.1128 (0.1013–0.1252) |
| GloVe | 0.0643 (0.0561–0.0720) | 0.0320 (0.0252–0.0389) |
| SIFT | 0.1089 (0.0968–0.1217) | 0.0996 (0.0890–0.1099) |

The realistic-history Gate passes 3/3 datasets. The result is therefore not restricted to LID ascending/descending stress orders and is not removed by a single graph-wide multiplier.

## Baselines and realizability

Exact local LID is reproducible, while Relative Contrast/distance-gap is retained only as a static diagnostic because no frozen budget mapping exists. Steiner-hardness, Adaptive-ef, official SHEAF, DABS, DARTH, and Escape Hardness are marked `BASELINE_NOT_REPRODUCIBLE` under the allowed evidence because no author-code/pinned integration uniquely fixes a 100K run; the frozen OCGT-v3 SHEAF-like implementation remains a separate negative result with full `C16+C24+Cpred` cost.

The frozen logistic single-prefix diagnostic evaluates all 45 graphs. Mean Recall differences are −0.00050 Arxiv, −0.00013 GloVe, and −0.00195 SIFT; worst graph/history differences exceed the −0.001 safety margin. Without reuse, mean net gains are −150.4%, −5.34%, and −130.7%. Even an ideal full-reuse lower bound is only +1.19%, +16.05%, and +0.80%, is not positive for every Arxiv/SIFT graph, and is not an actual executable cost because the frozen tracer cannot serialize candidate/result queues and visited state. The candidate method Gate therefore fails and `REALIZABILITY_GAP_PERSISTS`.

## Scope

Supported claim: on these three frozen 100K fixtures, per-query sufficient HNSW budgets and their ordering depend materially on graph seed and construction history; source-index budgets remain lossy after global calibration, including natural and cluster-block histories. Unsupported claims: universal non-portability, superiority to unreproduced official baselines, production latency gains, or a completed adaptive algorithm. Formal-test remains sealed; 1M work may be planned but is not authorized as a hidden extension of this protocol.
