# GSC theory-Delta alignment patch (pre-certification)

This incremental patch supersedes only the affected GSC protocol definitions;
the completed Phase 0 audit and operator-proposal allowance remain valid.  The
theory status is `GSC_THEORY_VALID_CONDITIONAL_EMPIRICAL_BRIDGE_REQUIRED`.

Before any certification or final-evaluation access, the workflow is frozen as
operator generation -> operator validation -> candidate selection -> freeze one
action and one primary track -> independent certification -> one final
evaluation.  Certification does not search or rank a second action, and
`future_confirm` remains sealed.

`M_cert` is the number of actions actually entered into the same simultaneous
certification procedure.  Trial count and generated graph count are reported
separately; trials are not silently charged to `M_cert`.  If one action is
certified, `M_cert=1`; if a separately certified fallback is included,
`M_cert=2`; a K-by-L simultaneous family has `M_cert=K*L`.

For alpha=.05, the report separates four quantities: certificate-radius
requirement, high-probability acceptance requirement, exact Clopper--Pearson
zero-failure requirement, and observed acceptance rate.  The corrected
Hoeffding sufficient condition is

`n >= (sqrt(log(M/alpha)) + sqrt(log(1/beta)))^2 / (2*gamma^2)`,

reported for beta in {0.20, 0.10, 0.05}.  It is a power/sample-size aid only;
exact CP remains the safety certificate.

The online accounting is fixed to

`G_candidate = C_baseline - C_candidate`,
`D = G_candidate - p_R*DeltaC_f - C_control`,
`C_offline = C_build + C_operator + C_truth + C_selection + C_cert`,
and `C_mixed = (1-p_R)C_candidate + p_R C_fallback + C_control`.

The identity `C_baseline-C_mixed = D` must hold before any break-even claim;
otherwise the status is `COST_DECOMPOSITION_INCONSISTENT`.  If D<=0 the label
is `NO_FINITE_BREAK_EVEN_WORKLOAD`; if D>0, `N*=C_offline/D` is reported.

p95 NDC, p99 NDC, CVaR0.95 NDC, and mean NDC are separate columns.  A Tail
track uses p95 as primary and CVaR only as supplementary.  Held-out builds are
`HELDOUT_BUILD_ROBUSTNESS_EVIDENCE`; open-world and arbitrary insertion-order
certificates are not claimed.

Novelty roles are corrected: O1/O3 are component/mechanism baselines, O2/O5
are proposal/diagnostic operators, and O4/O6 (or a preregistered two-operator
O7) are the only routes eligible for `GSC_METHOD_CANDIDATE`.  O4 and O6 each
require at least one conservative configuration.  O3-only success can support
an empirical behavioural signal but cannot be called a high-novelty GSC
method.

At this patch point no operator trial, candidate, certification, or evaluation
has been run or viewed, so no action or track is yet frozen.
