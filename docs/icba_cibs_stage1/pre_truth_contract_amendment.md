# ICBA CIBS-Fixed Stage-I pre-truth contract amendment

- Status: `PRE_TRUTH_CONTRACT_AMENDMENT_FROZEN`
- Evidence level: `EXPLORATORY_FIXED_TARGET_STAGE_I`
- Scope: execution-enabling repair only; this amendment is not CIBS-positive evidence.
- Amendment time: frozen before any Stage-I sentinel/evaluation/future-confirm truth or action outcome is read.
- Frozen base remains `b0190169cdb758aa5311c7d13fbfd4fd724020f0`; this additive record does not modify any frozen file or historical result.

## Outcome-independent provenance

The quality target is fixed as `tau = Recall@10 >= 0.90`. This value comes from the unified ICBA definition lock (`docs/icba_theory_lock/definition_lock.md`, SHA256 `b3a0c85e2a1f2bfacdd24883bfdd74f09516a1921a6a0ee25c80b3e2f6420809`) and the previously preregistered 100K protocol (`docs/hardness_portability_100k/preregistered_protocol.md`, SHA256 `6b23bc41753a8ebf17c6a1f8acb4b32d24b54f693befb1ea495106560e292409`). It was not selected from Stage-I outcomes.

The raw fixed-`ef` grid is exactly `{10,16,24,32,48,64,96,128,192,256,384,512}`. It comes from the same frozen 100K protocol and its machine preregistration (`manifests/hardness_portability_100k/preregistration.json`, SHA256 `0b4706003bc9caa024be12c15b27d8854f2e6b3dc347df1fe547c2f60a1aeb87`). No interpolation, envelope, monotonicity assumption, or post-outcome extension is permitted.

## Fixed-safe fallback

For each dataset, the fallback is preregistered as the first candidate build `G1` searched with raw `ef = 100000`, equal to the frozen base cardinality. It is an external fixed fallback action, not one of the 36 certification actions and not an empirically guessed "safe ef". It is triggered only when the simultaneous certified set is empty. Its endpoint is native hnswlib top-10 with no filter.

The safety argument is implementation-specific to hnswlib v0.8.0, commit `3f3429661187e4c24a490a0f148fc6bc89042b3d`, whose `hnswalg.h` SHA256 is `0fb2c1b1d3aae1ea959b536f96844f3f3ae6a2f32ce063f2c31f93d84a7e5c32`. In `searchBaseLayerST`, while fewer than `ef` points have been retained, every newly discovered neighbor is admitted. With `ef >= current_count`, `top_candidates` cannot reach `ef` before every element is discovered, so capacity cannot cause early stopping or pruning. On a deletion-free, filter-free index whose every node is directed-reachable at layer 0 from the entry point, the traversal therefore visits the entire dataset. Native top-10 is then the exact top-10 of all 100,000 elements (subject to the frozen deterministic distance/label tie rule).

This argument is usable only after all of the following per-dataset checks pass on the actual `G1` artifact:

1. `current_count == max_elements == 100000` and all expected labels occur exactly once;
2. `num_deleted == 0`, no filter, no stop condition, and native `knn_query(k=10)` is used;
3. a directed layer-0 traversal from the saved entry point visits exactly 100,000 nodes;
4. the ordered traversal serialization and its SHA256 connectivity hash are recorded;
5. independent design-side queries give identical native and brute-force exact top-10 labels/distances under the frozen tie rule;
6. save/load replay preserves index SHA, structural facts, connectivity hash, native top-10, and exact top-10 equivalence;
7. synthetic connected and deliberately disconnected graph tests demonstrate respectively full enumeration and fail-closed rejection.

Any count, label, deletion, filter, connectivity, exact-top-k, native/tracer equivalence, or replay failure yields `NO_VALID_FIXED_SAFE_FALLBACK` and stops the pilot before sentinel access. Historical outcomes may not repair a failed fallback.

## Cost and decision accounting

Every fallback invocation is charged its observed full-enumeration NDC, actual expansions, requested `ef=100000`, and wall-clock time. These observations enter mean, p50, p95, p99, total offline cost, both truth-cost channels, storage/serialization cost, and finite workload break-even. If full enumeration makes the tail or cost gate fail, the registered gate fails; fallback `ef` may not be lowered.

Before every build, free space must remain at least projected additions plus 5 GiB. The amendment does not authorize validation-dev, formal-test, certification-reserved, evaluation-reserved, future-confirm, GloVe, GPU search, result-driven tuning, open-world/confirmatory/SOTA claims, or CIBS-Race. Phase 1 may start only after this amendment and its outcome-independent tests are committed and pushed.
