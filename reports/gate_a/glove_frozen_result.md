# GloVe-100K frozen Gate-A result

Status: **PRIMARY_ENDPOINT_UNREACHABLE_WITHIN_PREREGISTERED_GRID**.

The sealed-development matrix contains three build seeds and all 27 preregistered
main runs. Every run completed without failure using the frozen 100K base, 1,000
development queries, exact development top-10 truth, and configuration SHA-256
`2b8b1da4fbec3b3c67f4fcfaae16b151edc07d48cba5a14161dbe79fe2b174fc`.
Formal HDF5 `test`, `neighbors`, and `distances` members were not accessed.

Across all methods and builds, mean Recall@10 at the frozen maximum efSearch of 200
was at most approximately 0.9273. No run crossed Recall 0.95 or 0.99 between adjacent
base-grid values, so the preregistered midpoint rule triggered no supplement. The
primary matched-recall cost at Recall 0.95 is therefore undefined/right-censored for
this dataset; it is neither a zero effect nor evidence of equal method performance.
The old Gate-A grid must not be expanded after observing this result.

GloVe cannot supply a positive result for the old Performance Gate. Its observed
curves remain usable for explicitly labeled secondary and robustness analyses below
the unreachable primary target, including control comparisons and tail behavior.
