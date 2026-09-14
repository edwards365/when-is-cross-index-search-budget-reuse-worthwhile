# DARTH versus TCP M4: ICBA audit-before-deploy value

M4 replays only sealed M1--M3 outputs. A blind policy is treated as deployed on every target build; the ICBA path first applies the disjoint 500-query target certificate and sends a rejected policy to the already certified fixed-safe action. Evaluation truth is used only after the decision.

Across the seven registered DARTH strategy/cell combinations (70 build decisions), every raw deployment was evaluation-unsafe and all 70 were blocked by the audit. Target retraining did not change that result. The price of correct rejection was loss of DARTH's attractive raw distance-computation numbers: its audited deployment became fixed-safe in every case. Thus the audit contributes genuine safety value and prevents an efficiency-only comparison from endorsing an inadmissible method.

TCP displayed a different profile. No raw TCP build was evaluation-unsafe, although finite-sample certification rejected some actions at 1% and 5% refresh. Audited fallback retained mean distance-computation reductions versus fixed-safe of 44.8% at rebuild-only, up to 26.5% at 1% refresh, and up to 49.0% at 5% refresh. At 10% refresh the pool selected the safe endpoint and the advantage became exactly zero. The 5% refreshed-pool cell also improved mean per-build p95 by 31.72 distance computations; other cells expose small tail costs and are not described as tail improvements.

The result supports a scoped paper claim: ICBA is useful as a guardrail that prevents unsafe DARTH deployment and as a selector that preserves TCP's safe efficiency advantage when recovery headroom exists. It does not establish universal TCP dominance, a formal 5% source-build conformal certificate, or wall-clock superiority. Safety is supplied by independent target-query certification, and the explicit 10% null cell provides the registered stopping boundary.

