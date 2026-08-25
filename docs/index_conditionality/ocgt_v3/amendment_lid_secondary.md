## 2026-08-25 — omitted frozen LID secondary baseline

- The frozen primary analysis commit `d50a101` included Oracle, Omega, transfer and SHEAF-like analysis but accidentally omitted the preregistered LID/static secondary baseline.
- `analyze_ocgt_v3_lid_secondary.py` reuses the exact feature definitions and Ridge alpha from the frozen OCGT-v2 implementation; it cannot change Gate O, Gate C or the final primary label.
- This append-only correction was recorded before running the LID secondary analysis. No endpoint, threshold, data member, seed or primary statistic changed.
