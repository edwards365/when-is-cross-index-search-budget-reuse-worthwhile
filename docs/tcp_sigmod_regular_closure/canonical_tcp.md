# Canonical TCP for the SIGMOD closure

## Name and claim boundary

The primary executable method is **TCP-HM9-TC**: stable-tail History-Max over
nine source rebuilds followed by independent Target Certification. It is not
the finite-build conformal order-statistic theorem instantiated at alpha=.05;
with nine source builds that theorem has resolution 0.10. The order-statistic
variant remains a theoretical extension requiring at least 19 qualifying
source builds and is not the primary method in the current matrix.

The certificate produced here is fixed-target query-risk control for one
target build. It is not a guarantee for a future unseen target build and is not
a simultaneous claim over the complete experiment campaign.

## Frozen action and event semantics

Let the ordered action grid be A=(10,20,40,80,120,160,200). For query q and
build g, Z(q,g,a)=1 when Recall@10 at actual efSearch a is below 0.90. Define
the stable-tail label

    B_tail(q,g) = min {a in A: Z(q,g,b)=0 for every b in A with b>=a}.

If the set is empty, B_tail is BOT (+infinity). This differs from the first
observed safe action and remains valid when raw Recall is non-monotone.

For a target build t and query q, TCP-HM9-TC takes the maximum B_tail over the
nine source builds. If any source label is BOT, the query abstains and uses the
fixed-safe endpoint. Unsupported ranks are never clipped to an observed rank.

## Frozen certification sequence

The endpoint efSearch=200 is the preregistered fixed-safe fallback; it is not
selected by scanning target certification results. On the 500 target
certification queries:

1. Test endpoint risk with a one-sided 95% Clopper-Pearson upper bound. If the
   upper bound exceeds 0.05, declare the target undeployable and stop.
2. Only after endpoint acceptance, test the complete TCP policy (including its
   per-query abstentions) with the same bound. If accepted, deploy TCP;
   otherwise deploy the endpoint for every query.

This is a fixed sequence. Evaluation data never select actions, change the
sequence, tune a threshold, or choose a fallback. Evaluation is read only
after the target action has been fixed.

## Query roles

The source-side labels for target certification-role and evaluation-role query
ids are a frozen history cache. They must predate the corresponding target
execution and are hashed separately. This is a repeated-query deployment
setting. Cold queries are not silently dropped: they abstain to the endpoint,
and later experiments vary cache coverage explicitly.

## Required accounting

- Risk denominators include accepted, abstained, and fallback queries.
- Search cost is the ratio of aggregate distance-computation totals; the mean
  of per-query ratios is only a secondary diagnostic.
- Report raw first-safe versus stable-tail differences, BOT rate, target
  certificate failures, evaluation risk, mean/p50/p95/p99, query-pooled tails,
  every target build, LOBO, and largest-benefit deletions.
- Offline source history, exact truth, certification, storage, control, and
  fallback costs remain mandatory before an economic claim.

## Promotion rule

TCP-HM9-TC may advance from fixed-target exploratory evidence only after the
same frozen implementation passes SIFT and repaired Arxiv analysis, the
registered robustness checks, lifecycle-cost accounting, and a prospective
new-query/new-build confirmation. Failure on a dataset may only be excluded by
a deployable applicability gate frozen before that dataset's evaluation.
