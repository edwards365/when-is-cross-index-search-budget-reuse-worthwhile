# Open-world failure decomposition

This phase uses frozen replay summaries only. It is descriptive and non-causal.

The frozen evidence identifies two varying factors: environment inclusion
(closed-world versus leave-one-build-out) and endpoint scope (all graphs versus
certified-feasible graphs). The source policy is always the per-query source
stable-budget Oracle, and target information is always a labeled target
sentinel. Consequently, deployable-source and unlabeled/no-target-information
contrasts are `NOT_IDENTIFIABLE_FROM_FROZEN_DATA`; they are not imputed as zero.

`factorial_cells.csv` contains every calculable dataset-by-implementation cell,
including one-sided exact risk bounds and censoring counts. The decomposition
tables report endpoint and environment contrasts and their interaction. These
are Shapley-compatible only over the identifiable two-factor subgame; a full
four-factor Shapley attribution is not identified by the frozen design and is
therefore withheld.

The principal interpretation remains that endpoint control does not remove the
open-world excess risk. Since the successful lane additionally requires target
labels and a source Oracle, the frozen data cannot establish deployable recovery.
