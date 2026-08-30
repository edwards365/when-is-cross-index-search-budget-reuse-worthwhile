# Executive summary

## Decision

**Final label: `READY_WITH_THEOREM_DOWNGRADE_EMPIRICAL_BRIDGE`.** The permitted pilot interface is **Interface C — `EMPIRICALLY_CALIBRATED_EF_PILOT`**. This authorizes a small, preregistered pilot after the listed instrumentation and repair code is implemented and smoke-tested. It does not authorize a claim that T-SC5 directly certifies hnswlib `ef`.

The server worktree paths named in the task were not mounted. This audit therefore used an isolated staging tree and the authenticated GitHub repository at the four frozen commits. No server-worktree inspection is claimed.

## Gate results

| Gate | Result | Evidence |
|---|---|---|
| L — direct prior art | PASS | Ten Level-A full texts were newly read or directedly rechecked; no work met all four direct-prior predicates. |
| U — unit consistency | PASS | Requested `ef`, retained-result capacity, actual expansions, NDC and time are separately defined. |
| H — implementation audit | PASS | Project pins hnswlib v0.8.0 / `3f342966…`; `searchKnn` and `searchBaseLayerST` were read at that commit. |
| B — implementation bridge | PASS BY DOWNGRADE | No nontrivial implementation bridge from expansion-prefix delay to raw fixed-`ef` action is proved. Layer 3 is empirical only. |
| O — observability | PASS WITH IMPLEMENTATION WORK | 16/24 fields are already emitted or reconstructible; all 24 are obtainable after a specified tracer extension. |
| A — repair instantiation | PASS AT PSEUDOCODE LEVEL | Objective, tie rules, mandatory edges, deletion, connectivity, layer and fallback are frozen; production code does not yet exist. |
| P — query roles | PASS | Design, calibration, certification and evaluation IDs/truth are pairwise disjoint; evaluation truth is sealed. |

## Semantic finding

At the pinned implementation, Python `set_ef` sets `ef_`; `searchKnn` calls base search with `max(ef_, k)`. In base search, that value controls the maximum retained `top_candidates` heap and participates in admission/stopping. The candidate queue is not capped by `ef`, and the number of candidate pops and distance computations can exceed it arbitrarily.

Accordingly:

\[
B_G^{ef}(q)=\min\{e:R_G(q,e)\ge\tau\}
\]

is an input-parameter response, while

\[
B_G^{exp}(q)=\min\{w:\text{a resumable best-so-far prefix is safe after }w\text{ pops}\}
\]

is an execution-prefix response. They are not interchangeable. Current premises do not prove a useful function `psi` with `B_G^ef <= psi(B_G^exp)` uniformly over builds and queries.

## Theorem correction

- T-SC5's union-bound disruption clause remains valid and classical.
- T-SC5's search clause is `FORMAL_PROOF_RESTRICTED` only for a deterministic expansion-prefix machine with fixed numeric keys and explicit tie tokens.
- T-SC5 is `THEOREM_INVALID_FOR_EF_ACTION` as previously phrased.
- T-SC10's general no-surrogate counterexamples remain valid.
- T-SC10's positive clause controls expansion-prefix delay and abstains on certificate failure; `d_phi -> B^ef` is `EMPIRICAL_CALIBRATION_ONLY`.
- Raw fixed-`ef` Recall is not licensed as upward-closed. A resumable best-so-far prefix is upward-closed by construction; a monotone envelope may summarize raw runs but cannot prove the raw action safe.

## Prior-art boundary

The most dangerous works are Yang et al.'s path-rank pruning analysis, MARGO's monotonic-path edge weighting, Ma et al.'s SNG degree/path analysis, Steiner-Hardness's graph-native effort object, and Ponomarenko's query-based graph improvement. None combines active construction, cross-build minimum-safe-budget stability, a structure-to-risk/budget theorem and multi-build validation. The defensible novelty is therefore narrow: a cross-build safe-budget estimand, a restricted trace/intruder expansion certificate, and an independently calibrated/certified Graph-ANNS deployment protocol.

## Scope lock

No Stable-by-Construction effect experiment was run. No graph was built. No frozen result was changed. `validation-dev`, `formal-test`, and evaluation truth were not accessed.
