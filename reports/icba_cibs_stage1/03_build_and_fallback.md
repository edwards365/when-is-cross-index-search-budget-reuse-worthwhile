# Build and fixed-safe fallback report

Six preregistered indexes completed without replacement. Every index passed 100,000-node directed layer-0 reachability, byte-identical save/load replay, and native/tracer equivalence. G1 raw ef=100000 enumerated all 100,000 reachable nodes and returned brute-force exact top-10 on all design queries.

| Dataset | G1 bytes | G2 bytes | G3 bytes | Fallback mean NDC | Fallback p95 NDC |
|---|---|---|---|---|---|
| SIFT-100K | 66049984 | 66057668 | 66056512 | 100088.9 | 100123.1 |
| ArXiv-Nomic-100K | 322049984 | 322057668 | 322056512 | 100090.3 | 100131.0 |
