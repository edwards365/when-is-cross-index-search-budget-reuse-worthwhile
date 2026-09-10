# Falsification Ladder Methodology

## 1. Purpose

The ladder converts iterative method development into a preregistered scientific object. A route advances only when its predicted success channel survives every earlier rung. Passing a mechanism rung does not authorize deployment; failing a later rung preserves the earlier mechanism evidence while closing the full route.

The ladder is evaluated only from frozen historical results. It introduces no new ANN search, build, query access, or post-hoc threshold optimization.

## 2. Recovery claim decomposition

A deployable recovery claim is decomposed into five ordered questions:

1. **Semantic validity:** Are the native action, failure event, endpoint state, cost, query roles, and target scope well defined?
2. **Attainability and information:** Does the allowed action family contain a nontrivial safe/low-cost action, and can a deployable transcript identify when to use it?
3. **Safety validity:** Is the proposed structure-, policy-, or lane-level bridge mechanically or statistically valid under the registered semantics?
4. **Certification validity:** Can the frozen action be certified from independent target evidence, with valid multiplicity and fallback/abstention behavior?
5. **Deployment value:** Does the accepted route improve its target metric while preserving registered quality, tail latency, robustness, and finite break-even?

The ordering prevents a downstream performance number from repairing an upstream semantic or information failure.

## 3. Condition classes

The ladder distinguishes formal theorem conditions from route-specific engineering hypotheses.

- **Theorem-level obstructions:** endpoint feasibility, environment/action identifiability, positive risk margin with adequate independent target evidence, and valid fallback or abstention.
- **Finite-class method condition:** candidate attainability inside the frozen action family.
- **Route-specific bridge conditions:** structural surrogate validity, conditional rescue, truth-free triggering, and shared-cost realizability.
- **Decision condition:** safety, mean cost, tail cost, and complete economics must be reported separately.

Only the first group is presented as part of the main conditional recovery theorem. The others are empirically falsifiable method premises, not universal mathematical necessities.

## 4. Verdict vocabulary

- `PASS_MECHANISM_ONLY`: the proposed mechanism is real, but later safety/value conditions fail.
- `PASS_FIXED_TARGET_SAFETY_ONLY`: independent target evidence supports safety for the named target without deployment value.
- `FAIL_ATTAINABILITY`: the registered candidate family contains no CI-supported jointly feasible action.
- `FAIL_OBSERVABILITY`: an Oracle or retrospective signal exists but no deployable truth-free transcript selects it.
- `FAIL_SEMANTIC_BRIDGE`: the proposed proxy does not control the native search response under corrected semantics.
- `FAIL_ECONOMIC_VALUE`: safety is possible but mean/tail/total cost or break-even fails.
- `CLOSED`: no further compute is authorized for the route under the current action and signal family.

## 5. Evidence hierarchy

1. Formal theorem/proof under stated assumptions.
2. Independent or disjoint-role fixed-target experiment.
3. Registered multi-build robustness analysis.
4. Retrospective/Oracle mechanism audit.
5. Diagnostic simulation or incomplete-cost analysis.

Experiments support relevance, diagnose assumptions, or falsify a route. They do not prove a general theorem. Oracle headroom never counts as a deployable algorithm.

## 6. Pruning rule

A route is closed when a registered condition fails and the failure cannot be repaired without changing the action space, observable information, cost regime, or scientific question. Such a change constitutes a new route and requires a new theory/semantic lock; it is not a continuation of the failed method.

No route may be revived merely by relaxing all quality, tail, and cost constraints simultaneously. A narrower objective is permitted only when declared as a different estimand and compared with the appropriate baseline.

## 7. Scope

All verdicts are conditional on the cited frozen experiments. “Closed” means closed for the tested method/signal/action family, not a universal impossibility result for every future algorithm. Conversely, a partial pass does not justify deployment, SOTA, unseen-build, or open-world claims.
