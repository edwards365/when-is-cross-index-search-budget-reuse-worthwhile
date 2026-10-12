# P8 verification portability correction

Prepublication snapshot `artifact-deepening-v1` retained an exact string comparison between the P8 EC200 qualification bounds and saved P5 values. In Python 3.11.17 on Ubuntu 24.04, the candidate upper bound was `0.017433673725913514`; the saved Windows value was `0.017433673725913517`. The 3.5e-18 difference stopped the checker despite lying far inside the already declared numerical comparison tolerance.

Failed runs [38206038241](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/actions/runs/38206038241) and [38206289135](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/actions/runs/38206289135) remain identifiable. They passed P0/P1/P2/P3/P3b/P4/P5/P7 before P8 stopped. No failed result is labeled as a full pass.

The exported P8 checker changes the historical EC200-to-P5 comparison for `candidate_ucb` and `endpoint_ucb` to its existing numeric `close` function (absolute tolerance 1e-9, relative tolerance 1e-11). All other fields remain exact. The outer expected-output comparison retains absolute tolerance 1e-9 and the stricter relative tolerance 1e-12, recording every nonzero difference. Optimizers, safe sets, fitting rules, support, query roles, decisions and data are unchanged.

`PROVENANCE.json` and the component `SOURCE_PROVENANCE.json` identify the original checker hash, the earlier portable hash and this export hash. The publication candidate uses a new fixed tag rather than moving v1. Its independent checks and comparison receipt establish the actual result after this correction.
