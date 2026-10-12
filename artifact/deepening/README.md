# P0–P11 mechanism and learning evidence

This additive release binds the revised working manuscript to all P0–P11 saved-response analyses and independent checking code. The previous paper, response, source and execution-entry tags remain fixed. Download **ICDE_P0-P11_artifact.zip**, **manuscript-source.zip**, **manuscript.pdf**, and **release-manifest.json** from [artifact-deepening-v2](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-deepening-v2).

The ZIP provides two scientific components (`p0-p10/`, `p11/`), current theory and result notes, a 23-claim evidence map, all configurations, saved inputs, expected outputs and an umbrella command. Optimizers, learning rules and measured arrays retain their original hashes. The portable P8 checker compares two qualification-bound fields numerically instead of as strings; see [PORTABILITY.md](PORTABILITY.md). That verification-only change and the release wrapper are separately identified in provenance.

## Reconstruct the added evidence

Use Python **3.11** in a new virtual environment. Extract the ZIP to `deepening-bundle` and run from its parent:

```sh
python -m venv analysis-env
# POSIX: analysis-env/bin/python; Windows: analysis-env/Scripts/python.exe
analysis-env/bin/python -m pip install -r deepening-bundle/requirements.txt
analysis-env/bin/python deepening-bundle/rebuild.py --bundle deepening-bundle --verify-only
analysis-env/bin/python deepening-bundle/rebuild.py --bundle deepening-bundle --output rebuilt
```

At least **5 GiB available RAM** and **10 GiB free disk** are required at launch. The wrapper uses one logical CPU and library thread, samples a 3 GiB free-memory reserve and a 2 GiB task RSS ceiling, and stops on a gate violation. These sampled controls supplement platform memory enforcement; they are not a continuous peak measurement. Outputs must be new and outside the bundle. A failure retains logs and is not automatically retried.

The ordered command runs eleven P0–P10 stages (P3b separately; P6 within P5), theory examples, and four P11 analysis/checking phases. It then compares every declared output with the saved expectations. Integers, categories, actions, fields and row order match exactly. Floating-point differences use absolute tolerance `1e-9` and relative tolerance `1e-12`, with all nonzero differences recorded. The prior same-host P11 receipt records 14 byte-identical outputs; a new platform reports its own equality level. `VERIFICATION.json` reports the actual result.

## Find a result

[EVIDENCE.md](EVIDENCE.md) maps the stages and manuscript claims to inputs, commands and expected files. Inside the ZIP, `docs/claims.csv` resolves every evidence path from the bundle root. `PROVENANCE.json` lists source, export and configuration identities. `LICENSE_SCOPE.md` specifies the license boundary; [SOURCES.md](SOURCES.md) records upstream datasets and dependencies.

The current claim map takes precedence over historical P0–P9 interpretation where explicitly narrowed. The added 100K tie analysis removes some local safety witnesses while preserving the main conditional cost pattern. The million-scale SIFT 69/72 observation retains its ID-based scoring convention; boundary-tie sensitivity for that panel remains unresolved.

## Paper and validation scope

The release manifest pins the manuscript PDF/source, six frozen figure hashes, scientific ZIP, and referenced earlier release versions. Author details remain deferred in this working manuscript. The new release's public verification receipt records saved-response reconstruction and independent algorithmic checks in its stated environment; it does not remeasure ANN, ground truth, bootstrap or original timings. Figures 3 and 4 still show their original panels, while the added construction/learning evidence is indexed here.

Original vectors, documents, graph indexes, binary environments and third-party paper PDFs are excluded. The source-data acquisition routes remain in the pinned original-execution delivery. Code, documentation and project-generated numerical records follow the repository's existing MIT grant; third-party material retains its own terms.
