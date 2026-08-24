# Post-E0 D0-E/F counterfactual and oracle add-back result

Machine decision: `FAILURE_STRUCTURALLY_DIFFUSE`.

The decision uses the frozen 25%/80%/50% thresholds. Conservatively, each dataset must pass in at least two of three build seeds; this operational aggregation rule was committed before inspecting the generated curves.

| Dataset | Passing seeds | Decision |
|---|---:|---|
| sift_10k | 0/3 | FAIL |
| glove100_10k | 0/3 | FAIL |
| arxiv_nomic_10k | 0/3 | FAIL |

These are oracle-supervised diagnostic counterfactuals, not a deployable algorithm and not evidence that E0 passed. No validation-dev or formal-test members were accessed.
