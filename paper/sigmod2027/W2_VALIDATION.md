# W2 validation, 2026-09-17

## Delivered scope

- Introduction and Related Work are prose drafts rather than section outlines.
- 13 cited bibliography entries; four related-work themes; four contributions.
- Abstract and Methodology receive only the necessary refresh-setting clarification. The completion note is updated. Later scientific sections, figure placeholders, formulas, and tables remain the W1 draft, not a completed submission.
- No experiment, model training, new index, statistical recomputation, threshold change, or W0 evidence change.

## Checks performed

1. `python check_w1.py`: PASS. All 57 W0 macro values match the ledger; 34 are used in the manuscript. Ten sections, five figure placeholders, four tables, and cross-references resolve. All 13 citation keys are unique, cited, and defined.
2. Repository W0 check: PASS before and after synchronization. Remote and local PDF SHA256 match; the evidence directory has no diff. Writing checks do not establish statistical validity.
3. Tectonic 0.17.0 / XeTeX + BibTeX: successful compilation, **6 pages including references**, original acmart v2.20 template and unchanged page dimensions. No undefined citations/references, missing glyphs, or horizontal overfull boxes in the final log.
4. All six final pages rendered and visually inspected. Text, formulas, four tables, reference numbers, and the explicit figure placeholders are legible. There are no clipped/overlapping objects or blank pages. The first two sections are on pp.1–2; later skeleton content and references remain visible for continuity.
5. Nonfatal diagnostics retained: fontconfig configuration/font-request messages, underfull boxes, a 1.27 pt vertical-box warning from final-page balancing with no visible clipping, and 10 BibTeX completeness warnings for missing publisher/address or page fields in selected conference records. No metadata were invented to silence these warnings. This is not a zero-warning or submission-compliance claim.
6. Semantic check: 5% refresh-plus-rebuild is not called a pure-rebuild causal effect; mean recall, expected FNR, and below-threshold query risk remain distinct; the source-profile population, empirical recovery, and candidate/fallback certificate are not conflated.
7. Bounded literature check: prior adaptive methods and prior quality guarantees are credited; no claim of universal superiority, first guarantee, or absence of prior update experiments. DARTH+ is explicitly a preprint with abstract-level support only; see `LITERATURE_NOTES.md`.
8. Prose scan plus manual review: semicolon-density and regular-paragraph-length advisories reviewed. Necessary scientific contrasts and the four-topic structure retained. No acceptance score or scientific-validity conclusion is inferred from a style checker.

## Frozen checksums

|File|SHA256|
|---|---|
|`evidence/results_macros.tex`|`ef839562385360d59cc24cb719fa5d7a2f72ca4c4a5d9efd3760209ac5a94f4d`|
|`evidence/evidence_ledger.json`|`c4d3f7b73c259bd87708a228e9e848bac0eb61f3e5a2c71ec08d849beee99125`|
|`acmart.cls`|`784c4f2fb07a70d8a797ee9d1c63f441c10fbd2f915c9c615d28cda35c0b742a`|
|Delivered W2 PDF|`16586eb2d803effcb894064d38460a1f11a620cd8271230b4d04080cb9d999a6`|

W0 holds H1–H6 remain open. A complete theory proof, joint certificate, source-truth cost analysis, or shared-query uncertainty repair requires the corresponding later work; W2 does not resolve them by wording.
