# Saved-record reconstruction for paper figures

This entry complements `artifact-response-v1`; it does not replace that frozen release. It reconstructs Figure 2 statistics, Figure 4 operating points and paired intervals, Figure 5 model curves, and Figure 6 batch-lookup means. Figure 3 and Table III's detailed fixed-cost components use the existing nine-table response entry.

## Run

Use Python 3.12 with the versions in `artifact/requirements-analysis.txt`. All inputs for this entry are small files in this checkout; no Release asset or private host access is needed.

```sh
python -m pip install -r artifact/requirements-analysis.txt
python artifact/reproduce_paper.py --check-inputs
python artifact/reproduce_paper.py --output paper-reconstruction
```

The output directory must be new and outside `artifact/`. To reconstruct one part, add `--parts F04` (or F02, F05, F06). A failed run retains `failure.json`; do not overwrite it to conceal failure. The numerical tolerance is relative `1e-10`, absolute `1e-9`. Schemas, memberships, covered cells and input identities are checked separately. An output match means reproduction from the stated saved-record level, not independent original measurement.

## Inputs, computation and outputs

| Result | Saved input | Computation | Generated output |
|---|---|---|---|
| Figure 2 | `inputs/graph_only_query_clusters.csv`: 750 shared query clusters for each of four dataset/implementation blocks, all 552 directions already averaged per query | 5,000 query-cluster draws, seed 991; each draw shared across transfer/reference/difference; conditional on the registered graphs | `F02_intervals.csv`: 12 means and their 12 intervals |
| Figure 4 | `inputs/sift_paired.npz`, `arxiv_paired.npz`: locked-policy 8-target by 1,000-query matrices | Means, 5,000 crossed target/shared-query draws per contrast, seed 991, and leave-one-target-out checks | `F04_operating_points.csv`, `F04_paired_intervals.csv`: ten points and 24 paired intervals |
| Figure 5, overhead boundaries | `inputs/component_ledger.csv` | At Q=1,000, compute B, D, B−VD, first strict integer repayment and D/8,000 per-request boundary | `F05_curves.csv`, `F05_overhead_boundaries.csv` |
| Figure 6 | `inputs/cache_raw_blocks.csv` and `cache_memory.csv` | Mean of seven recorded batch-time-per-lookup values per cell; select 100-round cyclic cells; convert saved object-size bytes to decimal MB | `F06_lookup_means.csv`, `F06_plotted_values.csv` |

The graph-only input is a sufficient compact record for the reported query-cluster estimator, not the complete action-by-query response grid. Figure 4 matrices retain method pairing; `search_ns` is already the arithmetic mean of seven API-time repeats. This entry does not rerun selection/qualification or reconstruct the original seven timing records. Figure 6 reconstructs batch means, not pooled per-call p95/p99. Object memory is a saved measurement, not an object-size remeasurement on a different Python implementation. Figure 5 is ledger arithmetic, not repeated deployment measurement.

## Exact statistical recipe

Figure 2 uses NumPy `default_rng(991).integers(0,750,(5000,750))` separately in each dataset/implementation block. Figure 4 resets `default_rng(991)` for each paired contrast, draws multinomial target and shared-query weights in chunks of 100, and computes their product-weighted mean. Chunk size is part of the random-number sequence. Both use NumPy's default linear quantiles at .025 and .975. Units remain probability, native distance counts and nanoseconds in paired outputs; Figure 4 applies percentage-point, thousand-count and millisecond conversions at display time.

One library thread is requested before importing NumPy. The bounded inputs total less than 1 MB; expected working memory is below 512 MiB. This is a planning estimate, not an enforced process quota or benchmark. No index construction, ANN query, raw truth acquisition, cache timing or old worker is invoked. Original records are read-only; outputs are written to a new directory.

## Provenance and remaining scope

The two paired NPZs and cache block CSV match the original completed E1/E2 receipt hashes. The other inputs are byte-preserved saved records. `manifest.json` pins the exact inputs and expected outputs. An initial local adapter check caught the use of the shorthand `TCP_dedup` where the retained curve file uses `TCP_deduplicated`; the adapter was corrected without changing data. The clean-export verification records the corrected implementation.

These files are project-generated numeric responses and aggregates, without vectors, source documents or indexes. They follow the repository license; upstream data and implementation licenses remain separate. Consult [the complete coverage map](../EVIDENCE.md) for narrative results and original-execution paths still missing from this release. Do not describe this entry as complete paper reproduction.
