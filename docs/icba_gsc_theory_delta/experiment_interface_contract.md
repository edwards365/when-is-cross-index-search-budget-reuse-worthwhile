# GSC theory–experiment interface contract

This contract is the handoff to the experiment agent. It authorizes protocol preparation and, after the designated gates, the GSC experiment. It does not authorize reading final evaluation during theory work.

## Sync 1 — Phase-0 freeze

Before any operator trial, freeze:

- dataset, implementation, construction parameters, seed/insertion-order registry;
- `cibs_sentinel`, proposal, operator-validation, evaluation, and `future-confirm` roles;
- raw fixed-`ef` semantics and endpoint-aware failure event;
- target \(\tau\), risk \(\delta\), total error \(\alpha\), and finite-family multiplicity;
- bootstrap unit and any build-cluster resampling unit;
- p95/p99 and mean-NDC gates;
- truth access policy, query SHA256, overlap matrix, master seed, and future-confirm seal.

## Sync 2 — operator registry freeze

Register at most 24 trials and three generations. The registry must contain the operator ID, source commit, input fields, output graph hash, expected response target, validation split, and cost accounting fields. O1–O7 may be compared to prior art, but performance results cannot be used to invent an additional operator after the registry closes.

Generation and stabilization may inspect proposal/validation data only. They may not inspect final evaluation or future-confirm truth, and they may not alter the certification family after its first certification outcome.

## Sync 3 — final reporting

After the action and all thresholds are frozen, the experiment agent may read the independent evaluation once. It must report:

- (D_Z,D_C), endpoint disagreement, rank reversals, raw-`ef` response, and any expansion-prefix diagnostic separately;
- candidate-level simultaneous certification and fallback;
- mean NDC, actual expansions, wall-clock, p95/p99, build/operator/truth/certification costs;
- per-dataset gates, independent portfolio/build-cluster uncertainty, and top-1% deletion;
- exact hashes and replay status.

## Prohibited feedback loops

No final-evaluation result may change an operator, seed, insertion order, candidate family, tie-break, risk threshold, p95 rule, baseline, or claim. A failed operator family narrows the empirical conclusion; it does not prove all stabilization impossible.

## Interpretation contract

- `CERTIFIED_SAFE`: fixed-target safety event only.
- `GOOD_CANDIDATE`: empirical mean/tail and recall gates on independent evaluation.
- `DEPLOYABLE`: good candidate plus measured positive service net benefit and replayable artifact.
- `OPEN_WORLD`: not established by this contract; requires an outer build law and independent build units.

