# Equal-information baseline audit

This phase closes an attribution gap without constructing indexes or issuing
new searches.  It reuses the complete, frozen Recall@10=.95 response cube from
the registered five-percent refresh study.

The primary comparison is the registered query-conditional TCP lane versus a
target-only global action.  Both receive the same 500 selection, 500
certification, and 1,000 cold-evaluation queries.  The target-global baseline
chooses the smallest native action passing a one-sided CP screen on selection;
the action is then frozen.  Candidate and endpoint are independently checked
on certification with `.025 + .025` error allocation.  Evaluation cannot
change selection, certification, fallback, or reporting.

The analysis is necessarily post hoc because the parent outcomes were already
known.  It is therefore an attribution audit, not prospective evidence.  Its
first gate is exact reproduction of the paper's existing TCP and endpoint
paired arrays.  Only after that gate passes may the new baseline comparison be
reported.  Mean work, risk, p95, p99, crossed target/query intervals, LOTO, and
deletion of the largest-gain target are all reported separately; a mean win
cannot substitute for a tail result.
