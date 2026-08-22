# Gate A frozen development data

Run `phase2_gatea_development_data_v2` freezes the query/truth input for the 100K
development screen. For every dataset, base is the first 100,000 rows of HDF5
`train`; 1,000 development queries are sampled without replacement from
`train[100000:200000]` using seed 20260822 plus the fixed dataset index. Every query
was checked byte-for-byte against every base row and no duplicate was found.

Exact top-10 was recomputed from the 100K base in float64. SIFT uses squared
Euclidean distance. GloVe-100 and Arxiv-Nomic are L2-normalized at ingest and use
`1 - inner product`. Distance ties are resolved by ascending base ID. Computation is
chunked but exhaustive; no ANN result enters ground truth.

| Dataset | Truth time | Base content SHA-256 | Query content SHA-256 | Truth content SHA-256 |
|---|---:|---|---|---|
| SIFT | 11.73 s | `d0ad618c...d0ab21` | `945c5d57...95ff3` | `79b4aa2d...b16b1` |
| GloVe | 5.29 s | `c4dd1cf6...8c109` | `a152de04...a1a3` | `1eb20f26...f71ad` |
| Arxiv | 35.16 s | `9fc6c6e7...de107` | `7bc9b685...284e` | `6ce9ece2...a5cf7` |

Total time was 59.10 seconds. The run accessed only `train`; official `test`,
`neighbors`, and `distances` remain sealed. All method/seed runs in Gate A must use
these exact query arrays and ground truth without resampling.
