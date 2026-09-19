# SIGMOD E&A manuscript and compact evidence package

The canonical review build is:

- [Final V3 Prime main paper](ICBA_SIGMOD_EA_FINAL_V3_PRIME.pdf)
- [Final V3 Prime appendix](ICBA_SIGMOD_EA_FINAL_V3_PRIME_appendix.pdf)
- `ICBA_SIGMOD_EA_FINAL_V3_PRIME_SOURCE.zip`
- `FINAL_V3_PRIME_DELIVERY_SHA256.txt`
- `qa/FINAL_V3_PRIME_READINESS.json`

The public project title is **ICBA: Auditing Search-Budget Portability Across Graph-ANNS Rebuilds**. Historical W1--W6 and intermediate final builds remain for provenance but are not the recommended reading path.

## Build from source

Upload the source archive to Overleaf and select the corresponding main document. The manuscript uses the ACM `acmart` template in anonymous `sigconf` mode. The main paper and appendix are separate submission files.

With Tectonic 0.17:

```bash
tectonic -X compile main_final_v3_prime.tex --outdir build --keep-logs
tectonic -X compile appendix_final_v3_prime.tex --outdir build --keep-logs
```

If local filenames differ inside the delivered source archive, use the manifest/checklist in that archive as the authority.

## Regenerate compact evidence, tables, and figures

Python dependencies include NumPy and Matplotlib (see `requirements.txt`). The sealed clean replay records exact versions in its readiness report.

```bash
python evidence/replay_graph_only_intervals.py
python evidence/check_postseal.py
python make_figures.py
python check_evidence.py
python run_clean_replay.py --package .
```

These steps reconstruct compact statistics and manuscript products. They do not rebuild ANN indexes or access unbundled reserved truth.

## What the checks cover

- Query-cluster intervals for graph-only portability.
- One-sided Clopper--Pearson qualification logic.
- Decision, gain, quantile, LOTO, deletion, and cost checks.
- Source-only fresh-query and post-seal target-certified stages.
- Deep1M crossed target/query intervals and tail checks.
- Anonymous-package manifest, normalized generated-table hashes, and PDF build when a supported engine is available.

See [PROVENANCE.md](PROVENANCE.md) for the frozen claim-to-source map and `ANONYMOUS_PACKAGE_MANIFEST.json` for package contents.

## Full native replay

The full experiment repository and large response/index files are not bundled in the manuscript package. The repository-level artifact provides a gated path:

```bash
bash ../../artifacts/graph_anns_phase3_ea85/run_artifact.sh full-check
ICBA_FULL_REPLAY_ACK=YES bash ../../artifacts/graph_anns_phase3_ea85/run_artifact.sh full
```

Read `../../artifacts/graph_anns_phase3_ea85/full_replay.md` before running it.

## Evidence boundary

- Matched-source diagnostics, crossed uncertainty, and cost reconstructions are identified as reanalyses where applicable.
- Fresh source-only and target-certified stages use frozen candidates and disjoint registered roles.
- Per-target/per-decision certificates are not simultaneous campaign certificates.
- TCP is a recurring-profile recovery route, not a universal build-conformal algorithm.
- NDC, wall time, serving-work savings, and lifecycle value remain distinct quantities.
- The anonymous package is compact evidence, not a container for every native experiment.

The PDFs intentionally contain no personal repository URL. Anonymous hosting and the live submission form are author submission steps.

## Directory guide

- `sections/`: manuscript sections.
- `figures_v3/`: current PNG/PDF/SVG figures.
- `evidence/`: compact evidence, registrations, generated tables, and checks.
- `qa/`: readiness and clean-replay reports.
- `PROVENANCE.md`: frozen sources and inference units.
- `ANONYMOUS_PACKAGE_MANIFEST.json`: delivered package file sizes and SHA-256 hashes.
- `FINAL_V3_PRIME_DETAIL_CHECKLIST.md`: final content and formatting checks.

ACM template licensing is retained in `ACM-LICENSE` and the template headers.
