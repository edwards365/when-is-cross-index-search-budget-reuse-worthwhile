# Z1 exploratory information pilot

## Protocol

This is an `EXPLORATORY_INFORMATION_PILOT`, not algorithm performance. It reuses nine frozen SIFT-100K HNSWlib builds, 256 fingerprint queries and 744 disjoint evaluation queries per build. Fingerprints use only unlabeled runtime fields at fixed budgets 32, 128 and 512. No graph, query, threshold, model or sealed split was added. The three preregistered summaries are NDC quantiles, returned-distance/gap quantiles, and fixed-probe NDC increments plus returned-neighbor stability.

## Results

NDC quantiles have Spearman 0.7454 with minimal-safe-budget response distance; the 5,000-replicate build resampling interval is [0.4429, 0.9152], all leave-one-build-out directions are positive, and the monotone upper envelope covers 97.22% of held-out build pairs. Nevertheless, nearest-build transfer under-budgets 11.90% of evaluation queries on average and 24.19% on the worst build.

Fixed-probe increments have Spearman 0.5695, interval [0.1515, 0.8857], all leave-one-build-out directions positive and 95.83% envelope coverage; nearest-build under-budget risk is 9.53% on average and 10.08% on the worst build. Distance/gap quantiles are unstable: Spearman 0.1192, interval [-0.3333, 0.7143], only 44.44% positive leave-one-build-out directions, with 16.10% average under-budget risk.

Each build's three-budget fingerprint costs about 1,614,798 distance computations over 256 queries. Amortization is not adjudicated because no fingerprint passes the safety-control Gate.

## Gates

- Z1-A existence: PASS for HNSWlib frozen runtime fields.
- Z1-B directional stability: PASS for NDC quantiles and fixed-probe increments; FAIL for distance/gap.
- Z1-C certification relevance: FAIL for all three. Pair-envelope coverage alone is insufficient; realized nearest-build under-budget risk remains well above 5%.
- Z1-D complexity: NOT ESTIMABLE / not reached after Z1-C failure.

## Decision

The frozen HNSWlib data contain deployable information correlated with budget response, so “no Z1 exists” is too strong. However this information does not control held-out safety at the required level. The pilot label is `Z1_PILOT_FAILED_RESPONSE_CONTROL`. It supports further theory about structured information conditions but does not authorize algorithm design or formal testing.

All conclusions inherit the conditional-baseline limitation recorded in `full_seal_reaudit.md`.
