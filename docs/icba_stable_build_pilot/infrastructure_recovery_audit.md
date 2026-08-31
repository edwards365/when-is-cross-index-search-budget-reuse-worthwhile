# Infrastructure Recovery Audit

Recovery basis: commit `5422868a624fc59d36c724250011611c3dfd8d20`.

The earlier `INSUFFICIENT_STORAGE_FOR_REPRODUCIBLE_PILOT` decision was an infrastructure stop and produced no evidence for or against Stable-by-Construction. Theory and method authorization remain unchanged.

## Before and after

- Initial root free space: 5,780,381,696 bytes.
- Final root free space: 16,132,358,144 bytes (15.024 GiB).
- Mandatory root reserve: 5 GiB.
- Post-reserve experiment headroom: 10,763,649,024 bytes (10.024 GiB).
- Recovery Gate: `PASS_MINIMUM_10_GIB_HEADROOM`.

## Safe actions

- Converted 13 completed or tracked-clean historical Git worktrees to reversible sparse checkouts. Branches, commits, remote refs, and all untracked artifacts were retained.
- Ran ordinary `git gc` on the shared repository; no aggressive prune was used.
- Removed two inactive, regenerable VS Code Server payload caches plus inactive launcher binaries after process/open-file checks.
- Removed the inactive VS Code extension cache after recording its version inventory; no extension host had files open.
- Removed only `.deps/cross_index_g1`, an inactive regenerable Faiss/DiskANN Python dependency directory. The separate DiskANN source tree with four local modifications was explicitly retained.
- Cleared Conda package-cache paths only after exporting explicit environment specifications and proving there were no symlinks into the cache. Both base Conda and the experiment environment passed post-clean verification.
- Removed an inactive 88 MiB Codex temporary plugin cache after an open-file/process audit.

## Explicitly preserved

- All historical experiment results, frozen checksums/manifests, logs, indexes, base datasets and query/truth inputs.
- The main 1.8 GiB experiment environment and current Conda installation.
- Dirty/untracked artifacts in historical worktrees.
- Modified DiskANN source files.
- Current VS Code agent processes and Codex sessions/plugins.

The resumed pilot must re-run Phase 0 and maintain the rule `free >= projected_remaining_additions + 5 GiB` before every build phase. The present capacity authorizes the SIFT smoke and minimum pilot path, not an unconditional two-dataset run; Arxiv remains conditional on both scientific and storage Gates.
