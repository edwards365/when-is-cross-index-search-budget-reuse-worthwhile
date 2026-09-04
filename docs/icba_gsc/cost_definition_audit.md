# Cost-definition audit

The patched ledger distinguishes candidate online gain, rejection/fallback
tax, control cost, and offline cost.  Candidate gain excludes certification
rejection and fallback; those appear exactly once in `D` and in `C_mixed`.
No cost or break-even estimate is available at Phase 0 because no candidate
action has been selected and no operator trial has run.  The status is
`COST_LEDGER_NOT_STARTED`, not a negative result.

The required consistency check is
`C_baseline - ((1-p_R)C_candidate + p_R C_fallback + C_control) = D`.
Missing truth/control/search components are reported explicitly and prevent a
finite-break-even claim.
