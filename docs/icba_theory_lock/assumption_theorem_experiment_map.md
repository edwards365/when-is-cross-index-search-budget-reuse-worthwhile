# Assumption–theorem–experiment map

| Result | Core assumptions | Formal status | Computational test | Frozen empirical quantity | Included policies | Excluded policies | Method implication |
|---|---|---|---|---|---|---|---|
| I | measurable source summary; almost-sure safety; integrable monotone cost; strict cost for iff uniqueness | FORMALLY_PROVED / explicit conditions | finite envelope exhaustive tests | information tax, alias cells, zero-tax pairs | arbitrary source-summary policies | target-state policies | target information must refine source aliases |
| II | ordered finite grid; stable target demand; monotone policy; query-specific monotone cost | barrier FORMALLY_PROVED; matching RESTRICTED_PROPOSITION | 648 telescoping identities; random nonlinear/flat/weighted tests | barrier-level NDC, trimmed tax, matching diagnostic | safe monotone source-budget policies | nonmonotone or target-state policies | avoid expensive barriers, not merely inversions |
| III | frozen candidates; independent iid calibration; exact binomial model; named multiplicity rule; fixed fallback | FORMALLY_PROVED UNDER EXPLICIT CONDITIONS | 405 exact cells; earlier Monte Carlo | failures, CP bounds, Pcert, fail-closed cost | complete frozen deploy/fallback policies | post-calibration selection | precompute certification power and certify full policy |
| IV | nested target filtration; acquisition cost; finite Markov model for Bellman interface | information result FORMALLY_PROVED; DP UNDER EXPLICIT CONDITIONS | boundary examples; prefix/native equivalence audit | perfect-label prefix Oracle, repeated-probe penalty | target-native stopping times | source-only lower-bound class | acquire cheap resumable target state |

No computational row upgrades a proof status. NDC is implementation-local; Oracle trace values are non-deployable upper bounds.
