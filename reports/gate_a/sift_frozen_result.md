# SIFT-100K frozen Gate-A result

Status: **FROZEN WEAK NEGATIVE (development evidence)**.

The sealed-development matrix contains three build seeds, 27 main runs, and five
uniformly scheduled midpoint supplements. Every run used the frozen 100K base,
1,000 development queries, exact development top-10 truth, and configuration SHA-256
`2b8b1da4fbec3b3c67f4fcfaae16b151edc07d48cba5a14161dbe79fe2b174fc`.
Formal HDF5 `test`, `neighbors`, and `distances` members were not accessed.

The primary endpoint is the minimum observed p95 exact NDC among efSearch settings
whose mean Recall@10 is at least 0.95. With the cost-improvement convention
`(Geometry cost - GGR cost) / Geometry cost`, positive is favorable. The three
build-seed improvements were:

| Build seed | Signed GGR minus Geometry |
| --- | ---: |
| 7 | -1.121% |
| 17 | +0.098% |
| 29 | -0.279% |

The across-build mean is -0.434%. One build has a favorable point estimate beyond
1%, but directions are not consistent and GGR does not stably outperform either
Geometry-safe Random or Shuffled-Resistance. Higher-recall and p50/p99 checks do not
show a stable resistance-specific benefit. SIFT is therefore frozen and must not be
used for further epsilon, candidate-pool, weight, query, or ef-grid selection.

This is a development-set empirical result. It does not alter the valid local
effective-resistance mathematics, and it does not establish formal external validity.
