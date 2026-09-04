# ICBA GSC Phase 0 input audit

Audit scope: the ANNS main worktree on server `101.6.160.66`, branch
`exp/icba_gsc_behavioral_operator_search`, HEAD
`759e605044491bb911dc74a6839cedd89a200d1b`.  No tracked changes were present;
only pre-existing untracked historical artifacts were observed.  No experiment,
validation-dev, formal-test, or future-confirm process was running.

Frozen references were present and type `commit`: CIBS closure
`736c3799a92bf31f503c37e8eaaf680f84398aa5`, CFSR-Lite pilot
`7417147e9ce2e526973cd47b3b390c0ae2bb7c65`, semantic gate
`f7f08ce1f82e23eb4b14cdc08db1190301dc82af`, theory locks
`b0190169cdb758aa5311c7d13fbfd4fd724020f0`,
`4e728d437038816a7706e9cb802d19274aa691b9`, and
`41a44bd930679b5e933034a1496d2fe42e1ae018`.

The frozen raw inputs are SIFT-100K (525,128,288 bytes; source SHA
`dd6f0a6ed6b7ebb8934680f861a33ed01ff33991eaee4fd60914d854a0ca5984`) and
Arxiv-Nomic-100K (4,135,431,488 bytes; source SHA
`8be0993b978b0d0ef023d21d878251a5ed09e058adb25994553c08388d37d414`).
The GloVe input remains sealed and is not used.  The project virtual
environment imports hnswlib 0.8.0; the frozen CIBS manifest records source
commit `3f3429661187e4c24a490a0f148fc6bc89042b3d`.

At audit time the root filesystem reported 18,467,468 KiB available.  With a
5,242,880 KiB reserve and a 10,485,760 KiB minimum experimental allowance,
the resource gate passes.  This is a minimum-margin pass; projected additions
must be recomputed before every build and execution must stop if the reserve
would be crossed.

The CIBS role manifest reports zero pairwise overlap among its design,
sentinel, evaluation, and future-confirm source IDs.  GSC roles are not yet
allocated; their IDs remain sealed in `query_role_audit.csv`.  Future-confirm,
certification, and evaluation data are not accessed in Phase 0.

Phase 0 result: `PASS_RESOURCE_AND_INPUT_AUDIT`; no operator search or query
execution was started.  Existing results, indexes, logs, and worktrees were
left unchanged.
