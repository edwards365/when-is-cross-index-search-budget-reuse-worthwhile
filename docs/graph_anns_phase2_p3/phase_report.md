
## Execution record (steps 2-3)

- contract_ablation.py built four-tier tables from frozen S3 rows + COMPLETE.json metadata
  (build wall times, per-build index hashes). 16/16 checks after one type-handling fix.
- Key mechanistic finding recorded: D2 (fixed order+seed, 8 threads) yields six distinct
  index hashes - parallel scheduling is a residual nondeterminism source; single-threading
  is necessary and sufficient for byte identity.

## Theory/paper consistency review (step 5)

1. No frozen number modified; D3 zero-variation and 3.52x/1.71x overhead reproduce the
   frozen gate values; the 4.73x/1.86x tier-relative overheads are new derived quantities
   (ratios of frozen medians), labeled descriptive.
2. The paper's "fix the thread count" wording must be strengthened (see optimization 1);
   this is a wording-level change consistent with the frozen evidence.

## Final review closure (step 5, second half)

- Consistency with P2: the prescription ordering (contract > pooling > certify > abstain)
  gains the order-only intermediate rung; no contradiction with the margin finding.
- Handoff §8.2 item 6 (D3 overhead attribution) is now answered with measured ratios.
