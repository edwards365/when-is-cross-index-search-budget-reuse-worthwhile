# Phase 0 audit

- Frozen parent: `exp/icba_bn_apd_observable_trigger_gate@5ece422`.
- Work remained in the existing ANNS main worktree; pre-existing untracked directories were not touched.
- Root free space was approximately 18 GiB; no relevant active experiment process was found.
- 12,000 trace rows, 9,000 joined rows, eight trigger-rule rows, parent manifest, and checksums were present.
- `__pycache__` directories exist in the environment, but are ignored and excluded from the new checksum; no source or historical CSV was deleted.
- Sealed validation-dev, formal-test, certification, evaluation, and future-confirm roles were not accessed.
