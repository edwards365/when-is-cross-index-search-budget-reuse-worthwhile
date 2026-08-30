# Counterexample catalog

All witnesses are finite. CE01, CE02 and the seeded random search are executable; the remaining cases are algebraic or explicit small constructions. They disprove implications but do not prove positive theorems.

| ID | Non-implication | Witness |
|---|---|---|
| CE01 | high edge overlap -> stable budget | Two graphs share a long chain and differ in one entry-to-target bridge; Jaccard exceeds .75 while one target is immediate and the other delayed/unreachable. |
| CE02 | low edge overlap -> unstable budget | Two graphs have disjoint irrelevant branches but both expose the target from the entry at the same expansion. |
| CE03 | deterministic -> good recall | A canonical graph omits every path to the true neighbor. It is perfectly reproducible and always wrong. |
| CE04 | consensus -> preserved criticality | A bridge occurs in one of ten builds and is essential for a tail query; threshold .5 deletes it with accurately estimated low frequency. |
| CE05 | retained top-1 path -> stable top-k | The nearest path is preserved while the sole path to the second true neighbor is removed. |
| CE06 | stable top-k recall -> stable NDC | Both graphs find the same target set, but one expands six decoys first. |
| CE07 | same mean -> same p95 | `[1 x95, 101 x5]` and `[6 x100]` have the same mean but different p95/tail shape. |
| CE08 | canonical order -> update robustness | Inserting one bridge early changes the ancestry/neighbors of all later points; deterministic replay does not bound update sensitivity. |
| CE09 | local target neighborhoods -> entry-path stability | Target neighborhoods match exactly while entry components/anchors differ. |
| CE10 | critical trace without margin -> stable trace | Equal-distance candidates swap under a deterministic identifier or floating-point tie change. |
| CE11 | minimum crossing -> upward safety | Recall sequence `0,1,0,1` makes a larger budget unsafe after the first crossing. |
| CE12 | endpoint value -> finite stable budget | A source at the maximum grid point shifted by one has no representable action; imputing the endpoint hides infeasibility. |
| CE13 | fixed-target certificate -> open world | Risk is zero on certified `G0` and one on unseen `G1`. |
| CE14 | mean cost gain -> p95 gain | 95 zero-cost and 5 cost-100 queries have mean 5 but p96 100. |
| CE15 | structural shrink -> finite certification gain | Source margin .02 and shift allowance .03 give nonpositive effective margin. |
| CE16 | positive oracle space -> finite break-even | If per-query stable-method gain after control/fallback is nonpositive, no workload amortizes build cost. |

The seeded search over 5-node directed graphs ran 5,000 trials and found a witness with edge Jaccard `2/3`, source budget `4`, and target endpoint infeasibility. This is finite computational support for CE01. It is not a population statement.
