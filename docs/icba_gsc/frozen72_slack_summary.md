# Frozen 72-action slack audit (proposal-only)

The six frozen sentinel files (three builds x twelve raw fixed-ef actions for
each of SIFT-100K and Arxiv-Nomic-100K) contain 72 action cells and 256 query
rows per cell.  This audit reads only the frozen sentinel role; no evaluation,
certification, or future-confirm query is opened.

All 72 cells had native/tracer top-k equality and `endpoint_status=PASS`.  The
fraction of `Z_abs` failures ranged from 0.0000 to 0.4023 on Arxiv and 0.0000
to 0.5938 on SIFT.  Using a descriptive <=5% slack screen (not a certificate)
left 24 Arxiv cells and 21 SIFT cells.  The lowest descriptive mean-NDC cells
among those were Arxiv G2/ef48 (mean 795.70, p95 1018, Z_abs 0.0078) and SIFT
G3/ef64 (mean 918.00, p95 1149, Z_abs 0.0313).  These values are historical
slack diagnostics only; they do not select a GSC action or establish safety.

The output is `results/icba_gsc/frozen72_slack_audit.csv` (72 rows plus header),
with dataset/build/ef, query count, Z_abs rate, mean/p95/p99 NDC, endpoint and
native/tracer equality.  No operator trial has been run (`actual_operator_trials=0`).
