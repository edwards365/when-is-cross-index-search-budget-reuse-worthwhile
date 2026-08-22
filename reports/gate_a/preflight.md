# Gate A preflight

Status: **READY FOR ONE-DATASET/ONE-SEED FAIRNESS SMOKE**. Bulk execution is not yet
authorized. Formal HDF5 `test`, `neighbors`, and `distances` remain sealed.

## Repository and baseline

- Branch: `exp/geometry-first-resistance-second`; preflight started from clean,
  remote-aligned commit `8d7e337`.
- hnswlib submodule: `3f3429661187e4c24a490a0f148fc6bc89042b3d`.
- Phase I tag remains `phase1-local-resistance-null-v1`; Gate 0 and specificity
  controls are inherited without parameter changes.
- Python: 65/65 tests passed before Gate-A changes; Ruff passed. Release CTest 3/3
  passed. The instrumented upstream smoke returned Recall@10=1 and exact wrapped
  mean NDC=199; its replay assertion matched upstream labels and exact distance calls.
  The upstream built-in metric remained 24.4375 and is explicitly forbidden as total
  NDC.

## Frozen definition

The single configuration is `configs/gate_a/gate_a_100k.yaml`, SHA-256
`34dba99482ad060ccbb6d9ec984edfa36662aa0c2751601df1b0b4c9e7a07abd`.
It freezes three 100K datasets, 1,000 development queries, `k=10`, `M=16`,
`efConstruction=100`, build seeds 7/17/29, control seeds 101/211/307, epsilon zero,
one thread, the six-point ef grid, and five predeclared midpoints. The generated run
matrix contains 81 unique builds: 27 deterministic-method builds and 54 randomized
control builds.

## Data audit

All source-file and derived-file hashes matched. Every base is float32 with 100,000
rows; queries are float32 with shape 1,000×dimension; truth is int64 1,000×10. Query
source IDs lie strictly in the frozen post-base train interval, and neither IDs nor
vector bytes overlap base. Eight fixed queries per dataset were exhaustively
recomputed and matched frozen labels and float64 distances exactly within `1e-12`.
Only the HDF5 `train` member was accessed. A role-aware reader now rejects formal
members in development mode, with positive and negative unit tests.

## Environment and resource boundary

Hardware is an ASUS TUF F16 with Intel i9-14900HX (24 physical/32 logical cores),
15.627 GiB RAM, RTX 4070 Laptop 8 GiB, and 256.261 GiB free disk at audit. Software is
Windows 11 10.0.26200, Python 3.11.16, MSVC 19.44.35222, CMake 3.30.5, NumPy 1.26.4,
SciPy 1.13.1, and hnswlib 0.8.0. The active power plan is `Silent`; latency is valid
only as same-device paired evidence under this recorded state. NUMA enumeration was
not exposed by `Win32_NumaNode`; the machine is single-socket.

Only 1.42 GiB RAM was free at the first resource snapshot. Gate-A configuration
therefore fixes one build at a time and requires at least 4 GiB free before a long
build. SIFT seed-7 fairness smoke is the next authorized action. Bulk 45/81-run
execution remains blocked until that smoke validates exact NDC, query schema,
treatment matching, runtime, memory, and index size.
