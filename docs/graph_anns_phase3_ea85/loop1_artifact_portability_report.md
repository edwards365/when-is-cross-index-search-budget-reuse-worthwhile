# Supplement Loop 1: artifact portability result

Decision: **PORTABILITY_INTERFACE_COMPLETE_EXTERNAL_ASSET_SETUP_REMAINS**.

Eight Phase 1--4 scripts that previously embedded machine paths now expose
explicit CLI or `ICBA_*` overrides while retaining the historical paths only as
backward-compatible defaults. A single artifact interface provides `smoke`,
`tables`, `full-check`, and guarded `full` modes. The full mode requires an
explicit acknowledgement and never downloads or deletes data.

The three analysis paths with sealed raw inputs (DARTH, Vamana, and Deep1M)
were rerun through explicit root arguments. All 80 pre-loop scientific files
retained their SHA-256 values. A neutral-path smoke passed and the focused suite
now passes 28 tests. The external root/binary preflight also passed on the
reference server.

This closes the machine-path execution blocker without changing any effect,
query role, seed, or decision. It does not bundle licensed/large external data,
nor does it recreate pre-existing baseline indexes; external asset setup still
follows the checksum ledger. The E&A reproducibility score rises, but the
harmonized lifecycle-cost blocker remains.
