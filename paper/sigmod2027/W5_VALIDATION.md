# W5: text, table and consistency seal

Date: 2026-09-17. Scope: manuscript revision and existing-evidence checks only.
No ANN experiment, new inference run, figure generation, parameter change, or
scientific-result overwrite was performed. W5.5 owns the deferred figures.

## Venue and template

- Target: SIGMOD 2027 Research, Experiments & Analysis, initial submission.
- Official CFP: https://2027.sigmod.org/calls_papers_sigmod_research.shtml
- Checked 2026-09-17: ACM two-column proceedings `sigconf`, Letter, main text at
  most 12 pages excluding references, PDF at most 10 MB, double anonymous;
  short appendix, if used, must be a separate PDF. No appendix is needed here.
- The CFP's ACM download URL returned HTTP 403. The released ACM package was
  independently downloaded from https://mirrors.ctan.org/macros/latex/contrib/acmart.zip
  and checked against https://ctan.org/pkg/acmart (2.20, 2026-08-16).
- The existing class-generating source `acmart.dtx` is byte-identical to that
  release: SHA256 `e29efd327f5c759f3d1f2e99dc8588c6a05b734c142f89c3e348161b893e44ff`.
- `ACM-Reference-Format.bst` is also identical:
  `4342d27456645567ef1a027f6474e894715bc31d468f040142fa54540440ad04`.
- The class file is unmodified. No font-size, line-spacing, geometry, margin,
  column-width, or text-height override was introduced. Emergency line breaking
  was retained from W4; ragged-bottom pages and balanced final columns avoid
  stretched whitespace. `anonymous,nonacm` suppress author and publication data.

## Revision record

1. Removed the internal draft banner, overview placeholder, section-purpose
   text and writing-completion map. The existing text-only workflow is now a
   numbered specification, not a figure. W5 contains zero figure environments.
2. Placed primary portability, audit, recovery, tail, build-sensitivity and
   economics evidence before the external-method/family/scale extensions.
3. Completed the setup from the preregistration: the primary refresh replay is
   the DARTH Faiss-HNSW fork, **not** hnswlib; Deep1M is a separate hnswlib block.
4. Preserved all W0 numbers and result files. Ten additional display values
   (endpoint risk, p99, LOTO and delete-largest) are extracted from the same
   frozen summaries in a separate W5 ledger. No bootstrap was rerun.
5. Corrected the external-method inference: absolute target risk is evidence of
   qualification failure, not by itself a measured source-to-target increment.
6. Replaced the unsupported broad fallback-tail claim with the observed pooled
   p95/p99 comparisons and exact endpoint equality on the fallback target.
7. Retained individual-CP versus simultaneous-certificate distinctions; the
   candidate's stored UCB is not silently relabeled as the fallback certificate.
8. Named lifecycle omissions found in the frozen cost code: old truth,
   source-role profiling outside evaluation, and endpoint-certification search.
   The old break-even values remain conditional, with an explicit additive
   missing-cost sensitivity formula. No missing cost was invented.
9. Reduced repeated positioning/defensive language while keeping conditions
   that change the interpretation of the findings.
10. Added publisher-verified article numbers for DARTH (242), Ada-ef (25) and
    graph-search evaluation (43), and LAET pages 2539--2554. Retained 16 cited
    references and the existing source-verification limits.

## Checks and measured output

- Eight PDF pages total; references begin on page 8. Counting that mixed page
  as a main-text page still gives 8 <= 12. Letter 612 x 792 pt.
- Five tables, four propositions, four proofs, zero figures; all RQ1--RQ9
  retained. The existing short proofs remain in the main text.
- W0 checker: 57 frozen values pass against the source repository.
- W5 numeric checker: 10 values; 80 per-build risk/fallback rows; 19 accepted
  candidates; fallback outcomes equal that build's endpoint. Frozen-source
  comparison passes at the W0 input baseline.
- Existing mathematical regression suite: 10/10 pass. These are regression
  checks, not an independent formal-proof review.
- Every citation key resolves; all 16 bibliography records are cited. No missing
  section/table/equation reference or duplicate label. Original W0 macro text
  agrees with its ledger.
- PDF font resources are embedded; metadata contains title, compiler and
  timestamps but no author name, account, institution, or server address.
- No identifying repository link or fake artifact placeholder in the PDF.
  Its external links are bibliographic links, not an uploaded research artifact.
- Compilation succeeds. Remaining BibTeX warnings concern optional publisher,
  address or page fields for page-less ICLR/NeurIPS entries; values absent from
  the official records were not fabricated. Font-selection and underfull-box
  notices are checked visually and do not imply missing fonts.
- Final PDF pages are rendered and inspected for table clipping, broken math,
  bibliography layout and collisions. File hashes are delivered separately.

## Remaining submission actions

**Anonymous artifact link: PENDING.** No verified anonymous hosting endpoint was
found in the manuscript or current artifact reports. The manuscript makes no
claim that an anonymous URL is already live. The LaTeX ZIP is a paper source
package, not the complete experimental artifact. Create/verify the anonymous
artifact and audit its contents before actual submission.

W5.5 may add figures using frozen evidence, followed by another page/layout and
caption-number check. This W5 pass does not repair experimental certificate
composition, crossed resampling, missing acquisition costs, or novel-query
generalization. Those boundaries are now explicit in the paper rather than
hidden by a formatting change. Author approval and portal preview remain separate.

## Source notes for this revision

- Official DARTH article: https://helios2.mi.parisdescartes.fr/~themisp/publications/sigmod26-darth.pdf
- Ada-ef authors' BibTeX: https://github.com/chaozhang-cs/hnsw-ada-ef
- Graph evaluation authors' BibTeX: https://github.com/iliasazizi/GVS
- LAET author's paper: https://conglongli.github.io/paper/ann-sigmod2020.pdf
- DiskANN official BibTeX: https://papers.nips.cc/paper_files/paper/2019/file/09853c7fb1d3f8ee67a61b6bf4a7f8e6-Bibtex.bib

Tools/assistance: Codex performed source-bound revision, LaTeX compilation and
PDF checks, using academic-research-suite, anti-defensive-writing, venue-templates
and PDF guidance. Venue-template workflow attribution (not scientific evidence):
Timothy Kassis, Vinayak Agarwal, Yuhuan He, Darshil Patel, and Aubrey M. Brueckner.
2026. *Scientific Agent Skills: A Library of Procedural Knowledge for Research
Agents*. https://doi.org/10.48550/arXiv.2609.00065 (current record checked
2026-09-17). This assistance note is outside the anonymous manuscript bibliography.
