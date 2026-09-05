# Fixed-target replay gate

The corrected A0–A6 family was frozen before certification. The primary architecture is Select-One-Then-Certify; if selected and fallback actions share one certification sample, each receives alpha 0.025. The Frozen-Family comparator uses Bonferroni alpha divided by the frozen family size. Empirical nesting is not used to justify fixed-sequence or nested-DKW inference.

No legal non-abstain action can be replayed from the frozen inputs. The source policy is absent, the complete twelve-level budget grid is absent, endpoint/censor evidence is not estimable, and the historical records do not expose an independent certification role. The apparent historical target actions cannot be promoted because their selection was outcome-derived. A next-ef action is not a fixed-safe certificate.

Therefore each of the six fixed target builds receives exactly one runtime decision: `A6 / ABSTAIN_NO_SAFE_ACTION`. This is a safe protocol outcome, not evidence that the candidate method is ineffective. No unsafe action is assigned finite regret, no Oracle cost is invented, and no tail or break-even statistic is synthesized without its per-query vector and full-cost inputs.

Gate result:

- Runtime alignment: PASS (24/24 code tests).
- Real-input and source-policy gates: FAIL.
- Independent safety, decision value, p95, break-even, and build robustness: NOT_ESTIMABLE.
- Future confirmation: NOT AUTHORIZED.

No future-confirm, validation-dev, or formal-test data were accessed. The only permitted continuation is artifact sealing and an explicit fixed-target method-closure decision.
