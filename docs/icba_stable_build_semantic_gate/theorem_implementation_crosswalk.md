# Theorem–implementation crosswalk

## Layer 1 — abstract expansion-prefix theorem

Fix a deterministic best-first transition system with state

\[
S_w=(F_w,H_w,V_w,O_w),
\]

where `F` is an ordered frontier, `H` is the retained-result state, `V` is visited state, and `O` is best-so-far output after `w` expansion pops. Priority is a total composite key, not a floating distance alone. Let the source certificate through its first safe checkpoint `h` contain:

- the entry and source expansion sequence `x_1,...,x_h`;
- for each non-entry certificate node, the edge whose neighbor scan first marks it visited and successfully admits it to the candidate frontier;
- the composite priority key and admission state at that event;
- the best-so-far checkpoint output establishing the safe event.

Assume in the target execution that every certificate insertion edge is present; certificate keys and tie tokens are unchanged; no certificate node is deleted/filtered; and before source step `j`, at most `rho_j` target-only nodes with strictly earlier composite priority are popped. If all required certificate admissions remain valid, then induction on `j` gives

\[
B_{G_t}^{exp}(q)\le B_{G_s}^{exp}(q)+s,
\qquad s=\sum_j\rho_j.
\]

The induction is over candidate pops. It does not mention `ef`. If an admission predicate depends on finite capacity, its full premise must be added; edge retention alone is insufficient.

**Status:** `FORMAL_PROOF_RESTRICTED`.

## Layer 2 — hnswlib implementation bridge

The desired claim is a useful bound such as

\[
B_G^{ef}(q)\le\psi(B_G^{exp}(q))
\]

or a cross-build fixed-`ef` shift bound. It is not proved from the current certificate. `searchBaseLayerST` uses `ef` in both admission and retained-result pruning, while expansion-prefix delay controls pops after successful admission. A certificate node may be first discovered but rejected, and visited marking prevents a later parent from admitting it. Heap capacity, admission margins and ties are therefore additional state variables.

A retrospective target trace can verify a per-query sufficient capacity by replaying every admission and retention decision. Because this uses the target frontier, it is not a source-only portability lemma.

**Status:** `IMPLEMENTATION_BRIDGE_NOT_PROVED`; any statement that T-SC5 directly shifts `ef` is `THEOREM_INVALID_FOR_EF_ACTION`.

## Layer 3 — empirical calibration

On design data, compute a registered trace metric `d_phi` in expansion units. On disjoint calibration queries and held builds, estimate a one-sided relation

\[
\Pr(B_{G_t}^{ef}>B_{G_s}^{ef}+m\mid d_\Phi\le d)\le\eta(d,m)
\]

using finite-sample simultaneous bounds. Candidate policies are frozen before independent fixed-target certification. Failure to obtain a monotone/useful calibration causes abstention/fallback. It never upgrades the Layer-1 proof.

**Status:** `EMPIRICAL_CALIBRATION_ONLY`.

## Introduction semantics

The upstream loop sets `visited[candidate_id]` before distance/admission. Freeze two notions:

- `discovery_parent(v)`: the edge `(u,v)` whose scan first changes `v` from unvisited to visited;
- `insertion_parent(v)`: `discovery_parent(v)` only when that same event admits `v` to `candidate_set`; otherwise undefined.

The certificate uses `insertion_parent`. It is unique in one fully instrumented execution, but is not graph-intrinsic: another equal-key order can expand a different parent first. Exact replay requires the graph bytes, query bytes, entry, code commit, compiler/numeric contract, neighbor order, total tie token, filter/deletion state and stop rule.

## Priority intruder

For the next certificate node `x_j`, a priority intruder is a target-only noncertificate node that is admitted and popped before `x_j` under the frozen composite key. Count actual pops, not merely graph neighbors or candidate insertions. The current event stream can approximate this; exact classification requires queue snapshots and explicit tie tokens.

## Upward closure

| Action | Upward-closure disposition |
|---|---|
| Resumable expansion prefix with retained best-so-far output | Holds by construction, conditional on fixed truth/tie semantics. |
| Raw independent fixed-`ef` runs | Not proved; finite tie counterexample. |
| Monotone envelope of raw fixed-`ef` results | A derived reporting object only; cannot certify the underlying raw action. |
| NDC or time | Cost outcomes, not ordered actions. |

## Endpoint handling

`B=infinity`, `B>e_L`, grid overflow and endpoint failure remain distinct recorded states. T-SC2 may charge them to its bad event. Layer 1 abstains if no safe checkpoint exists. T-SC10 assigns no finite surrogate distance when a certificate premise fails or the target endpoint is infeasible.
