# W3 validation and theory–implementation map

Date: 2026-09-17. Scope: manuscript writing only. Parent manuscript revision: `26875efd15bc1a251620808784154ed4d67b6ac1`. W0 evidence remains unchanged. No ANN runs, resampling of empirical data, policy changes, or new result tables were performed.

## Delivered content

- Section 3: event and estimand definitions; first-passing versus stable-tail labels; four propositions with compact proofs (information limit, margin-based selection, simultaneous certification, exchangeable-build pooling).
- Section 4: ICBA roles and outputs; exact refresh TCP policy and global shift; candidate/fallback decision; source-profile and serving-cost interfaces. Figure 2 now contains the five-step executable specification rather than a placeholder.
- Added three classical references; 16 cited bibliography entries overall. Verification depths and primary sources are recorded in `LITERATURE_NOTES.md`.
- Main draft status, completion map, README, and writing plan updated. W1/W2 previews and all historical experimental sources retained.

## Inspected sources and interpretation

|Manuscript object|Repository source inspected|Resolution in W3|
|Information lower bound|`results/graph_anns_phase2_p7/ICBA_ICLR_Anonymous_Revised_v12_final.tex`, theory and proof sections|Self-contained two-point proof; complete observable, disjoint acceptable regions, explicit loss gap. No old plug-in TV value or DKW-to-TV substitution.|
|Conditional recovery|Same old paper, fixed-target theorem/proof|Comparator restricted to margin-feasible policies; correct cost chain includes true selected cost. Selection-event result separated from later certification and fallback cost.|
|Build pooling|Same old paper; `docs/graph_anns_phase2_p11/theorem3_and_policy.md`|Discrete ties handled; infinity is abstention; rank unsupported at nine-source 5%; per-query marginal rather than joint-all-query or fixed-target guarantee. Unverified numerical farm claims are not imported.|
|Simultaneous selected-policy safety|`theory/tcp_certified_graded_fallback.md`; `scripts/tcp_sigmod_regular_closure/phase3_simultaneous_fallback.py`|Union-bound argument permits correlated bounds but requires the frozen family and i.i.d. certification queries. Code's 0.05/3 allocation is a separate historical configuration, not the refresh protocol.|
|Historical TCP-HM9-TC|`docs/tcp_sigmod_regular_closure/canonical_tcp.md`; `scripts/tcp_sigmod_regular_closure/tcp_hm9_tc.py`|Stable-tail at recall .90, infinity retained before endpoint execution. No silent equation with current .95 first-safe replay.|
|Primary TCP replay|`scripts/graph_anns_phase3_ea85/analyze_phase2_refresh95.py`, all functions and decision branches|First passing index, unresolved clipped to endpoint index, nine-old-build maximum, shifts 0–6, first selection-role CP pass, individual candidate/endpoint tests. All-fail records retain failed deployment flag.|
|Query roles and scenario|`docs/graph_anns_phase3_ea85/p2_refresh95_protocol.md`|500/500/1000 target roles; 5% refresh+rebuild; source profiles of corresponding evaluation queries are required inputs.|

## Material distinctions preserved

1. The old minimum-safe-action rank proof cannot silently certify native execution on a non-monotone response. Stable-tail coverage supplies a sufficient bridge; the refresh implementation uses first-safe labels instead.
2. An all-action average non-monotonicity rate is not automatically the failure rate of the deployed selected action. W3 does not import the old additive alpha-plus-average-nu claim.
3. The pool guarantee is unconditional over the exchangeable build draw for each fixed query. It is not conditional risk among accepted queries, simultaneous coverage over queries, or a certificate for an individually chosen target build.
4. The existing 95% candidate and 95% endpoint checks lack a 5% joint error allocation. W3 does not change their thresholds or claim a repaired empirical certificate.
5. A certificate rejection is not proof of unsafety. The 59-query zero-failure threshold is a mathematical acceptance threshold, not a power claim.
6. The refresh shift scan is not the cost-minimizing selector assumed in the margin proposition. Its observed cost improvements remain empirical.
7. Query-role disjointness is not itself proof of i.i.d. sampling. Formal binomial coverage is stated with its population/sampling assumption; the frozen replay numbers remain descriptive at their declared scope.
8. The source-profile, source-truth, shared-query bootstrap and empirical-TV holds remain open. Writing does not repair them.

## Verification

- `check_w1.py`: PASS for 57 frozen macros (34 used), 10 sections, 5 figures (4 placeholders), 4 tables, 4 propositions and proofs, 16 unique cited entries, and cross-references.
- `check_w3_math.py`: 10/10 deterministic checks pass. Checks cover zero-failure CP inversion and 59-query threshold, binomial coverage on a finite grid, tied/infinite-label exchangeable permutation orbits, pool resolution, non-monotone stable labels, the two-point bound on finite examples, grid clipping, the margin cost bound, and error allocation. These are regression examples, not substitutes for the written proofs and not new empirical evidence.
- Bounded single-agent scientific review: the propositions' probability spaces, conditioning, ties, comparator set and fallback scope were checked against the statements and code above. No independent reviewer or new full-paper score is claimed.
- Prose scan flags sentence-length runs and semicolons. Reviewed in context; parallel formal definitions and exact distinctions retained. No em dashes added.
- Tectonic 0.17.0 / XeTeX build succeeds, 8 Letter pages including references. All 8 pages rendered and visually inspected: equations, theorem glyphs, tables and workflow are legible with no visible collision or clipping.
- No undefined citations/references, missing characters, or horizontal overfull boxes. The acmart end-page balance produces a 1.166 pt vertical-box warning without visible clipping. Runtime fontconfig diagnostics and 10 existing bibliography metadata warnings remain; this is not a zero-warning build.
- Original template class, numeric ledger and result macros unchanged. W0 repository check passed before writing and after synchronization. Local and remote W3 PDF bytes match; the ZIP integrity check and 8-page PDF text checks pass. No unrelated working-tree files were included.

## Next stage

W4 should complete the experimental setup and evidence-block definitions, then connect per-build records to the planned exhibits. The current 8-page preview is a partial writing draft, not evidence that the final paper fits its complete content into the submission limit. The compact proofs can be allocated to the separate appendix after the results narrative is complete.
