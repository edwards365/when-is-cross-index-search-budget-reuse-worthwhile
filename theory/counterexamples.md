# Counterexamples

## High resistance need not aid greedy navigation

Place the center at the origin, target/query direction on the positive x-axis, and a candidate bridge endpoint far on the negative x-axis connecting to a graph appendage with no route toward the target. If that candidate is the appendage's only attachment, its edge leverage is one, yet following it strictly increases query distance and cannot improve a distance-monotone greedy path. Thus resistance alone cannot guarantee navigational value.

## Direction duplication

Several collinear candidates can each attach separate sparse appendages and have high leverage. Resistance-only selection can spend the entire degree budget in one direction. The log-det term penalizes this redundancy but still does not prove global progress.

