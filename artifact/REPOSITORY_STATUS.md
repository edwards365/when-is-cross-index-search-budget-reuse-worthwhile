# Repository reconciliation — 2026-10-06

This update replaces the public landing page with the current evaluation-and-analysis scope. It does not rewrite or retroactively merge the scientific history.

## Read-only findings

- Public `main` before this change: `62270763e84a1f9a445e4e6289ed78cb140b8139`. Its README describes an earlier rebuild-portability/method-development agenda, including plans and completion estimates that are not the current paper's status.
- The research workspace is on `exp/icde2027_eab_1m`, at `f88dc625272fade3dc7774747dc95683bda4b38a`. Its tracked and staged diffs were empty. It has **943 commits not reachable from that public-main commit**, and its tree comparison spans **4,492 changed files**. This is an ancestry count, not 943 independently reviewed changes or a promise of conflict-free merging.
- That research branch was absent from the public branch listing. Its **230 untracked files** include response tables, query bins, indexes, build artifacts, and older working material. Untracked does not mean missing scientific work, nor does it mean safe to publish.
- The Windows clone remains on an older feasibility branch with an untracked `results/gate_a/` directory. Current manuscript/artifact preparation lives outside that clone. The publication process preserves both working trees.
- No open pull requests were listed at inspection time. Public historical branches are not automatically treated as approved current contributions.

## Selected for this update

Project title/description, navigation, citation title, a selected saved-result artifact entry, path-redacted provenance, and a portable read-only consistency checker. Small result payloads are copied byte-for-byte; omitted private paths are confined to a separately identified public configuration view. Original evidence and frozen sources are unchanged.

## Still to reconcile

After the initial entry, the repository was renamed to `when-is-cross-index-search-budget-reuse-worthwhile`. A separate response-analysis release now provides the saved inputs and portable wrapper for the new summary-cost/qualification tables. This is selective integration, not a merge of the 943 historical commits. The unchanged historical README retains its original links.

| Material | Required action before a later release |
|---|---|
| Research commits not on `main` | Review a claim-linked source/config/test subset; merge or port selected changes rather than importing the whole history |
| Untracked response files | The selected summary-analysis inputs are now provided as a pinned Release attachment; other panels still need claim-linked input inventories |
| Indexes, datasets, binaries, environments | Do not commit to Git; provide legal acquisition/build instructions or an appropriate separate distribution where authorized |
| Manuscript and PPT figures | Pin the submitted version, audit metadata/rights, and deliver a dedicated reproducible paper package |
| Historical local paths | A new wrapper resolves selected-analysis inputs; remaining original-execution paths still require separate portable wrappers |
| Full artifact claim | Require the documented inputs and commands to work from a clean checkout; a repository URL and checksum check alone are insufficient |

The later `artifact-paper-v1` supplement adds new portable reconstruction of saved-record Figure 2/4 bootstrap intervals and Figure 5/6 statistics. It does not restart historical workers or original ANN/timing experiments. Its claim-by-claim coverage map supersedes the earlier generic statement that all bootstrap reconstruction was missing. Other narrative panels and original execution still require separate delivery.

No branch, result, or untracked file is deleted.
