# S9-4 Equal-Information Baselines, Ablations, and Failure Attribution

## Decision

S9-4 closes with
`ICBA_VALUE_CONFIRMED_SIMPLE_BASELINE_DOMINATES_SOURCE_SLACK_TARGET_RECALIBRATION_STRONGEST`.
The audit contribution remains supported, but the source-derived one-rung slack
rule is not a uniquely necessary recovery method on this panel. A certified
fixed action at `efSearch=256` exactly matches it on SIFT-100K and materially
outperforms it on Arxiv-Nomic-100K. Target-side recalibration is the strongest
deployable route, with the 1,000-label arm strongest overall and the matched
500-label arm positive but more variable because it falls back on 7/56 cells.

## Frozen protocol and integrity

The protocol, roles, and arm definitions were frozen before response replay.
Each dataset uses three disjoint 500-query roles drawn from the registered
training population: target selection, certification, and evaluation. All
pairwise role overlaps and all overlaps with external frozen roles are zero.
The role-manifest digest is
`0da5625ffebcbdbc4f9733837c46e4edf1ba66813ab4198555a8aa573688303f`.

The replay reuses the 16 hash-verified prospective S9-3 indexes (eight per
dataset) and evaluates 144,000 response cells. Reload equivalence is exact for
top-10 IDs and NDC. Fixed-machine timing uses one pinned CPU, one search thread,
50 warmups, and seven interleaved repetitions. Across 20,500 checked queries,
top-10 mismatch count is zero. Median/max timing CV is 0.0096/0.0176 on SIFT
and 0.0059/0.0125 on Arxiv.

## Deployable-arm results

All confidence intervals are 95% crossed target-build-by-query intervals; wall
time is measured against the registered `efSearch=512` endpoint. LOTO is the
minimum wall-time gain after deleting one target build.

| Dataset | Arm | Eval risk | Wall gain [95% CI] | p95 ratio (CI upper) | LOTO min | Decision |
|---|---|---:|---:|---:|---:|---|
| SIFT-100K | fixed-256 certified | 0.400% | 51.93% [51.20, 52.79] | 0.515 (0.525) | 51.61% | pass |
| SIFT-100K | source one-rung certified | 0.400% | 51.93% [51.20, 52.79] | 0.515 (0.525) | 51.61% | pass |
| SIFT-100K | target-global, 500 labels | 0.350% | 45.33% [32.48, 52.00] | 0.834 (0.930) | 44.26% | pass |
| SIFT-100K | target-global, 1,000 labels | 0.725% | 54.53% [51.20, 60.56] | 0.513 (0.524) | 51.61% | pass |
| Arxiv-Nomic-100K | fixed-256 certified | 0.400% | 43.64% [43.33, 43.97] | 0.563 (0.574) | 43.57% | pass |
| Arxiv-Nomic-100K | source one-rung certified | 0.307% | 32.73% [31.09, 34.55] | 0.868 (0.891) | 32.05% | pass |
| Arxiv-Nomic-100K | target-global, 500 labels | 0.925% | 46.81% [30.36, 60.54] | 0.763 (0.921) | 43.96% | pass |
| Arxiv-Nomic-100K | target-global, 1,000 labels | 2.225% | 66.47% [66.20, 66.74] | 0.340 (0.346) | 66.43% | pass |

The registered safety threshold is 5%. Every deployable arm passes safety,
mean-wall, p95, LOTO, and timing-stability gates on both datasets. The endpoint
arm remains safe but has no efficiency value by construction.

## Component attribution

1. **Source action versus one-rung shift.** The one-rung shift reduces held-out
   risk from 2.15% to 0.40% on SIFT and from 1.775% to 0.307% on Arxiv, but it
   sacrifices 24.92 and 31.21 percentage points of NDC gain, respectively.
   This is a safety-efficiency trade, not free recovery.
2. **Certification.** In this panel every fixed-256 and source-slack candidate
   is accepted, so certification changes authorization rather than the executed
   outcome. Its value is procedural safety, not an additional speedup.
3. **Fixed-action sufficiency.** Fixed-256 and source slack are identical on
   SIFT. On Arxiv, fixed-256 improves wall gain by 10.91 percentage points and
   NDC gain by 12.46 points. Hence source-side tailoring is not necessary here.
4. **Equal-information target selection.** The matched 500-label arm uses
   250 selection and 250 certification queries. It passes all gates but accepts
   49/56 cells and falls back on 7/56 on each dataset. It loses 6.60 wall-gain
   points to source slack on SIFT but gains 14.08 points on Arxiv. This is a
   deployable, label-matched alternative with visible fallback variance.
5. **Label-rich target selection.** With 500 selection plus 500 certification
   labels, target recalibration is strongest: +2.59 wall-gain points over source
   slack on SIFT and +33.74 on Arxiv. It is not an equal-information comparison.
6. **Oracle headroom.** The evaluation oracle shows remaining SIFT headroom,
   while the Arxiv label-rich target arm reaches the oracle action pattern on
   this panel. Oracle results remain nondeployable diagnostics.

## External-method context

DARTH and Ada-ef are retained at their native estimands. Their raw policies
show 22.55%/23.12% and 9.52% risk, respectively; audit/fallback reduces risk to
0.97%/1.10% and 0.60% but yields no audited efficiency gain in those native
experiments. Earlier target recalibration recovers 44.39% and 44.79% NDC on the
two registered hnswlib refresh panels. These rows are contextual evidence, not
an unmatched leaderboard. ConANN and ANNiE are explicitly `NOT_EXECUTABLE` from
the available frozen code and are not assigned synthetic results.

## Claim consequences

S9-4 strengthens the paper's central audit claim and narrows the recovery claim.
The paper should center ICBA as the method for distinguishing unsafe efficiency,
certified deployability, and economic value; present target recalibration as the
strongest supported recovery route; treat fixed-256 as the necessary simple
baseline; and demote source slack to a boundary ablation rather than a unique
algorithmic contribution. A claim that source-slack is required would be false
on this evidence.

## Limits

This is a paired baseline/ablation audit on the frozen S9-3 prospective build
panel, not a second independent build campaign. It covers eight builds per
dataset and one fixed CPU configuration. The 1,000-label arm is intentionally
not equal-information. External methods use native events and implementations,
so they support scope and failure attribution rather than a rank ordering.
