# ICBA Auditor Runtime Alignment — Phase 0 Audit

Evidence status: `RETROSPECTIVE_DEVELOPMENT_ONLY`.

The frozen starting point is `69d4b2aa89625be2e96fa0ff184af5378959dcfb` on branch `exp/icba_auditor_runtime_alignment_repair`. The requested theory-alignment object `0004ad9916ad4dc0efce915789eac9bafa352f02` is not present in the mounted repository, so its status is exactly `ALIGNMENT_COMMIT_NOT_MOUNTED_REQUIREMENTS_RECONSTRUCTED_FROM_AUDIT`; no merge is claimed.

The prior runtime output is machine-readable but cannot support method closure. Its implementation uses historical 500-query records, treats the next native ef as a fixed-safe fallback, hard-codes endpoint and right-censoring false, constructs per-query action decisions using outcome-derived risk, sets decision regret to zero by construction, and computes p95/p99 after aggregation rather than from per-query cost vectors. The frozen manifest also records that the source policy was not serialized and full-retraining cost is `NOT_ESTIMABLE`.

Accordingly, the following prior claims are withdrawn as evidence while their files remain immutable:

- A5/A6 decisions produced from per-query outcome truth;
- constant-zero regret;
- aggregated-mean p95/p99;
- next-ef as certified fixed-safe fallback;
- hard-coded feasible endpoint/censoring;
- historical queries as independent certification;
- action-family inference without multiplicity correction.

Resource audit at start: approximately 18 GiB free on `/`, 238 GiB available RAM, and no active ANN experiment. One stale self-matching CALS watcher was terminated without reaching its deferred hash/read step. Existing unrelated untracked directories were preserved without modification.

Input status:

| Requirement | Status |
|---|---|
| Raw hit/Recall proxy | PRESENT (`base_hits`, `union_hits`) |
| Per-query NDC components | PRESENT |
| Complete 12-level budget grid | NOT_ESTIMABLE from prior auditor output |
| Endpoint/right-censor evidence | NOT_ESTIMABLE (prior values hard-coded) |
| Wall-clock vector and full cost | NOT_ESTIMABLE |
| Serialized source policy | ABSENT |
| Independent four-way query roles | NOT_ESTIMABLE / prior role gate failed |
| Future-confirm access | NOT ACCESSED |
| validation-dev/formal-test access | NOT ACCESSED |

The runtime repair therefore proceeds only through code-level P1–P7 alignment and its 24 tests. It may not access new outcomes until those tests pass. The legacy statement remains unchanged: `LEGACY_BASELINE_CONDITIONALLY_REPRODUCED: 111/123 matched, 8 mismatched, 4 untracked __pycache__ entries`.
