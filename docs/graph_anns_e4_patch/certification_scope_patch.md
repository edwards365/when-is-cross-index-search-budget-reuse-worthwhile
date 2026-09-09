# Certification scope patch

Per-target action selection uses alpha=0.05/6. Fixed ef=120 across the 48 registered targets uses alpha=0.05/48. The all-target/all-action family uses alpha=0.05/(48×6). The selected action distribution remains SIFT 24/24 ef=200 and Arxiv 23/24 ef=200 plus 1/24 ef=120. Some ef=200 fallback sentinel certificates fail, so no universally certified fallback exists; the correct status is `ABSTAIN_NO_CERTIFIED_ACTION`, preserving deployment label `NO_DEPLOYABLE_VALUE`.
