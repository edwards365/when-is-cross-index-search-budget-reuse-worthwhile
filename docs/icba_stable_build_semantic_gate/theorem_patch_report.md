# T-SC5/T-SC10 patch report

## T-SC5 replacement

### T-SC5a — certificate disruption

For a preregistered finite certificate edge set of size at most `h`, if each edge has marginal target-loss probability at most `rho`, then certificate-edge disruption probability is at most `h rho` by the union bound. This says nothing about search success when edges remain.

**Status:** `FORMAL_PROOF_COMPLETE`; classical application.

### T-SC5b — deterministic expansion-prefix delay

Under the full Layer-1 state and admission premises in the crosswalk, retaining all certificate insertions and allowing at most `s` actual target-only priority pops before certificate completion yields

\[
B_{G_t}^{exp}(q)-B_{G_s}^{exp}(q)\le s.
\]

Proof is induction over the source certificate. At step `j`, the prior certificate predecessor has been expanded by target time `j+sum_{i<=j}rho_i`; its retained edge discovers and admits the next certificate node. Fixed composite priorities allow only counted intruders to precede it. The safe best-so-far checkpoint is therefore reached after at most `s` extra pops.

**Status:** `FORMAL_PROOF_RESTRICTED`.

### Deleted sentence

The former conclusion `B_Gt <= ceil_E(B_Gs+s)` is deleted when `E` is an `ef` grid. It remains valid only when `E` is an expansion/checkpoint grid. There is no licensed arithmetic `ef+s`.

**Overall T-SC5 status:** `THEOREM_RESTATEMENT_REQUIRED` and `THEOREM_INVALID_FOR_EF_ACTION` for the old fixed-`ef` reading.

## T-SC10 replacement

### T-SC10a — generic structural impossibility

The existing finite constructions still show that generic edge Jaccard/local-neighborhood similarity does not uniformly control safe-budget response. This holds separately for `B_exp` and, through finite fixed-action witnesses, for `B_ef`.

**Status:** `COUNTEREXAMPLE_FOUND` / complete negative result.

### T-SC10b — abstaining expansion surrogate

Define the registered per-query surrogate

\[
d_\Phi^{exp}(G_s,G_t;q)=
\begin{cases}
s(q),&\text{all certificate node, edge, key, tie and admission premises pass},\\
\bot,&\text{otherwise}.
\end{cases}
\]

Then T-SC5b gives the one-sided expansion bound when the surrogate is finite. Backup paths reduce abstention only if their insertion/admission states are themselves registered; edge-disjointness alone is insufficient.

**Status:** `FORMAL_PROOF_RESTRICTED`.

### T-SC10c — raw `ef` interface

Any map `d_phi -> B_ef` is fitted and checked on independent calibration queries/builds with simultaneous one-sided uncertainty. It is not a corollary of T-SC10b.

**Status:** `EMPIRICAL_CALIBRATION_ONLY`; `IMPLEMENTATION_BRIDGE_NOT_PROVED`.

## Ground-truth correction

The phrase “first safe discovery” requires exact top-k truth at target Recall threshold `tau`. Therefore the primary critical-path version is a **labeled workload-aware construction method**. Truth acquisition is build cost; design truth cannot overlap calibration, certification or evaluation IDs. ANNiE and QBAT profiling/retraining are mandatory cost baselines.

An unlabeled version may weight expansion frequency, frontier persistence, path recurrence and margin. It cannot call an edge “Recall-critical,” locate first safe discovery, or claim a risk/safe-budget guarantee.

## Claim ledger changes

Delete:

- T-SC5 directly controls hnswlib `ef`;
- one intruder requires exactly `ef+1`;
- larger independent `ef` runs always reuse/contain the smaller trace;
- raw fixed-`ef` Recall is automatically monotone;
- introduction edges are properties of the graph alone;
- critical-path construction is label-free;
- generic structural similarity gives a fixed-`ef` safety bound.

Retain narrowly:

- an expansion-prefix certificate under explicit state/admission/tie premises;
- a negative theorem for generic structural surrogates;
- a measurable Graph-ANNS trace/intruder interface;
- independent calibration of structure to raw fixed-`ef` response;
- fixed-target certification and fail-closed fallback after query-role separation.
