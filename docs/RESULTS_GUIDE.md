# Results and evidence guide

This page maps the public claims to their estimands and evidence. It is a navigation aid, not a replacement for the manuscript or provenance ledger.

## Core concepts

**Budget portability** asks whether a policy chosen on one graph rebuild retains its risk/efficiency behavior on another rebuild.

**ICBA (Index-Conditioned Budget Audit)** is the decision framework. It isolates policy construction, target certification, fallback, held-out evaluation, and cost accounting.

**TCP (target-calibrated pooling)** is a recovery policy for recurring queries with frozen historical profiles. TCP is one branch of the ICBA policy ladder, not the definition of ICBA.

Four claims are kept separate:

1. **Portability:** does the old policy retain its behavior?
2. **Qualification:** does target evidence support execution?
3. **Serving-work value:** does an accepted policy save search work or time?
4. **Net economic value:** do savings repay acquisition and control costs over a workload lifetime?

## Claim-to-evidence map

| Claim | Primary evidence | Inference / scope | Canonical entry point |
|---|---|---|---|
| Graph-only rebuilds break budget portability | hnswlib and Faiss on SIFT-100K and Arxiv-Nomic-100K | Registered build panels, grids, and shared query populations | `paper/sigmod2027/sections/portability.tex`; Table 1 compact replay |
| A 5% refresh can cross the 5% risk limit | Frozen recurring-query policy before/after refresh | Two registered 100K datasets; fixed protocol | Paper refresh section and `evidence/w6_audit/` |
| The phenomenon is not TCP-specific | DARTH/Ada-ef bridges, Deep1M, Vamana | Each extension retains its native estimand; not one pooled leaderboard | Paper cross-family section and `evidence/extensions/` |
| ICBA separates safe deployment from attractive but unsafe work savings | CP qualification, independent evaluation, fallback accounting | Per-target/per-decision scope unless explicitly stated | Paper theory/method sections and target decision tables |
| TCP gives endpoint-relative recovery | Recurring-profile target recalibration | Registered histories and target roles | Paper recovery section; Table 2/5 evidence |
| Query conditioning adds resolved incremental value only on SIFT | Same target-label budget audit; TCP also uses frozen histories | SIFT interval positive; Arxiv mean unresolved and p95 worse | Paired baseline audit in the final manuscript |
| Fixed-slack recovery can qualify prospectively | Fresh insertion-permutation builds and disjoint query roles | 112 separately certified target decisions; not simultaneous campaign coverage | `docs/sigmod_s9/S9_3_PROSPECTIVE_ROBUSTNESS_REPORT.md` |
| Runtime gains exist on the recorded machine | Fixed CPU/thread interleaved measurements | One machine setting; wall time does not replace NDC | Final V3 Prime runtime table and S9 reports |
| Recovery has lifecycle boundaries | Cold/cached histories and break-even analysis | Currency and omitted components stated per ledger | Paper economics section and compact ledgers |

The complete file-level mapping is in [paper/sigmod2027/PROVENANCE.md](../paper/sigmod2027/PROVENANCE.md).

## Headline numbers and how to read them

- **17.17--23.60 pp:** additional query failure from transferred first-passing actions relative to target-specific references. This is portability evidence, not a claim that every transfer fails.
- **44.39% / 29.86%:** endpoint-relative mean-NDC reduction from TCP under the reported qualification contract. This is not automatically incremental value over every target-only policy.
- **112/112:** fixed target decisions that separately qualify on the prospective panel. It is not a simultaneous 112-decision guarantee.
- **51.35% / 30.13%:** measured wall-time reduction on one fixed CPU setting. Hardware generalization remains outside this measurement.

## Positive, negative, and boundary evidence

The repository deliberately retains results that narrow the method:

- early resistance-specific rewiring did not establish ANN benefit;
- raw stage order was not a valid ordered budget ladder;
- some recovery routes were dominated by fallback cost;
- TCP's incremental query-conditional value was not resolved on Arxiv-Nomic;
- simple fixed or target-global policies can match or beat more complex recovery arms;
- Vamana and cross-family extensions do not share one common estimand.

These are part of the scientific contribution: ICBA is designed to reject unjustified reuse and unnecessary complexity.

## Canonical paper and artifact

- Main manuscript: [Final V3 Prime](../paper/sigmod2027/ICBA_SIGMOD_EA_FINAL_V3_PRIME.pdf)
- Appendix: [Final V3 Prime appendix](../paper/sigmod2027/ICBA_SIGMOD_EA_FINAL_V3_PRIME_appendix.pdf)
- Source archive: `paper/sigmod2027/ICBA_SIGMOD_EA_FINAL_V3_PRIME_SOURCE.zip`
- Artifact entry point: [artifacts/graph_anns_phase3_ea85](../artifacts/graph_anns_phase3_ea85/README.md)
- Anonymous package manifest: `paper/sigmod2027/ANONYMOUS_PACKAGE_MANIFEST.json`

## What this repository does not claim

- universal failure of budget transfer;
- absolute SOTA over every adaptive ANN method;
- one campaign-wide 95% guarantee unless a simultaneous contract is explicitly allocated;
- that NDC and wall time are interchangeable;
- that serving-work savings imply lifecycle profit without the corresponding ledger;
- that retrospective labels are deployment inputs.
