# S9-4 equal-information baselines, ablations, and failure attribution

Status: freeze before any S9-4 query-vector, truth, response, policy, or runtime access.

## Authorization and question

S9-3 passed its registered safety, real-runtime, tail, leave-one-target-out, and timing-stability gates on two fresh eight-build panels. S9-4 is therefore authorized. S9-4 asks whether the source-derived fixed-slack route contributes value beyond simpler policies under matched information, which components create that value, and which prior external-method results are genuinely comparable.

S9-4 is an explanatory paired experiment on the already frozen S9-3 indexes. It is not another independent build replication. The target build remains the outer statistical unit; source directions, queries, policies, and timing repetitions are nested.

## Frozen units and fresh roles

- Reuse the 16 S9-3 indexes without modification: eight SIFT-100K and eight Arxiv-Nomic-100K insertion-permutation builds.
- Reuse the native grid `(16, 32, 64, 128, 256, 512)`, endpoint 512, Recall@10 threshold 0.95, one thread, and the exact pinned DARTH/Faiss 1.8.0 binary.
- Freeze 1,500 previously unused source-HDF5 row IDs per dataset from `[850000, 1000000)`, after excluding every auditable prior role. Split into three disjoint 500-query roles: `baseline_selection`, `baseline_certification`, and `baseline_evaluation`.
- Only these roles may be accessed. Validation-dev, formal-test, and all reserved sealed roles remain forbidden.

## Comparison arms

All deployable arms use only registered native actions. Evaluation never changes an arm, threshold, fallback, or conclusion.

1. `B0_ENDPOINT_512`: certified fixed-safe endpoint; zero recovery complexity.
2. `B1_FIXED_256_CERTIFIED`: selection-free ef=256 plus independent 500-query candidate/endpoint certification. This is the strongest simple fixed-action control, not a post-hoc replacement for the S9-3 primary policy.
3. `B2_SOURCE_ONE_RUNG_CERTIFIED`: the frozen S9-3 source action, exactly one rung higher, followed by the new independent 500-query certification. This is the full fixed-slack route.
4. `B3_TARGET_GLOBAL_EQUAL_500`: first 250 `baseline_selection` queries select the smallest Bonferroni-qualified grid action; first 250 `baseline_certification` queries independently qualify that action and endpoint. Total target labels are 500, matching B2's 500 target-certification labels, while B2 additionally relies on amortized source-design evidence.
5. `B4_TARGET_GLOBAL_1000`: all 500 selection plus all 500 certification queries. This is a label-richer target-only upper comparator and is never called equal-information.
6. `A1_SOURCE_ACTION_DIRECT`: frozen source action without the one-rung shift or target certificate; diagnostic, nondeployable.
7. `A2_SOURCE_ONE_RUNG_UNCERTIFIED`: frozen one-rung candidate without target certification; diagnostic, nondeployable.
8. `A3_FIXED_256_UNCERTIFIED`: fixed 256 without target certification; diagnostic only.
9. `O1_EVALUATION_ORACLE`: lowest held-out action satisfying empirical risk at most 5%; nondeployable mechanism upper bound.

For every certified arm, candidate and endpoint use separate alpha allocations `0.025/0.025`. Selection uses one-sided Clopper--Pearson UCB with Bonferroni `0.05/6`. If the endpoint fails, abstain. If the candidate fails but endpoint passes, fall back to endpoint.

## Matched responses and runtime

Replay all six actions on every build for the three new roles, storing top-10 hashes, Recall@10, failure, and Faiss HNSW `n3` distance work. For the evaluation role, measure every unique action executed by B0--B4 on fixed logical CPU 2 using one thread, 50 warmups/action, seven seeded query-level interleaved repetitions, wall time and process-CPU time.

Native response hashes must be identical across repeated runtime searches. Timing validity retains the S9-2/S9-3 limits: median action-block CV at most 5% and maximum at most 10%.

## Primary estimands and gates

For each deployable arm and dataset report:

- candidate acceptance, fallback, abstention, and held-out risk;
- mean NDC and real wall-time gain relative to B0;
- query-pooled p95/p99 ratios;
- crossed target-build by query-ID 95% intervals with 5,000 replicates, seed 991;
- leave-one-target-out and deletion of the largest-benefit 1% of query IDs;
- target labels, amortized source labels, and whether the arm is selection-free.

A deployable arm passes only if both datasets have held-out risk at most 5%, wall-gain CI lower bound above zero, p95-ratio CI upper bound at most 1.05, positive leave-one-target-out wall gain, zero native mismatch, and valid timing. Comparisons among passing arms use the lexicographic order safety, p95, mean wall time, target-label count, then complexity. A simpler passing arm that is noninferior on safety/tail and no worse in mean wall time prevents a unique-method claim for B2.

## Component and failure attribution

The paired B0--B4/A1--A3/O1 table attributes:

- source-selection error: A1 versus O1;
- one-rung shift value: A2 versus A1;
- certification value: B2 versus A2 and B1 versus A3;
- fixed-action sufficiency: B1 versus B2;
- target-selection value and label allocation: B3/B4 versus B2;
- remaining oracle headroom: O1 versus the best deployable arm;
- fallback tax: candidate counterfactual versus executed certified arm.

These are paired descriptive/causal-mechanism contrasts within registered builds, not independent algorithm trials.

## External-method evidence integration

DARTH and Ada-ef are not silently ported onto incompatible Faiss units. S9-4 creates a locked evidence matrix from their official-code registered experiments, TCP results, and S9-3/S9-4 results, listing implementation, metric, label budget, safety event, outer unit, certification status, efficiency endpoint, and comparability. ConANN/ANNiE remain literature-only or `NOT_EXECUTABLE_FROM_AVAILABLE_CODE` unless an already frozen official executable and semantically matched result exists. No cross-implementation leaderboard is produced from unmatched estimands.

## Stop and interpretation rules

Stop on role overlap, input/hash drift, missing S9-3 index, endpoint-certification failure, native mismatch, timing instability, or any need to tune after response access. Preserve negative findings. S9-4 may conclude that ICBA remains valuable while the fixed-slack policy is unnecessary relative to a simpler certified baseline; that is a valid result and must not be hidden.
