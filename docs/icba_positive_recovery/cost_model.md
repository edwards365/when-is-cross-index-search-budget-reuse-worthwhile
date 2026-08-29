# Cost model

For workload N, search-side total cost is N times mean online policy NDC plus calibration-search NDC. Calibration conservatively evaluates every sentinel over all 12 frozen budget levels; it is not counted as one search per sentinel. Reports cover N={1e3,1e4,1e5,1e6,1e7}. Ground-truth generation and truth storage/read costs have no reliable logs and are `NOT_ESTIMABLE`; they are never set to zero. B5 training, calibration and index-side profiling costs are also `NOT_ESTIMABLE` because an evaluation-independent B5 split cannot be formed from the frozen query IDs.

At k=256, the finite search-side median break-even of B2 versus B1 is about 5,180 online queries for SIFT and 9,424 for Arxiv among directions with positive denominators. These are free-truth/search-side bounds, not deployable net-gain claims. Break-even versus B5 is `NOT_ESTIMABLE`.
