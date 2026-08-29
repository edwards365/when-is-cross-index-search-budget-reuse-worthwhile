# Rebuild portability recovery — executive brief

Status: `EXPLORATORY_DESIGN`; not confirmatory.

The deployable source policy passed all 18 independent source calibration gates. Across 144 directed hnswlib SIFT/Arxiv rebuild transfers, M0 and M1 passed query-safety Gate S in all directions; M1 already passed for every preregistered sentinel count \(k=32,64,128,256\), with median NDC saving about 39.9% versus fixed-safe. M2 increased median saving to 58.5% at \(k=256\) and passed 144/144 directions, but passed only 99/144, 102/144, and 141/144 at \(k=32,64,128\). It therefore did not reduce target truth by 50%. M3 was safe at \(k=256\) but included unsupported zero-gain fallbacks. Under a free-truth search-NDC upper bound, M2 breaks even versus fixed-safe before workload 1,000 in all directions; real truth, certificate, and full-retraining costs remain `NOT_ESTIMABLE`, so strict Gate V2 cannot pass. R1 is a standard fixed-target residual-certificate proposition; R2 remains conditional on unverified local stability and does not certify outer-build risk.

Final decision: `TARGET_ONLY_RECALIBRATION_SUFFICIENT_NO_NEW_METHOD`. Do not authorize a new historical/fingerprint recovery algorithm from this design-stage evidence. Preserve M2 as an efficiency hypothesis for a future preregistered study with measured truth and retraining costs and enough independent builds.

Input limitation: the current 59-file Full Seal set verifies, but the inherited 123-entry legacy list reproduces only 111 entries (eight derived CSV mismatches and four absent bytecode files); exact historical reproduction is not claimed. No validation-dev/formal-test access, new graph construction, GPU use, or confirmatory analysis occurred.
