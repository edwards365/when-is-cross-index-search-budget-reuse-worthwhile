# P12 supplement and bound manuscript — artifact-deepening-v3

Download the fixed [artifact-deepening-v3 release](https://github.com/edwards365/when-is-cross-index-search-budget-reuse-worthwhile/releases/tag/artifact-deepening-v3). It binds the current manuscript, P12 supplement, reconstruction receipt and [24-claim evidence map](EVIDENCE.md). The fixed v2 remains the P0–P11 evidence and preceding manuscript; its assets and tag are unchanged.

P12 checks SIFT1M boundary ties using original vectors and saved returned IDs, compares all 384 cost objectives, and includes a separately implemented checker. All 69 original smaller-action rescues of endpoint failures disappear under tie scoring; conditional compression costs remain positive. It does not rerun ANN or deployment qualification.

Download `P12_artifact_review.zip` from the release. SHA256: `0ddfae6978c8876edd272940a5ce5de7339b0bd2e4a4d8b43ad361aed8d86c0f`. The historical review-stage name and internal README are retained to preserve the exact payload validated in a fresh environment; this release supplies its public status and manuscript binding.

```sh
python artifact/p12/rebuild.py --package P12_artifact_review.zip --verify-only
# After reading its README/NOTICE, install the pinned requirements in a fresh Python 3.11 environment.
python artifact/p12/rebuild.py --package P12_artifact_review.zip --extract p12-bundle
python -m pip install -r p12-bundle/requirements.txt
python p12-bundle/p12_rebuild.py --hdf5 /path/to/sift-128-euclidean.hdf5 --output new-p12-output
```

The HDF5 is external and not redistributed. Its exact identity, historical dataset source, resource gates, scope and license boundaries are in the package. The analysis and checker have completed in a fresh Windows virtual environment with exact expected-result checks. No Linux P12 execution is claimed.

`release-manifest.json` fixes PDF, source and supplement hashes; `CHECKSUMS.sha256` covers all other release files. Earlier paper/execution/statistical releases and P0–P11 commands are linked from EVIDENCE.md. Changes after this snapshot require a new version, not replacement assets.
