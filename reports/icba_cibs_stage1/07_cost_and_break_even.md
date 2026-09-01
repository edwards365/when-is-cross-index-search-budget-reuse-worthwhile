# Complete cost and break-even report

Construction, peak RSS, exact index bytes, truth acquisition, 36-action search, selection/certification orchestration residual, combined inspection/serialization/replay, storage, and fallback costs are recorded. Selection/certification and serialization were not separately timed by the original runner, so their exact measured combined commands are disclosed rather than imputed.

| Dataset | Extra fixed wall ns | Online saving ns/query | Break-even queries | Extra index bytes |
|---|---|---|---|---|
| SIFT-100K | 62138694221 | -187.620 | NO_FINITE_BREAK_EVEN | 132114180 |
| ArXiv-Nomic-100K | 323637321629 | 150773.872 | 2146508 | 644114180 |

SIFT has no finite wall-clock break-even because CIBS is slightly slower per query. Both truth-available and truth-acquisition-included channels are tabulated for N={1e3,1e4,1e5,1e6,1e7}.
