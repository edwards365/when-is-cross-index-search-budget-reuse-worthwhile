# P4 literature audit + theory derivation + conclusion optimization

## Theory note: what grid sensitivity does and does not test

The registered grid G defines the action space; the transport event is
Z_t(q, B_s^G(q)). Subgrids G' subset G change two things at once: (a) the min-safe action
B^G'(q) >= B^G(q) pointwise (fewer, larger actions), which mechanically lowers measured
under-budget frequency, and (b) the achievable conservatism, which shrinks. Therefore
grid sensitivity is NOT a robustness check on a fixed estimand - it is a family of
related estimands indexed by G. The correct claims are the two the data support:
(i) the qualitative phenomenon (risk far above the 2% materiality gate) holds on every
registered subgrid, including a 3-action coarse grid (10.3%-17.8%); (ii) numeric risk
levels are grid-indexed, reinforcing the paper's native-action guardrail (never compare
raw grids across implementations). A shifted grid with new action values would require
new ANN searches and stays NOT_ESTIMABLE by design.

## Literature audit

- Budget-grid resolution effects: QBAT (Bae et al. 2026) and adaptive-termination lines
  tune on operator-specific grids; our subgrid result gives the phenomenon-level claim
  those papers' fixed grids cannot. Anchor for QBAT (pending from P0) can cite this row.
- The "coarse grid still fails" observation connects to robust quantile choice: on a
  3-action grid the max-over-source policy from P2 remains well-defined, and pooling risk
  bounds carry over verbatim (order statistics on any finite ordered set), so the
  constructive table is also grid-robust in the same sense - one sentence for P5.

## Conclusion optimization (fed to P5)

1. Section 7 gains one sensitivity paragraph + four-row table; abstract unaffected.
2. The economics matrix becomes the paper's single cost table (replaces scattered P4/P6
   citations); every NOT_ESTIMABLE reason string is kept in the artifact.
3. Claim registry: add "grid-robustness on registered subgrids" as an allowed claim;
   explicitly forbid "resolution-invariant risk level" (estimand is grid-indexed).
