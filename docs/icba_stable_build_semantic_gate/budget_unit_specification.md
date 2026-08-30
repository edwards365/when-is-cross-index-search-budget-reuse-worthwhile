# Budget unit specification

## Five non-interchangeable quantities

Fix build `G`, query `q`, top-k `k`, and the pinned hnswlib implementation.

1. **Requested parameter** `e_req`: the value supplied through `setEf`; base search receives `max(e_req,k)`.
2. **Retained-result capacity** `e_queue=max(e_req,k)`: the maximum size of `top_candidates` after pruning. It is not a cap on the unbounded candidate priority queue.
3. **Expansion work** `W_G^exp(q,e_req)`: number of base-layer candidate pops whose neighbor lists are expanded. Upper-layer greedy steps are reported separately.
4. **Distance work** `W_G^ndc(q,e_req)`: total calls to the selected distance function, including entry, upper-layer evaluations, and newly visited base-layer neighbors.
5. **Elapsed time** `W_G^time(q,e_req)`: wall-clock duration under a frozen hardware, compiler, thread, cache and warm-up protocol.

`ef` controls item 2 and the admission/termination logic. It is neither item 3 nor item 4. Item 4 depends on expanded-node degrees and previously visited neighbors. Item 5 additionally depends on vector dimension, SIMD, cache state, scheduling and concurrency.

## Two safe-budget objects

For a preregistered finite `ef` grid `E` and raw independent fixed-`ef` output,

\[
B_G^{ef}(q)=\min\{e\in E:R_G^{raw}(q,e)\ge\tau\},
\]

with `infinity` when no grid point is safe and right-censor statement `B_G^ef(q)>e_L` when only the finite grid was observed.

For a single resumable deterministic search state that emits a best-so-far top-k after every pop,

\[
B_G^{exp}(q)=\min\{w\ge0:R_G^{resume}(q,w)\ge\tau\}.
\]

The resumable result must retain the best distances seen so far. With exact, consistently tie-resolved truth this produces an upward-closed safe event. Re-running fixed `ef` values independently does not reuse this state and is a different action.

## Bridge status

No useful uniform bridge from `B_exp` alone to `B_ef` is proved. `ef` is a frontier-retention parameter, so an implementation lemma additionally needs the maximum live retained-result requirement, admission margins, exact tie resolution, entry state, deletion/filter state and stopping state. The current T-SC5 certificate does not provide all of these.

A conditional per-query bridge could be verified retrospectively if a full target execution establishes that each certificate node is admitted and retained for capacity `e` until its pop. That condition already contains target frontier information and is not a source-only theorem. It is therefore an empirical calibration interface, not a theoretical conversion.

## Rounding and endpoints

Grid rounding `ceil_E` is valid only after the controlled quantity and grid share units. Expansion delay `s` may be rounded on an expansion/checkpoint grid. It cannot be added to `ef` without an implementation bridge. If the rounded value exceeds the grid, the result is `infinity`/abstain; it is never silently set to `e_L`.

## Reporting rules

- Report requested `ef`, base expansions, upper evaluations, base NDC, total NDC and time in separate columns.
- Do not call NDC a budget action.
- Do not infer p95 from a mean work identity.
- For fixed-`ef` response, test raw event nesting; do not replace raw output by a monotone envelope in a safety theorem.
- For a resumable-prefix method, include continuation/checkpoint overhead and serialization state in control cost.
