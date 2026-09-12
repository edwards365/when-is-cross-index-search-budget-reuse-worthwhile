# P6 literature audit + theory derivation (interim: B and C complete, A running)

## P6-B — learned-predictor layer: the third layer measured (W2 closed)

Result (SIFT/Arxiv, 24 targets each, HistGB on ef=10 deployment-time transcript features):
- source-train -> target-transfer risk: 23.9% / 21.2% vs naive single-source 21.1% / 17.3%
  — transfer is NOT better than blind reuse;
- in-target 5-fold CV risk: 24.1% / 22.2% — the predictor fails even ON the build it
  trains on;
- fit diagnostics: source-train R^2 = 0.124 (log2 B), transfer R^2 on target = 0.015 — the
  minimum safe action is dominated by build-specific graph structure, not by query-intrinsic
  transcript difficulty.

Theory reading: B_t(q) = f_t(q) where f_t is a build-conditioned function with weak shared
component; the effective hypothesis class over 23 source builds estimates only the shared
marginal, which is nearly build-independent (see P6-C) — hence no transfer gain is exactly
what the two-layer decomposition predicts. This is the measured counterpart of the paper's
falsification-ladder row "history adds no stable value", now at the predictor layer.

Literature: consistent with learned early-termination/cost-estimator papers (Li 2020;
Wang 2026 ANNiE; Chatzakis 2025) which all calibrate per index; none claims cross-build
transfer. The probe makes that boundary quantitative for this registry.

## P6-C — transcript distinguishability: Theorem 1's premise, instantiated

Result (552 registered pairs, hit-count transcript over the k cheapest actions, k in
{1,3,6}):
- classifier two-sample accuracy is at chance (median 0.49-0.51, min 0.45) for every pair
  and every k — no classifier can attribute a transcript to its build;
- exact plug-in total variation between transcript marginals: median 0.20, MAX 0.25 at k=6
  (SIFT); <= 0.13 at k=1 (Arxiv) — bounded far below 1.

Theory consequence: Theorem 1's lower bound max_i E[loss_i] >= (Delta/2)(1 - TV) now has an
empirical object: with TV <= 0.25, any transcript-based build-blind policy must lose at
least 0.375*Delta in one of the two environments, while the per-query coupled disagreement
is 45-57% (H1-B). The near-indistinguishability premise — previously flagged (handoff 8.2
item 2) as never instantiated — is instantiated, with the subtlety that indistinguishability
holds at the MARGINAL transcript level while the conflict lives in the per-query coupling.
This resolves the earlier apparent tension between "TV small" and "responses differ".

Caveat to state: the transcript class is the registered hit-count vector over the probe
grid; other probe classes (latency, visited counts) may separate better and are future
work. The claim is probe-class-conditional, exactly as Theorem 1 requires.

## P6-A (running) — expected contributions
Scale replication (W1), 1M profiling cost re-measurement (so-what defense), 1M pooling
k-curve (constructive transfer of P2's result), 1M byte-identity contract check (P3
transfer).
