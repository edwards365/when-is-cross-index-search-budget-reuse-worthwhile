# Phase II formal-test firewall

Status: **SEALED**. No Phase II formal test query has been loaded or evaluated.

## Roles

| Role | Permitted use | Forbidden use |
|---|---|---|
| Construction vectors | Build HNSW, candidate pools, local reference graphs, LID order, Geometry, resistance | Acting as a formal query set selected for favorable performance |
| Development queries | Correctness, epsilon choice, numerical tolerance, runtime budget | Confirmatory claims or post-hoc dataset/method screening |
| Formal test queries | One frozen evaluation after all gates pass | Candidate selection, weights, epsilon, subsets, failure mining, metrics, or code changes |

Ground-truth neighbors inherit the role of their query split. Formal ground truth is
sealed with formal queries. Trace data and failed-query labels can never enter GGR.

## Filesystem controls

Downloaded archives and generated arrays must carry a manifest role of `construction`,
`development`, or `formal_test`. Formal-test paths are not accepted by development
commands. A Phase II runner must require an explicit `--formal` gate plus a committed
configuration hash; ordinary local runs default to development data only. Logs record
manifest checksum, split role, Git commit, hardware id, seed, order, method, and PID.

Merely downloading an archive that physically contains several splits is not test
access. Reading, summarizing, tracing, scoring, or evaluating the formal query/ground-
truth members is test access and is prohibited while this firewall is sealed.

## Opening checklist

The firewall may open exactly once for the main run only after:

- `phase2_v1.md`, `phase2_v1.yaml`, and this file are SHA-256 hashed and committed;
- the development epsilon amendment and main config are SHA-256 hashed and committed;
- dataset source/license/checksum manifests are complete and verified;
- GGR has no query-bearing API and its unit/integration tests pass;
- the five methods, five seeds, two orders, search grid, metrics, and statistics remain
  those preregistered;
- `reports/phase2_status.md` records the authorizing commit and declares the opening.

After opening, unexpected engineering failures may be repaired only with a documented
incident and rerun of all affected methods. Outcome-driven algorithm or parameter
changes create a new exploratory study, not a replacement confirmatory result.
