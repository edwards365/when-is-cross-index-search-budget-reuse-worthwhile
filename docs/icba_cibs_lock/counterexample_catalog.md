# Counterexample catalog

All witnesses are finite and deterministically verified by `scripts/icba_cibs_lock/verify_cibs_lock.py`.

| ID | Failed shortcut | Finite witness | Consequence |
|---|---|---|---|
| CE01 | each candidate has 95% coverage, so selection is 95% safe | 36 independent 5% errors give family-wise error (1-.95^{36}=.8422) | simultaneous control is mandatory |
| CE02 | mean Recall implies low failure risk | 94 queries at recall 1 and 6 at 0: mean .94, failure risk .06 | certify the event, not only mean recall |
| CE03 | raw fixed-`ef` recall is monotone | one query has recall 1 at `ef=40`, .9 at `ef=80` | no raw-action envelope certification |
| CE04 | smaller budget proxy means smaller NDC | action A `ef=20,NDC=100`; B `ef=40,NDC=80` | proxy gains require real NDC measurement |
| CE05 | lower mean NDC ensures lower p95 | A: 94 zeros and 6 hundreds; B: all sevens | separate tail gate |
| CE06 | sentinel winner generalizes | sentinel costs A=1,B=2; evaluation A=3,B=2 | independent evaluation is needed |
| CE07 | post-hoc candidate generation is harmless | select among 20 unadjusted 95% intervals | fixed-family certificate no longer applies |
| CE08 | always choose something | UCBs .08 and .09 with \(\delta=.05\) | empty set must fallback |
| CE09 | endpoint infeasible can be max-budget success | 10 of 100 unreachable queries relabeled success | true risk .10 can be erased |
| CE10 | shared truth makes multi-build evaluation free | truth=100 plus 36 searches at 10 = 460 | charge action searches |
| CE11 | query bootstrap covers build uncertainty | portfolio P1 prefers A; P2 reverses | need independent portfolio units for outer claims |
| CE12 | positive oracle headroom ensures break-even | offline=1000 and realized (g=-.1\) | no finite break-even |
| CE13 | pairing always reduces variance | both variances 1, covariance -.5: paired variance 3 vs 2 | efficiency is covariance-conditional |
| CE14 | Bonferroni is always efficient | 36 perfectly correlated tests | valid but needlessly conservative |

These counterexamples do not invalidate CIBS-Fixed as specified; they invalidate common semantic shortcuts that the frozen protocol excludes.
