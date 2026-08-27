# Main Result III: Risk-Matched and Certification-Aware Adaptation

## Population value and certification are different

`V_delta(G)` assumes the distribution is known and optimizes expected cost subject to true marginal failure at most delta. A deployed certificate is random because it is computed from an independent calibration sample. For a frozen policy `h` with true risk `p(h)`, `X_h~Binomial(n,p(h))`; under a prespecified family of `M` candidates, policy `h` is certified when its one-sided exact upper bound at level `alpha/M` is at most delta. Threshold selection and policy construction must precede and be independent of the certification set. A full sequential policy—including checkpoints, fallback, and any selection rule—is the certification unit; individual checkpoint bounds do not certify an adaptively selected sequence.

## Fail-closed deployment value (`FORMALLY PROVED UNDER EXPLICIT CONDITIONS`)

For a frozen candidate `h`, fixed fallback cost `C_fixed`, online cost `C_h`, and amortized calibration cost `A/N`, define

`C_deploy(h)=1{cert}C_h+1{not cert}C_fixed+A/N`.

Therefore

`E[C_deploy(h)]=P_cert(h)C_h+(1-P_cert(h))C_fixed+A/N`.

For a fixed candidate set and selection rule, the certification-aware value is the minimum of this expectation over candidates selected without using the certification outcomes. If `C_h<=C_fixed`, `A>=0`, and the population-risk optimum is a lower bound on every admissible candidate's online cost, the certification tax relative to `V_delta` is nonnegative. Without these containment and cost conditions, the sign is not a theorem.

Holding the frozen candidate and costs fixed, larger certification probability lowers fail-closed cost when `C_h<C_fixed`. Increasing `n` often increases power for a fixed margin `delta-p`, but also raises one-time calibration cost; total amortized cost need not be monotone at a fixed workload. Increasing `M` weakly reduces the Bonferroni certification event. As `p` approaches delta, power can remain poor even for a truly safe policy. Break-even is infinite when expected operational saving is zero or negative.

The generated frontier fixes a transparent theoretical normalization `C_fixed=1`, `C_online=0.5`, and calibration cost `n` fixed-query equivalents. It is an illustrative certification-cost surface, not a measured latency result.

## Exact certification grid

For alpha 0.05, the grid covers delta `{0.01,0.05,0.10}`, n `{64,128,256,512,1024}`, M `{1,4,16}`, and p `{0.005,0.01,0.02,0.028,0.03,0.04,0.05,0.06,0.10}`. It reports exact `k*`, binomial certification probability, true-safe-but-not-certified probability, exact unsafe-but-certified probability under the named p, normalized expected fail-closed cost, and break-even workload. At n=256, M=16, alpha=delta=.05, `k*=3`.

## GloVe 16-policy autopsy

The frozen calibration table recovers actual failures for all 16 policies: 32–181 failures out of 256. Even the zero-early-stop fallback row has 32 failures, so none certifies at M=1 or M=16. All 16 are classified `POINTWISE_UNSAFE` under the required taxonomy; the 0/16 outcome is not primarily a multiplicity or sample-power failure. Per-policy design gains and per-build confirmation were not preserved for all 16 and are marked `NOT_RECOVERABLE_PER_POLICY`, rather than reconstructed from unrelated splits.

## Signal–certification boundary

The equal-AUROC/AUPRC counterexamples prove only that ranking aggregates do not certify the exact fixed-threshold operating policy. They do not show that AUC is useless for design, that equal-coverage risks must differ, or that every high-AUC policy is uncertifiable.
