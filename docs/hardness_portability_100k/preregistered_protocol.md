# Query Hardness Is Not Portable — 100K preregistration

Status: frozen before any 100K HNSW query. Parent evidence is OCGT-v3 commit `0d490fecb655bf0345186a137f2ba2d5ee6287d6` and is read-only.

Three fixtures use the first 100,000 vectors of the frozen `train` member as base. Each has 1,000 distinct scale-dev queries sampled from train IDs at or above 100,000 with seed 20260915 (dataset offset only), excluding the frozen Gate-A/OCGT-v2 query source IDs; OCGT-v3 query IDs lie below 100,000 and are excluded by range. No `test`, `neighbors`, or `distances` HDF5 member is opened. Exact top-10 is computed against the 100K base after the frozen normalization rule. The outcome-independent split is 250 train-design and 750 confirmatory-audit queries.

The only core graph family is Original HNSW with M=16, efConstruction=100, k=10, seeds 43/59/71 and random, LID-ascending, LID-descending insertion orders. The random permutation seed is 20260915 and the same permutation is reused across graph seeds. Search ef is fixed to 10,16,24,32,48,64,96,128,192,256,384,512. Primary recall target is 0.90 and sensitivity target is 1.00; primary difficulty is stable sufficient ef.

Gate R runs seed 43 for all three datasets and three orders over every query and ef. Native and non-invasive instrumented runs must have identical top-10 labels, Recall, exact NDC and graph hash, no missing cells, and deterministic repetition. Any unexplained mismatch yields `INVALID_100K_REPRODUCTION_FAILURE` and the core matrix is forbidden until the complete gate is rerun after a documented repair.

After Gate R, the core matrix is exactly 27 graphs and 324,000 query-ef rows. Paired query bootstrap uses 5,000 replicates, seed 991 and 95% intervals. Gates and their order are frozen in the machine-readable preregistration. Oracle, Conditionality, or Portability failure immediately prevents realistic-history and later expensive stages. No results may add an ef, query, seed, order, feature, or tune a parameter.

The disk stop line is 10 GiB. Graphs and temporary materializations must be deleted after durable metrics, invariants and hashes are written. Formal-test remains sealed.
