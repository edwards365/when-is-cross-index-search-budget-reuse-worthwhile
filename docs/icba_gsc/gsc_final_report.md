# GSC final smoke report

Branch `exp/icba_gsc_behavioral_operator_search` reached the bounded SIFT
operator-validation smoke at commit `5cd1241`.  Eight O4/O6 operator trials
and one O0 control were run on a 10K SIFT subset; O4 passed degree/self-loop
invariants, while O6 produced no safe half-track Pareto point.  O6-robust's
small tail/mean improvement violated recall, and the best recall-safe p95
change was only -0.071%.  The correct label is
`GSC_NO_OPERATOR_SIGNAL_AT_SMOKE`.  No candidate action, track, certification,
final evaluation, Arxiv migration, or future-confirm step was opened.  The
theory remains conditional and the result is exploratory fixed-target smoke
evidence only.
