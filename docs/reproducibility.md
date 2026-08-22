# Reproducibility contract

Every run receives a UUID and records the Git commit, hardware ID, dataset path/checksum, algorithm, parameters, seed, insertion order, build configuration, timestamps, raw result path, logs, and status. Data and indexes are reconstructed from manifests and scripts and are excluded from Git.

Latency comparisons require the same device, thread count, compiler configuration, counter setting, warm-up policy, and query order. Counter-enabled and counter-disabled builds are reported separately. GPU exact search is never compared as if it were CPU HNSW query latency.

The current native Windows machine is Tier 0 because memory is below 32 GiB, irrespective of its CPU and GPU. Full 1M sweeps are not scheduled here.

