# Reorganized SIGMOD E&A manuscript

Main document: `main.tex`. Separate short supplement: `appendix.tex`.
The source archive includes compiled PDFs, six vector figures (PDF and SVG),
the ACM class/bibliography style, bibliography, table data, and analysis code.
Historical W5/W5.5 drafts are not required to compile this version.

## Compile

Upload the archive contents to Overleaf and select `main.tex` as the main
document. Use XeLaTeX with BibTeX (automatic in Overleaf). Switch the main
document to `appendix.tex` to build the independent supplement.

Locally, with Tectonic 0.17:

```
tectonic -X compile main.tex --outdir build --keep-logs
tectonic -X compile appendix.tex --outdir build --keep-logs
```

The class is the supplied ACM `acmart` template, `sigconf,anonymous,nonacm`.
No negative layout spacing, margin reduction, or global body-font reduction
is used. The main PDF and supplement are separate submission files.

## Regenerate tables and figures

Python dependencies: NumPy and Matplotlib (see `requirements.txt`). The delivered
regeneration/validation used NumPy 2.3.5 and Matplotlib 3.11.2. PDF QA used
`pypdf` 6.10.0 and `pypdfium2`; they are optional for compiling the manuscript.

```
python make_figures.py
python check_evidence.py
```

`make_figures.py` regenerates six PDF/SVG/PNG figures and the TeX table macros
from the packaged CSV/NPZ files. The delivered figures use Times New Roman.
If unavailable, the script announces a DejaVu Serif fallback: inspect the
layout before using that output. PDF metadata timestamps can differ between
runs; numerical reproducibility does not imply byte-identical PDFs.

`check_evidence.py` independently inverts the binomial CDF for CP bounds,
checks decisions, gains, quantiles, LOTO and costs, and reproduces the crossed
bootstrap intervals. It performs no ANN search or raw-truth access. The
delivered run passes 244 checks; this is not independent native replication.

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

## Evidence status and submission boundary

The matched-source diagnostic, crossed uncertainty, joint-error replay, and
completed cost accounting are **post-hoc reanalyses of frozen responses**.
They are not new preregistered experiments. TCP remains a recurring-profile
case; its main replay is not a new-query predictor or a 5% build-conformal
algorithm. The stricter CP allocation is per target, not simultaneous across
twenty targets. NDC economics is not wall-clock or monetary economics.

The PDFs have no identifying repository URL. This archive is an author-facing
source/evidence delivery, with frozen commit provenance; it is not an already
deidentified public artifact. Hosting an anonymous,
accessible artifact and checking the live submission form remain author
submission steps. Do not put a personal repository URL into the anonymous
PDF. The supplied numerical package is not a container for full native replay.

## Files

- `main.tex`, `sections/`: manuscript, definitions, theory, RQ1--RQ9.
- `appendix.tex`: short proofs and complete twenty-target certificate table.
- `figures/`: six PDF/SVG figures, all used in the main paper.
- `evidence/generated_tables.tex`: generated typeset table definitions.
- `evidence/w6_audit/`: compact numerical evidence and validation report.
- `evidence/extensions/`: unchanged external-method and scale/family summaries.
- `make_figures.py`, `check_evidence.py`: regeneration and independent checks.
- `PROVENANCE.md`: frozen sources and inference units.
- `SHA256SUMS.txt`: hashes for the delivery contents, excluding itself.

ACM template licensing is retained in `ACM-LICENSE` and the template headers.
