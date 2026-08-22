# Baseline smoke report

This is a Tier-0 correctness and pipeline result, not evidence for H1 or H2. Timing is single-threaded but not CPU-affinity controlled.

Run ID: `5c814131-a03b-4264-9f36-852f06a5b5c4`; dataset: `data/synthetic/narrow_bridge_n2000_d16_s7.npz`; build: 0.0593 s.

```text
 ef_search  recall_mean  recall_ci95_low  recall_ci95_high  latency_p50_us  latency_p95_us  latency_p99_us
        10        0.914           0.9005            0.9275            6.60           8.305           8.912
        20        0.983           0.9765            0.9885           10.90          18.320          30.800
        40        0.997           0.9945            0.9990           15.20          23.875          31.517
        80        1.000           1.0000            1.0000           21.90          25.000          27.943
       120        1.000           1.0000            1.0000           32.00          51.240         111.607
       200        1.000           1.0000            1.0000           41.05          60.025          68.552
```
