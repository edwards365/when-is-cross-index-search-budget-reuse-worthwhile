# Certification scope

# E4 semantic and factorial reanalysis

Final label: `E4_H1_H2_TRANSPORT_CONFIRMED_TWO_DATASETS`. Deployment label: `NO_DEPLOYABLE_VALUE`.

This is a post-confirmatory semantic analysis, not the original preregistered primary test. It uses only the frozen E4 query/search records and performs no build, ANN search, query selection, or new truth access. The 48 artifacts are a crossed 2-dataset × 8-seed × 3-fixed-order design; order is fixed and seed is the resampling block.

- sift_100k: H1 nonzero fraction 0.8947; oracle transport risk increment 0.21573; under/over/exact 0.2187/0.2187/0.5625; absolute safe NDC cost 128.46; ratio-of-means tax 0.1945; mean-of-ratios 0.2387.
- arxiv_nomic_100k: H1 nonzero fraction 0.7533; oracle transport risk increment 0.17121; under/over/exact 0.1745/0.1745/0.6510; absolute safe NDC cost 90.79; ratio-of-means tax 0.1488; mean-of-ratios 0.1706.

The former 178%/244% values are retained only under their accurate name, mean per-query relative NDC regret for global ef=120 versus a per-query oracle. Main transport reporting uses absolute NDC difference and ratio of means. Oracle transport is explicitly nondeployable; source/target sentinel calibration is post-confirmatory deployable-information analysis.
