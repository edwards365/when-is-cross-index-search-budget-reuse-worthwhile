# CERTIFIABILITY_AWARE_ORDERED_RECOVERY_TEMPLATE

**Authorization:** theoretical and preregistration template only. It is not an experimentally validated algorithm and is not authorized for deployment.

## Inputs

- named target build `G`;
- fixed strong baseline `B` and independently justified `pi_fixed`;
- ordered budget grid and a finite, preregistered universe of candidate policies;
- disjoint query-role manifests `D_sel`, `D_cert`, optional `D_tail`, and future evaluation IDs;
- absolute endpoint-aware failure labels on certification queries;
- thresholds `delta`, `alpha`, workload `N`, and a separate tail gate;
- truth, probing, retraining, control, and search costs in compatible units.

## Pseudocode

```text
procedure CERTIFIABILITY_AWARE_ORDERED_RECOVERY_TEMPLATE(inputs)
    assert evaluation truth is unavailable to this procedure
    assert no Oracle action or Oracle-safe-budget feature is an input
    verify D_sel, D_cert, D_tail, evaluation IDs are disjoint as preregistered

    families <- preregister ordered policy families for reuse, recalibrate, retrain
    using D_sel only:
        fit permitted recalibration/retraining objects
        freeze each candidate policy and its conservative order
        estimate recurrent search, control, evidence and training costs
        discard action modes with nonpositive symbolic break-even denominator

    choose one locked safety engine:
        BONFERRONI:
            compute level alpha/L one-sided UCB for every frozen candidate
        FIXED_SEQUENCE:
            verify query-level nested failures on D_cert
            test rungs in order L,L-1,...,1 at level alpha; stop on first failure
        NESTED_DKW:
            verify query-level nested failures on D_cert
            convert each query to minimum successful rung S
            construct the simultaneous survival-function upper band

    certified <- candidates whose locked safety engine proves U_l <= delta

    using D_tail only, or a tail bound frozen before D_cert:
        retain only candidates passing the separate p95/tail gate
        never switch to an uncertified candidate because of a tail result

    for each retained action a:
        total_cost_bound[a] <- recurrent_search[a]
                               + evidence_and_training[a]/N
                               + rejection_probability[a]*fallback_gap[a]
                               + control[a]

    feasible <- retained actions with total_cost_bound[a] < cost(B)
    if feasible is nonempty:
        return argmin_a total_cost_bound[a] and its certificate record
    else if a newly retrained policy can be produced and independently certified:
        return RETRAIN_REQUEST (not the uncertified policy)
    else if pi_fixed has an external fixed-target safety statement:
        return FIXED_SAFE_FALLBACK
    else:
        return ABSTAIN_NO_SAFE_ACTION
end procedure
```

## Safety interface

The template is strictly fixed-target safe only when:

1. candidate policies and their order are frozen before `D_cert`, or safety bounds are simultaneous over the full pre-selection universe;
2. `D_cert` has the stated iid/exchangeable fixed-target law;
3. the absolute failure event includes endpoint censoring;
4. the selected rung is covered by Bonferroni, valid fixed sequence, or the nested DKW band;
5. the terminal fallback has its own safety statement.

If candidate selection and certification use the same data without full-universe simultaneous control, the authorization is withdrawn.

## Economic interface

For action `a`, compute

`D_a=G_oracle,a-R_selection,a-P(R_a)Delta C_f,a-C_control,a`.

If `D_a<=0`, record `NO_FINITE_BREAK_EVEN_WORKLOAD`. Otherwise require

`N>C_evidence,a/D_a`.

This comparison is performed before formal algorithm confirmation. Unknown truth, retraining, or control costs remain symbolic intervals; they are not set to zero.

## Tail interface

Mean cost and p95 use separate gates. A candidate with positive mean net value is rejected by the template if its preregistered p95 or tail-risk upper bound is worse than the baseline tolerance. The safety certificate is never presented as a tail-cost certificate.

## Output record

The template outputs exactly one of `reuse`, `recalibrate`, `retrain_request`, `fixed_safe_fallback`, or `abstain_no_safe_action`, together with:

- certification engine and error allocation;
- selected rung and upper risk bound;
- evidence count and role-manifest hash;
- mean-cost decomposition and break-even workload;
- independent tail-gate result;
- fallback premise and scope label `FIXED_TARGET`.
