# Retrospective cross-fit report

The replay covers 12 directed source-to-target pairs and five folds per pair. Each fold freezes one fixed action on 600 selection queries, pseudo-certifies selected and fallback actions on 200 disjoint queries, and evaluates once on the remaining 200 queries. Oracle use is pair-level and evaluation-only. Evidence scope is RETROSPECTIVE_CROSSFIT.

{
  "decisions": 60,
  "deployed_action_counts": {
    "A5": 32,
    "A6": 24,
    "A1": 4
  },
  "outcomes": {
    "SAFE_ACCEPTANCE": 36,
    "SAFE_BUT_REJECTED": 24
  },
  "future_confirm_accessed": false,
  "evidence": "RETROSPECTIVE_CROSSFIT"
}
