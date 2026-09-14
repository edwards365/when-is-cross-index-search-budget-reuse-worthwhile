# DARTH M1 one-build interim result

Status: **DARTH efficiency signal observed, direct deployment rejected by the strict safety gate.** This is a one-build SIFT-100K result, not the final cross-build or cross-dataset comparison.

The fresh DARTH model was trained only on the frozen 2,000-query source role, using 833,424 observations and the preregistered 11 features. On independent certification it achieved mean Recall@10 0.933 but failed the primary per-query event 80/500 times: risk 16.0%, one-sided 95% Clopper–Pearson UCB 18.95%. The untouched 1,000-query evaluation role agreed (mean Recall@10 0.9308; 167 failures; risk 16.7%). Therefore the model cannot be directly deployed under the registered 5% risk limit.

The fixed-ef certification grid selected ef=80 as the smallest safe fixed baseline: 5/500 failures, risk 1.0%, UCB 2.09%. Ef=40 looked acceptable only after evaluation (3.9% risk), but its certification UCB was 9.40%, so it was correctly not selected. On evaluation, DARTH used 379.0 mean and 695 p95 distance computations versus 962.1 mean and 1265.1 p95 for certified ef=80—60.6% and 45.1% fewer, respectively—but its exploratory wall time was worse (0.649 ms mean versus 0.124 ms), consistent with substantial predictor overhead in this unoptimized bridge. Wall time is secondary until the registered affinity/cache protocol is sealed.

This result supports neither universal DARTH inferiority nor TCP superiority. It establishes a useful comparison tension: DARTH exposes a strong computation-efficiency signal, while ICBA detects that average recall conceals unacceptable query-level risk and forces fallback. M1 remains open for TCP target-pool and multi-build statistics; M2 will test frozen-model transfer across independent rebuilds.
