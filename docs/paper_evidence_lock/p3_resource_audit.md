# P3 resource audit

## Scope

This is a resource-preparation audit for the existing Graph-ANNS main worktree. It does not access `confirmatory_query` or `future_replication`, and it does not start a build or ANN search. The overall P3 gate therefore remains conditional until a preregistered pilot supplies wall-clock measurements.

## Storage envelope

- Root filesystem free space at audit: 17.17 GiB. It is not an acceptable location for the confirmatory matrix.
- `/home/wlk/data500` free space at audit: 902.66 GiB.
- Historical Gate-A artifacts: 16,346,353,993 bytes over 113 completed runs, or 0.1347 GiB/run.
- Planned confirmatory envelope: 48 total builds (24 per dataset preferred design).
- Stress budget: 100x the observed artifact-per-run rate, plus the mandatory 5 GiB reserve. This gives a conservative projected payload of 646.67 GiB and projected total of 651.67 GiB.
- Remaining data500 margin under that stress envelope: 250.99 GiB.

The storage sub-gate is therefore **PASS for data500 placement under the recorded stress envelope**. The 100x factor is a storage guard, not a runtime or scientific-performance claim.

## Runtime and safety status

Historical build times were 25.04 s minimum, 38.32 s median, and 148.37 s maximum across 113 Gate-A runs. These are historical observations, not a confirmatory runtime guarantee. CPU and memory were idle at audit (128 logical CPUs, approximately 238.5 GiB available memory, no swap, no relevant active process). A runtime pilot is still required before the full matrix can be authorized.

No old result, log, index, sealed query role, validation-dev role, or formal-test role was modified or accessed. The overall decision remains `BLOCKED_BY_BUILD_LEVEL_POWER_OR_RESOURCES` with `P3=CONDITIONAL`.
