# Full replay contract

The raw replay is intentionally separate from the lightweight artifact because
datasets and indexes are not committed. Supply a data root containing the
checksummed inputs listed in the Phase 1--4 manifests.

Order:

1. Verify all input SHA-256 values and external commits.
2. Recreate the registered query roles before inspecting evaluation results.
3. Run Phase 1 external bridges using their pinned official commits.
4. Run the Phase 2 5% mixed-refresh replay with the frozen selection,
   certification, and cold-evaluation ranges.
5. Re-run Phase 3 analysis from the two frozen Vamana event tables; it does not
   rebuild an index.
6. Run Deep1M with eight frozen build identities, then its analyzer.
7. Run Phase 5 integration and the artifact smoke.

Machine-specific absolute paths in historical launch scripts are provenance,
not an anonymous artifact interface. Reviewers should map them through a local
data root or use the committed aggregate replay. The paper must report this as
an artifact limitation until every historical launcher is fully parameterized.

Expected additional space for Phase 4 is about 5 GiB, with at least 5 GiB free
reserve. The complete historical SIFT/Arxiv stores require more space and are
not duplicated by the artifact.
