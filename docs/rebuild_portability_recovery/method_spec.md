# Preregistered methods

- **M0 Frozen Transfer:** deploy the source policy unchanged.
- **M1 Target-Only Residual Calibration:** use the fixed target sentinel set to add a one-sided residual shift; this is the strong standard recalibration baseline.
- **M2 Historical Hierarchical Residual Calibration:** use only leave-one-history-out design residual donors plus the same target sentinel transcript.
- **M3 Fingerprint-Gated Local Calibration:** use the frozen first-prefix build fingerprint, the three nearest eligible donor histories, and fixed-safe fallback outside support.

All methods use seed 991, \(k\in\{32,64,128,256\}\), 500 without-replacement repetitions, the same sentinel/evaluation firewall, and the fixed 12-level budget grid. No fifth method, feature search, threshold tuning, target Oracle input, or post-hoc candidate selection is permitted.
