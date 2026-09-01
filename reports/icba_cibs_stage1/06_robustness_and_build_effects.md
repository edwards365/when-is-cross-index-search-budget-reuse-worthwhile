# Robustness and build-effect report

| Dataset | Frozen action stability | Selected-action removal | Selected-build removal | Top-1% deleted gain positive |
|---|---|---|---|---|
| SIFT-100K | 94.46% | G1:ef=96 | G1:ef=96 | True |
| ArXiv-Nomic-100K | 100.00% | G2:ef=64 | G3:ef=64 | True |

LOBO, per-ef build effects, per-query gain ECDFs, and all 5,000 selection-stability counts are in the machine record. These diagnostics do not change the frozen selection.
