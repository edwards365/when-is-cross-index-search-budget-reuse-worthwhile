# Positive recovery input audit

- Frozen base: `10e003386a5ea67274b0fdb767a7a7a7a106dd43`
- Recovery SHA256: 48/48 passed.
- Legacy limitation: 111/123 only; exact legacy reproduction is not claimed.
- M0 rows: 144; M1 rows: 576.
- M1 target shift zero: 576/576.
- M0/M1 semantic equality at tolerance 1e-9: 576/576.
- Source training IDs: 250; source calibration IDs: 750; target sentinel: 256; target evaluation: 744.
- Source-training/target-evaluation overlap: 177; source-calibration/target-evaluation overlap: 567.
- Evidence label: `PAIRED_QUERY_REPLAY_NOT_NEW_QUERY_GENERALIZATION`.
- validation-dev/formal-test accessed: false/false.
- New graph/GPU use: false/false.

Disposition: `PHASE0_PASS`. The current upward-only M1 is a no-op and cannot be interpreted as true target recalibration. Shared query IDs make this a paired rebuild replay, not independent new-query confirmation.
