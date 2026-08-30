# Executive brief

The fixed-target autopsy finds a mixed certification-rejection and fixed-safe fallback bottleneck. Safe-but-rejected episodes are material, but unsafe acceptance is also nonzero. Perfect certification and cheap fallback restore mean value only as nondeployable upper bounds. The candidate stage ladder is not ordered, so ordered recovery is not authorized.

## Decision

Final label: `MIXED_CERTIFICATION_AND_FALLBACK_BOTTLENECK`. Ordered-policy assumption: failed. Method implementation: not authorized. Recommended pivot: Stable-by-Construction, while separately improving independent certification and designing a deployable intermediate fallback.

## Gate

Safety fails due to nonzero unsafe acceptance; Tail fails on both datasets; Efficiency fails on SIFT; Fallback and Deployability fail because no deployable intermediate fallback exists and only Oracle upper bounds restore joint value.
