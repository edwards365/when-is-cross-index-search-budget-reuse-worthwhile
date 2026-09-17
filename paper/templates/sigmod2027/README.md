# SIGMOD 2027 LaTeX template intake

This directory preserves the user-supplied `acmart-primary.zip` archive unchanged for the SIGMOD 2027 manuscript workflow.

## Intake status

- Target: ACM SIGMOD 2027 research track, Experiments & Analysis, initial submission.
- Official rule source: <https://2027.sigmod.org/calls_papers_sigmod_research.shtml>
- Rule checked: 2026-09-17.
- Required submission format: current ACM two-column proceedings template.
- Main-paper limit: 12 pages excluding references.
- Review mode: double anonymous.
- Required E&A title suffix: `: [Experiments & Analysis]`.

## Supplied archive

- File: `acmart-primary.zip`
- SHA-256: `b38560ed55cc5e644ab23cfbde76e968ae2d09ef7f083b7aa70bd8f8c0876c01`
- Compressed size: 15,548,908 bytes.
- Entries: 66.
- Expanded size: 17,085,189 bytes.
- Path-traversal entries: 0.
- Executable/script entries: 0.
- Embedded class declaration: `acmart` v2.20, dated 2026-08-16.
- License: LPPL 1.3c.

## Provenance boundary

The archive is an ACM `acmart` source-tree snapshot and contains the class, bibliography style, guide, samples, and license. Its own README labels the GitHub source as a development/experimental version and directs production use to the ACM or CTAN release. Therefore it is retained as a candidate source package, not asserted to be the final SIGMOD-specific submission kit.

Before producing the submission PDF, compare this archive with the version linked by the current SIGMOD 2027 author instructions. Keep the chosen `acmart.cls`, margins, font sizes, spacing, and headers unchanged. Record any replacement archive and its checksum in `template_manifest.json` rather than silently overwriting this intake.

## Intended use

1. Preserve the archive unchanged as provenance.
2. Extract a working copy under the manuscript build directory when drafting begins.
3. Start from the official `sample-sigconf.tex` pattern using anonymous review mode.
4. Do not commit author identity, affiliations, acknowledgements, private paths, or identifying PDF metadata to the review package.
5. Revalidate page count, anonymity, fonts, PDF size, and current official-template identity before submission.
