# CIBS-Race theory template

## Status

`CIBS_RACE_THEORY_TEMPLATE_AUTHORIZED`

This authorizes mathematical development only. Real implementation remains blocked until the CIBS-Fixed pilot passes every Stage-I gate.

## Information process

At batch time (t), a new shared query reveals the vector \(O_t=\{Z_t(a),C_t(a):a\in\mathcal A_t\}\) for actions still evaluated. Maintain simultaneous anytime-valid confidence sequences \([L^r_t(a),U^r_t(a)]\) and \([L^C_t(a),U^C_t(a)]\), using a prespecified alpha allocation/spending rule. Fixed-(n) Clopper–Pearson intervals cannot be repeatedly inspected under adaptive stopping and retain their nominal coverage.

## Safe eliminations and stopping

1. **Unsafe elimination:** remove (a) when \(L^r_t(a)>\delta\).
2. **Cost dominance:** after some (b) is safety-certified (\(U^r_t(b)\le\delta\)), remove (a) when \(U^C_t(b)<L^C_t(a)\).
3. **Stop:** select a certified (b) only when its upper cost is within \(\varepsilon\) of every action that could still be safe.
4. **No result:** at the evidence cap, return the preregistered fallback.

On the event that all confidence sequences cover at every time, every selected action is safe, all unsafe eliminations are sound, and the stopped action is \(\varepsilon\)-optimal among actions not validly eliminated. A full stopping-time theorem requires an explicit confidence-sequence construction, handling of action-dependent observation cessation, and an exact alpha ledger; those are not supplied as an implementation in this lock.

## Complexity sketch and prior overlap

For bounded/sub-Gaussian observations, gap-dependent evidence is expected to scale like

\[
O\left(\sum_a \frac{\log(M/\alpha)+\log\log(1/\Delta_a)}{\Delta_a^2}\right),
\]

with separate safety gaps \(|r(a)-\delta|\) and cost gaps. This is a template, not a proved CIBS-specific optimal rate. SafeBAI, Track-and-Stop, LUCB/successive elimination, racing, and confidence-sequence literature create `STRONG_THEOREM_OVERLAP`. Any future contribution must center the paired full-information Graph-ANNS service-cost interface, not claim new generic racing theory.

