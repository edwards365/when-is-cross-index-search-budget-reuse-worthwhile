# Finite counterexamples

Every table is interpreted exactly and is reproduced by `tests/icba_oracle_observable/exhaustive_verify.py`.

## C1/C2 — positive oracle headroom, zero observable value, and useless sentinels

Environments are equiprobable. Observation is always `z`. Actions are `(a0,a1,f)`.

| environment | cost a0/a1/f | risk a0/a1/f |
|---|---|---|
| 0 | 0/2/1 | 0/1/0 |
| 1 | 2/0/1 | 1/0/0 |

At `delta=0`, observable safety forces fallback cost one; the oracle costs zero. Any number of identical `z` observations is useless.

## C3 — easy environment identification, no cost value

Observations reveal the environment perfectly, but both environments have cost `(0,1)` and risk `(0,0)`. The same first action is optimal, so identification accuracy can be one while observable gain is zero.

## C4/C9 — low exact accuracy, negligible regret; zero cost margin

Two actions have costs `(0,epsilon)` in every state but a tie-breaking oracle label alternates. Always choosing the first action can have 50% exact accuracy and regret at most `epsilon/2`; at `epsilon=0`, exact accuracy is undefined as a value metric.

## C5 — meta-average safe, pointwise unsafe

Let `Pi(theta_0)=0.99`, `Pi(theta_1)=0.01` and risks be `0` and `1`. Meta-average risk is 1%, while target `theta_1` is always unsafe.

## C6 — current-target certificate, open-world failure

One action has risk zero on the certified target and risk one on an unseen environment outside the calibration support. Arbitrarily many current-target queries leave the unseen risk unchanged.

## C7 — reused selection/certification

There are `M` independent candidate actions, each with true Bernoulli failure probability `delta`. One observation is drawn for every action; select any action with observed zero and report the same zero as its certificate. False acceptance occurs with probability `1-delta^M`, not the nominal single-action probability `1-delta`. Data reuse destroys the selected-action conditional argument.

## C8 — zero risk margin

An action has true risk exactly `delta`. For every finite iid sample there is positive probability its empirical risk lies on either side of `delta`; stable strict certification cannot be guaranteed without slack.

## C10 — truth cost destroys search-only gain

Baseline search cost is 10. Recovery search cost is 8 but fixed evidence cost is 300. At workload `N=100`, total recovery cost is 11, worse than baseline. Break-even requires `N>150`.

## C11 — safe fallback with zero value

Fallback and baseline are the same safe action with cost 10. A selector that always rejects is perfectly safe but has zero observable gain.

## C12 — source-only collision

Two environments share source metadata `x`, while their minimum safe budgets are 1 and 2. A source-only action 1 is unsafe in the second; action 2 is conservative in the first. This is the ordered-action instance of the two-point conflict.

## Accuracy–regret separation

Let oracle labels have probabilities `(0.9,0.1)`. Majority prediction `0` has accuracy 0.9. If its rare-class error costs 100, regret is 10. Always predicting `1` has accuracy 0.1, but if its common-class error costs 1, regret is 0.9. Thus lower exact accuracy has lower decision regret.
