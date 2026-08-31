# ICBA CIBS-Fixed Stage-I Phase 0 input and resource audit

- Audit time (UTC): `2026-08-31T13:08:54Z`
- Evidence level: `EXPLORATORY_FIXED_TARGET_STAGE_I`
- Phase status: `STOPPED_BEFORE_PHASE1`
- Primary blocker: `BLOCKED_MISSING_RECALL_TARGET`
- Secondary fallback status: `NO_VALID_FIXED_SAFE_FALLBACK`
- Final pilot label: not assigned; no Stage-I experiment was run.

## Frozen identity and isolation

- Requested frozen commit: `b0190169cdb758aa5311c7d13fbfd4fd724020f0`.
- Dedicated worktree: `/home/wlk/projects/navigation-aware-resistance-hnsw-cibs-stage1`.
- Dedicated branch: `exp/icba_cibs_fixed_stage1_pilot`.
- Audited HEAD: exactly the requested frozen commit.
- Ancestry check: pass.
- Tracked changes: none before this audit record.
- Untracked files: none before this audit record.
- Stage-I output directories/manifests: absent before this audit record.
- Git remotes: `origin` is the local frozen bundle; `github` is `git@github.com:edwards365/navigation-aware-resistance-hnsw.git`.
- Remote Stage-I branch: absent at audit time.

No existing file under `docs/results/manifests`, no theory-lock artifact, and no legacy result was modified.

## Frozen evidence integrity

- `results/icba_cibs_lock/checksums.sha256` contains 28 entries.
- `sha256sum -c results/icba_cibs_lock/checksums.sha256`: `28/28 OK`.
- Legacy restriction retained exactly: `LEGACY_BASELINE_CONDITIONAL_REPRODUCTION_111_OF_123`, sourced from `legacy_checksum_status=CONDITIONAL_111_OF_123` in `manifests/rebuild_portability_recovery_decision.json`.
- hnswlib submodule: `3f3429661187e4c24a490a0f148fc6bc89042b3d` (`v0.8.0`).
- Toolchain observed without compiling: GCC `9.4.0`, CMake `3.16.3`, Python `3.8.10`.
- CPU: 128 logical CPUs, AMD EPYC 7542; AVX/AVX2 available.
- GPU inventory: four RTX 3090 devices, each idle at the audit; GPU use remains prohibited for this pilot.

## Data, query, truth, and measurement firewall

- Frozen datasets named by the CIBS contract: SIFT-100K and Arxiv-Nomic-100K.
- Existing source HDF5 manifests record:
  - SIFT: `/home/wlk/projects/navigation-aware-resistance-hnsw/data/raw/sift-128-euclidean.hdf5`, 525,128,288 bytes, manifest SHA256 `dd6f0a6ed6b7ebb8934680f861a33ed01ff33991eaee4fd60914d854a0ca5984`.
  - Arxiv: `/home/wlk/projects/navigation-aware-resistance-hnsw/data/raw/arxiv-nomic-768-normalized.hdf5`, 4,135,431,488 bytes, manifest SHA256 `8be0993b978b0d0ef023d21d878251a5ed09e058adb25994553c08388d37d414`.
- The physical HDF5 files were not rehashed because the same container includes sealed query/truth arrays. Only existing manifests and filesystem metadata were read.
- No `cibs_sentinel`, `cibs_evaluation`, or `cibs_future_confirm` role manifest has been materialized.
- No Stage-I query IDs, vectors, truth, action results, or overlap matrix were read or generated.
- No validation-dev, formal-test, evaluation-reserved, future-confirm, or certification-reserved data was accessed.
- No graph was built, no source was compiled, and no query was executed.
- The inherited NDC implementation records exact query-to-index distance-function calls and requires native/instrumented top-k equality. Its pinned tracer must still pass the Stage-I equivalence tests before use.
- `ef` remains a requested raw control, not NDC or actual expansions. No monotonicity or right-censor success assumption was introduced.

## Runtime and resource audit

- Relevant Stage-I process count: zero.
- Open file descriptors under the dedicated worktree: none observed.
- Load averages: `0.28, 0.25, 0.19`.
- RAM: 270,282,723,328 bytes total; 256,482,873,344 bytes available; no swap.
- `/dev/shm`: 136,782,774,272 bytes available.
- Root/project filesystem: 13,681,238,016 bytes available.

Conservative projected additions use measured existing 100K index sizes:

| Component | Projected bytes |
|---|---:|
| Three Arxiv indexes at 322,059,640 bytes each | 966,178,920 |
| Three SIFT indexes at 66,059,640 bytes each | 198,178,920 |
| Maximum transient serialization copy | 322,059,640 |
| Query-action traces, logs, reports, tests, and figures | 1,073,741,824 |
| Query-role arrays, insertion orders, manifests, and build files | 268,435,456 |
| Additional contingency | 536,870,912 |
| Total projected additions | 3,365,465,672 |
| Mandatory reserve | 5,368,709,120 |
| Required free space | 8,734,174,792 |

The resource gate passes with 4,947,063,224 bytes of headroom over projected additions plus the mandatory 5 GiB reserve. This estimate assumes source HDF5 files are referenced in place and not copied. It must be recomputed immediately before any future build.

## Mandatory stop findings

1. `docs/icba_cibs_lock/cibs_fixed_algorithm.md` uses only the symbolic phrase `recall target tau`.
2. The complete frozen CIBS-specific contract, manifests, and result tables contain no numeric value for `tau`. The gate `Delta Recall@10 >= -0.001` is an evaluation non-inferiority gate, not the absolute per-query certification target.
3. Other historical project documents mention Recall@10 `0.90`, but the CIBS-Fixed contract does not explicitly inherit them. Using that value would silently repair the frozen contract after seeing the repository and is forbidden by the instruction `missing => BLOCKED_MISSING_RECALL_TARGET`.
4. The frozen CIBS-specific contract also requires a fixed-safe fallback but names no concrete build/ef artifact or independent safety basis. Until a pre-truth contract amendment supplies one, the fallback status is `NO_VALID_FIXED_SAFE_FALLBACK`.
5. The CIBS contract fixes `L=12` but does not enumerate the twelve raw `ef` values. Historical files consistently use `{10,16,24,32,48,64,96,128,192,256,384,512}`, but Stage-I has not adopted that grid.

Therefore Phase 1 was not started and no no-truth preregistration commit was created. The branch must remain stopped until an explicit pre-truth contract amendment supplies one numeric Recall target and a verifiable fixed-safe fallback; the raw-ef grid should be enumerated in the same amendment or subsequent no-truth preregistration.
