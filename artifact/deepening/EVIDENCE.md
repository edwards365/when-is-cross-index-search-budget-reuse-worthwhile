# Unified paper and P0–P11 evidence entry

Use the fixed [artifact-deepening-v2 release](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-deepening-v2), its asset hashes and the [runbook](README.md). Every path in the following added-analysis rows resolves from the extracted `deepening-bundle` root. Individual stage commands run from `p0-p10/` with a new output path; stage dependencies must precede dependents. The umbrella command executes them in order.

| Stage / paper use | Inputs and configuration | Execution / independent check | Expected result |
|---|---|---|---|
| P0: non-singleton contribution, IV-D | `p0-p10/configs/p0.json`, saved SIFT/Arxiv response arrays | `python rebuild.py --stage p0 --output ../run`; separate scalar grouping | `p0-p10/expected/p0/{per_query,per_target}.csv` |
| P1: actual versus stable-tail cost | `p0-p10/configs/p1.json`, same targets and retained sets | `--stage p1`; separate optimizer | `expected/p1/objectives.csv`, `endpoint_diagnostics.csv` |
| P2: Deep1M mechanism replication | `configs/p2.json`, saved Deep roles/action rows | `--stage p2`; separate reader/optimizer | `expected/p2/objectives.csv`, `attribution.csv` |
| P3/P3b: role-separated mapping and target calibration | `configs/p3.json`, `p3b.json`; three disjoint roles | `--stage p3`, then `p3b`; scalar models and binomial checks | Models, support, qualification locks and per-query/target results |
| P4: native SIFT100K degree conditions | `configs/p4.json`, saved 16-graph native responses | `--stage p4`; separate optimization/decisions | Objectives, contribution, paired-M and deployment files |
| P5/P6: hierarchical rule and support sensitivity | `configs/p5.json`; Deep and P4 responses | `--stage p5`; support 1/2/5/10/20 is part of this stage | Paths, models, locks, work/failure points and support summary |
| P7: path/support/selection attribution | `configs/p7.json`, P5 mappings and response records | `--stage p7`; per-query scalar reconciliation | `decomposition.csv`, support/path/overlap files |
| P8: construction-effort conditions | `configs/p8.json`; 24 graph records including reused EC200 | `--stage p8`; raw-file and independent optimizer checks | Paired construction, objectives, contribution and deployments |
| P9: feasibility and minimizing-action chains | `configs/p9.json`; 56 unique targets in seven conditions | `--stage p9`; separate reachable-action/cost checks | Full/retained classifications, cells and witnesses |
| P10: boundary-tie diagnostics | `configs/p10.json`; returned IDs/distances and exact boundary distances | `--stage p10`; scalar tie scores and chain checks | 384 cases, hits, changed events and graph classifications |
| P11: tie cost and relearning, IV-D/V | `p11/config.json`; P4/P5/P8/P10 inputs, all 32 added graphs | Umbrella command; cost/check then learning/check | All 14 files in `p11/expected/`, including objectives, attribution, models, locks, support and fixed scores |
| Finite theoretical conditions, IV-C | `docs/theory_conditions.md`, `docs/p9_theory.md` | `p0-p10/rebuild_theory.py`; finite examples complement the proofs | `p0-p10/expected/theory` and checked theoretical notes |

Except where `p0-p10/` is written explicitly, `configs/` and `expected/` in P0–P10 rows are relative to that component. The bundle's `docs/claims.csv` supplies exact root-relative paths for the 23 current claims, including unsupported upgrades and unresolved million-scale ties. Native source/header pins describe earlier measurement provenance; the default reconstruction has no native search or compiler step.

## Original paper figures and measurements

| Result | Fixed public path | Connection to current manuscript |
|---|---|---|
| Figure 1, six editable figures | `artifact-delivery-v1` figure package | Frozen presentation sources; current six PDF hashes in release manifest |
| Figures 2/4, original paired intervals | `artifact-paper-v2`, paper/narrative runbooks | Same original statistical estimands and saved-response layers |
| Figure 3 original two-dataset optima | `artifact-response-v1`, nine-table reconstruction | Added P0/P1/P11 provide separate attribution and sensitivity records |
| Figure 5 and Table III ledger | `artifact-paper-v2` plus response-v1 cost records | Original History-Max accounting, not a new learned-policy lifecycle |
| Figure 6 memory and lookup | `artifact-paper-v2` saved measurement records | Original static lookup path and measurement boundaries |
| New original-protocol execution | `artifact-delivery-v1` execution-entry package | Source/config/access routes; full-scale repeat execution is separate |

The [previous whole-paper map](../EVIDENCE.md) retains every original result's input layer and remaining measurement boundary. The new release adds the mechanism evidence and a bound manuscript snapshot; it does not turn historical missing provenance into a new measurement.
