# SIGMOD 2027 E&A — W5 text and tables

W5 is the complete text/table manuscript. Figures are deferred to W5.5.
The compiled PDF has 8 pages including references, 5 tables and 4 propositions
with proofs. No new experiment was run for this revision.

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
- `check_w5.py` (repository only): numerical, source and PDF checks, using
  Python `pypdf`; optional rendering also uses `pypdfium2` and `Pillow`.
- `W5_VALIDATION.md` (repository / separate author report): format audit,
  revision record, remaining scientific boundaries and outstanding actions.

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
identifying development repository into the blind-review PDF. W5 is a checked
writing deliverable, not a declaration that every scientific or submission
requirement is complete. W5.5 adds the deferred figures and repeats layout checks.
