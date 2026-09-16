# Ada-ef Arxiv-Nomic-100K Ten-Build Extension Seal

## Protocol

- Registered event: `Recall@10 < 0.95`.
- Primary statistical unit: target build.
- Builds: seeds 991, 1009, 1021, 1031, 1049, 1061, 1069, 1087, 1097, and 1103.
- Per build: 2,000 design, 500 certification, and 1,000 evaluation queries with disjoint roles.
- Certification: one-sided 95% Clopper-Pearson upper bound with threshold 0.05.
- Inference: 5,000 target-build bootstrap repetitions, seed 991; LOBO and deletion of the largest-benefit build are reported.
- Ada-ef is evaluated only on the implementation-supported cosine/inner-product Arxiv-Nomic-100K lane. Euclidean SIFT remains `NOT_IMPLEMENTATION_SUPPORTED_UNDER_REGISTERED_METRIC`.

## Results

All ten raw Ada-ef policies failed independent certification. Raw certification risk ranged from 0.120 to 0.126 and the one-sided 95% upper bound ranged from 0.1466 to 0.1531. All ten fixed-safe `ef=200` actions passed: certification risk was 0.012 and the upper bound was 0.02355 in every build. Therefore every frozen deployment was `FIXED_SAFE_EF200`.

Across evaluation roles, raw Ada-ef risk averaged 0.0952 with target-build bootstrap 95% interval [0.0944, 0.0960]. Its mean distance-computation saving relative to fixed-safe was 0.57596 with interval [0.57547, 0.57646]. Fixed-safe evaluation risk was 0.0060 in every build. Because ICBA rejected the unsafe raw action and selected fixed-safe in every build, audited gain versus fixed-safe was exactly zero, with interval [0, 0].

Deleting the largest raw-efficiency build (seed 991) leaves raw risk 0.09522, raw saving 0.57583, fixed-safe risk 0.006, and audited gain zero. Every leave-one-build-out result has the same qualitative decision.

## Decision

`RAW_ADA_EF_UNCERTIFIED_AUDITED_FIXED_SAFE_ZERO_GAIN`

The result is not evidence that Ada-ef lacks efficiency value in its native setting. It is evidence that its frozen source-side adaptive action does not satisfy the registered per-query Recall@10 safety criterion after target graph rebuilds. ICBA correctly prevents deployment and preserves safety, but it recovers no efficiency over the fixed-safe endpoint on this lane.

Together with the sealed DARTH results, Phase 1 establishes that rebuild portability failure is reproducible across two published adaptive-search method families and two datasets. It does not establish universal failure, absolute SOTA, or a positive TCP efficiency result.
