# SIGMOD E&A manuscript and anonymous evidence package

Main document: `main.tex`. Separate short supplement: `appendix.tex`.
The source archive includes compiled PDFs, six vector figures (PDF and SVG),
the ACM class/bibliography style, bibliography, table data, and analysis code.
Historical W1--W6 previews and duplicate sections are not required to compile this version and are excluded from the anonymous export.

## Compile

Upload the archive contents to Overleaf and select `main.tex` as the main
document. Use XeLaTeX with BibTeX (automatic in Overleaf). Switch the main
document to `appendix.tex` to build the independent supplement.

Locally, with Tectonic 0.17:

```
tectonic -X compile main.tex --outdir build --keep-logs
tectonic -X compile appendix.tex --outdir build --keep-logs
```

The class is the supplied ACM `acmart` template, `sigconf,anonymous`, with the
reference block and CCS concepts suppressed for double-anonymous review.
No negative layout spacing, margin reduction, or global body-font reduction
is used. The main PDF and supplement are separate submission files.

## Regenerate tables and figures

Python dependencies: NumPy and Matplotlib (see `requirements.txt`). The delivered
clean replay used Python 3.11.16, NumPy 2.4.6, Matplotlib 3.11.2, and pypdf
6.10.0; PDF libraries are optional for compiling the manuscript.

```
python evidence/replay_graph_only_intervals.py
python make_figures.py
python check_evidence.py
python run_clean_replay.py --package .
```

`make_figures.py` regenerates six PDF/SVG/PNG figures and the TeX table macros
from the packaged CSV/NPZ files. The delivered figures use Times New Roman.
If unavailable, the script announces a DejaVu Serif fallback: inspect the
layout before using that output. PDF metadata timestamps can differ between
runs; numerical reproducibility does not imply byte-identical PDFs.

`replay_graph_only_intervals.py` reconstructs the absolute, reference, and
incremental 95% query-cluster intervals in Table 1 from 3,000 compact
per-query cluster means (750 shared queries for each of four
implementation--dataset blocks). It uses 5,000 seed-991 bootstrap draws and
also verifies the already frozen incremental intervals before writing the
derived four-row table.

`check_evidence.py` independently inverts the binomial CDF for CP bounds,
checks decisions, gains, quantiles, LOTO and costs, and reproduces the crossed
bootstrap intervals. It performs no ANN search or raw-truth access. The
delivered run passes 244 checks; this is not independent native replication.
The separately frozen fresh-query stage passes 210/210 recorded checks. Its
public preregistration summary records the frozen source-policy digest, query-role
counts and digests, lane definitions, and confidence allocation without exposing
host paths or private role-ID arrays.
For each held-out target direction at per-direction `alpha=0.05`, the fresh-stage
audit records B when the one-sided CP upper bound is at most 0.05, A when the
lower bound is above 0.05, and U otherwise. No simultaneous correction is
applied across 552 directions; these labels are descriptive audits rather than
target deployment certificates.
`run_clean_replay.py` verifies the anonymous manifest, both check sets, and
normalized generated-table hashes, then builds the PDFs when a supported
LaTeX engine is available. `qa/S5_CLEAN_REPLAY_PUBLIC.json` records the sealed
replay status without machine-specific paths. The sealed run used Tectonic
0.17.0: the main paper is 11 pages total (references begin on page 10), the
supplement is 3 pages, both are US Letter, and both are below 10 MB.

## Reanalyze the existing native responses (optional; external data required)

The full experiment repository and frozen refresh95 response files are not
bundled in this small manuscript archive. With NumPy and SciPy available:

```
python evidence/reanalyze_review.py --repo PATH_TO_EXPERIMENT_REPOSITORY --replay PATH_TO_REFRESH95_REPLAY
```

This uses `scripts/graph_anns_phase3_ea85/analyze_phase2_refresh95.py` and the
original `results/graph_anns_phase3_ea85/refresh95/per_build.csv` to reproduce
the original decisions before deriving new outputs. It writes only its own
`evidence/w6_audit` directory. It neither builds indexes nor modifies frozen
scientific outputs. See `PROVENANCE.md` for claim-to-source mapping.
The packaged replay script has SHA-256
`ab012e376fa73686fe07bad7498aa6ec928d89d06fef28842ccebd8732dab471`.

## Evidence status and submission boundary

The matched-source diagnostic, crossed uncertainty, joint-error replay, and
completed cost accounting are **post-hoc reanalyses of frozen responses**.
The source-certified slack bridge is a separately preregistered fresh-query
confirmation conditional on the registered builds. TCP remains a recurring-profile
case; its main replay is not a new-query predictor or a 5% build-conformal
algorithm. The stricter CP allocation is per target, not simultaneous across
twenty targets. NDC economics is not wall-clock or monetary economics.

The PDFs contain no identifying repository URL. The anonymous package is built
from an explicit allowlist and scanned for identity, host, and local-path
tokens. Hosting that package at an anonymous, accessible URL and checking the
live submission form remain author submission steps. Do not put a personal
repository URL into the anonymous PDF. The compact numerical package is not a
container for full native replay.

## Files

- `main.tex`, `sections/`: manuscript, definitions, theory, RQ1--RQ9.
- `appendix.tex`: short proofs and complete twenty-target certificate table.
- `figures/`: six PDF/SVG figures, all used in the main paper.
- `evidence/generated_tables.tex`: generated typeset table definitions.
- `evidence/w6_audit/`: compact numerical evidence and validation report.
- `evidence/graph_only_query_clusters.csv` and
  `evidence/replay_graph_only_intervals.py`: compact replay for all Table 1
  marginal risk intervals.
- `evidence/extensions/`: unchanged external-method and scale/family summaries.
- `evidence/s4_fresh/`: compact fresh-query evidence, the 96 frozen source
  actions, a sanitized preregistration summary, and the public protocol.
- `make_figures.py`, `check_evidence.py`, `run_clean_replay.py`: regeneration and checks.
- `PROVENANCE.md`: frozen sources and inference units.
- `ANONYMOUS_PACKAGE_MANIFEST.json`: byte sizes and SHA-256 hashes for the delivered package contents, excluding itself.

ACM template licensing is retained in `ACM-LICENSE` and the template headers.
