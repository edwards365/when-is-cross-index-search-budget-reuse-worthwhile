# SIGMOD 2027 E&A — W5.5 illustrated manuscript

W5.5 adds three vector figures, an unnumbered single-column glossary, explicit
ICBA/TCP names, and a descriptive failure-concentration check. The PDF has
10 pages including references (main text ends on page 9), five numbered tables
and four propositions with proofs. No new experiment was run.

## Open and compile

Upload the LaTeX ZIP to Overleaf, choose `main.tex` as the main document, and
select **XeLaTeX** with a recent TeX Live. Recompile from scratch if citation
links are stale. The class is ACM `acmart` 2.20 in `sigconf,anonymous,nonacm` mode.

Local alternatives (create `build/` first):

```text
latexmk -xelatex -outdir=build main.tex
tectonic -X compile main.tex --outdir build --keep-logs --keep-intermediates
```

## Source and evidence

- `sections/`: complete manuscript; primary evidence precedes extensions.
- `references.bib`: 16 cited records in ACM reference style.
- `evidence/results_macros.tex`: 57 unchanged W0 values.
- `evidence/w5_macros.tex`: 10 further values from the same frozen summaries.
- `evidence/check_w5_numbers.py`: checks the compact W5 input copies, risk
  aggregation, fallback and extra macros; no experiment execution.
- `check_w55.py`: numerical, source and PDF checks, using
  Python `pypdf`; optional rendering also uses `pypdfium2` and `Pillow`.
- `figures/`: ready-to-include vector PDFs and editable SVGs; PNGs are previews.
- `make_figures.py`: reproduces the three figures from compact frozen summaries,
  using Python with matplotlib and numpy and an installed Times New Roman font.
  This does not run an experiment or access external datasets.
- `evidence/w55_diagnostics.json` and `w55_macros.tex`: descriptive aggregates
  from the unchanged 80-row per-build table.
- `W55_VALIDATION.md` (repository / separate author report): critical response
  to the supplied review, format checks, naming provenance, and open actions.

The downloadable source ZIP contains the paper and compact numeric inputs,
not raw vectors, indexes or the full experimental artifact. Compilation needs
neither SSH access nor a dataset. Existing W0/W1--W4 history is retained in the
repository rather than duplicated in the clean Overleaf package.

## Submission boundary

The official SIGMOD 2027 Research CFP requires a two-column ACM proceedings
paper, Letter size, no more than 12 main-text pages excluding references, and
double anonymity. Rules checked 2026-09-17:
https://2027.sigmod.org/calls_papers_sigmod_research.shtml

The class-generating source and bibliography style match the released CTAN
ACM package byte-for-byte. Class/style files are unmodified.

An anonymous artifact URL has not yet been verified. Do not insert the public,
identifying development repository into the blind-review PDF. W5.5 is a checked
writing deliverable, not a declaration that every scientific or submission
requirement is complete. The 19/20 candidate decisions use individual CP checks;
the manuscript preserves their distinction from a joint 95% pipeline certificate.
