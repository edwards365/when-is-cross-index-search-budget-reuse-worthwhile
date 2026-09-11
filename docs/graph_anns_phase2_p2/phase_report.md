# Phase P2 report — constructive closure (handoff Phase B, review items E1+max-over-source)

## Goal

Fill the paper's biggest gap: a constructive decision table computed purely from frozen
per-query records. Three deliverables:

1. **max-over-source robust baseline** (B1): a_robust(q) = max_s B_s(q) over the 23 source
   builds; evaluated on every target. Answers "does conservative source pooling already
   solve transport risk at finite cost?"
2. **Six-method certification table** (B2): naive source transport / max-over-source /
   frozen-action CP certification (M=1, m=59) / target select-then-certify (selection on
   disjoint queries, Bonferroni-48 certification) / maximum registered action /
   per-query oracle — risk, cost (DistComp where estimable), tails, certification outcome.
3. **Five-condition instance table** (B3): per target build, the Theorem-2 conditions
   (feasibility, identifiability, margin, independent evidence, fallback) each marked
   satisfied/failed with evidence — full instances or transparent failures.

## Frozen design decisions

- Quality event: hit_count >= 10 of 10 (h=10 semantics; ceil(10*tau)=10 for tau=.95/.99).
- hnswlib per-query source: /home/wlk/data500/graph_anns_e4/raw/<build>/queries.csv.gz
  (ef grid 10/20/40/80/120/200; NDC from latency_round 0; evaluation queries = 750 per
  dataset via results/graph_anns_e4_reanalysis/query_role_mapping.csv).
- Faiss per-query source: /home/wlk/data500/graph_anns_iclr_phase1_1_repair_scratch/
  faiss_100k/raw/*.csv.gz (ef grid 16/32/64/128/256/512; rows are the 750 clean queries;
  DistComp NOT_ESTIMABLE).
- Policy semantics (policy level, distinct from the registered estimand): deploy a(q);
  when the policy's own rule yields no finite action, primary variant ABSTAINS, secondary
  variant deploys the maximum registered action; both reported, never mixed.
- Certificates: zero-failure Clopper-Pearson; M=1 -> m=59; Bonferroni over the 48-target
  family uses the stored cp_ucb_bonferroni_48 convention; select-then-certify splits the
  750 evaluation queries per target into disjoint selection (375) / certification (70) /
  evaluation (305) roles (retrospective replay, seed 991) and is labeled RETROSPECTIVE.
- Bootstrap: query bootstrap, 5000 reps, seed 991, full directed-pair vectors retained.

## Constraints

- Pure code; no ANN search; frozen trees read-only; no estimand reinterpretation.
- Results are conditional on registered builds; no open-world claim.

## Deliverables

results/graph_anns_phase2_p2/{max_over_source.csv, six_method_table.csv,
five_condition_instances.csv, decision_manifest.json}; scripts; tests.

## Execution record (steps 2-3)

- max_over_source.py: four cells (hnswlib/Faiss x SIFT/Arxiv), 24 targets each. Headlines:
  naive k=1 reproduces the registered main results (0.2237/0.1838/0.2367/0.1793 - closes
  the loop with frozen tables); pooling-22 risk 0.09-0.92% (all CI upper bounds < 1.1%),
  DistComp 1.34-1.45x oracle (hnswlib), abstention 0.5-2.7%, LOBO max 2.1%; Faiss DistComp
  NOT_ESTIMABLE (batch-cumulative counter). k-ladder measured for k=1..22.
- certification_table.py: M1-M6 per target. M3 certify probability 0.63/0.47 (100 draws);
  M4 point-screen certifies 0/48; M4b Theorem-2 screen selects ef=120 (8/24) or ef=200
  (16/24) and certifies 0/48 - margin failure; M5 risk 0.8-1.3% at 4.09-5.14x; M6 oracle
  risk = endpoint mass only.
- five_condition_table.py: 48 targets, zero complete positive instances; first failed
  condition = c3_margin on all 48.
- Two process-review fixes were applied (retry 0->1): M4b screen corrected from an
  impossible p_cert threshold to Theorem-2 semantics (selection-block CP-UB, alpha=0.025);
  M2 dominance re-evaluated under the four-outcome semantics (overall unsafe-execution
  probability including abstention). Framework unchanged; outputs regenerated; 27/27 checks.

## Theory/paper consistency review (step 5)

1. The new constructive table does not touch the frozen primary estimand: M1 reproduces
   the registered numbers exactly (validates the replay), and M2-M6 are policy-layer
   quantities labeled RETROSPECTIVE_REPLAY_PURE_CODE. No estimand reinterpretation.
2. Consistency with Theorem 2: the measured c3_margin failure is consistent with, and now
   empirifies, the theorem's stated prerequisite; the paper must NOT claim "certification
   is impossible" - only that the registered grid offers no margin-separated action.
3. Consistency with ICBA's four outcomes: pooling's abstention variant maps cleanly onto
   the abstain outcome; the max-action variant's residual risk (0.8-1.3%) matches the
   M5 row, so the paper's "max registered action is not automatically safe" sentence now
   has exact per-target support.
4. Abstract/intro numeric ranges (17.17-23.60% etc.) remain untouched; the constructive
   table enters as new results, old numbers unchanged.
