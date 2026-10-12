# License and source inventory

The repository's existing [MIT license](../../LICENSE) applies to project-authored code, documentation and project-generated numerical experiment records. The release ZIP includes that exact license plus a scope notice. Existing copyright notices remain intact. No new license is asserted for original external vector datasets or third-party software.

| Material | Origin / fixed identity | Treatment in this release |
|---|---|---|
| Primary and independent P0–P11 code | Project execution locks and `SOURCE_PROVENANCE.json` | Original code hashes retained; packaging changes separately recorded |
| Numeric outputs, query row IDs, returned IDs/distances, hits and native work | Project runs on SIFT, Deep1M and Arxiv panels | Saved generated records only; no embeddings, documents or graph indices |
| SIFT and Deep1M dataset access | [ANN-Benchmarks](https://github.com/erikbern/ann-benchmarks), [dataset provider](https://ann-benchmarks.com/) | Upstream access and dataset-specific terms remain applicable; data bytes excluded |
| Arxiv-Nomic access | [VIBE](https://github.com/vector-index-bench/vibe) | Benchmark code MIT is not a blanket dataset grant; original vectors/text excluded |
| HNSW implementation used by new 100K measurements | [hnswlib v0.8.0](https://github.com/nmslib/hnswlib/tree/v0.8.0), [Apache-2.0 license](https://github.com/nmslib/hnswlib/blob/v0.8.0/LICENSE) | Header SHA pins and project wrapper included; third-party headers/binaries excluded from the added ZIP |
| NumPy 1.26.4, SciPy 1.14.1 | Official PyPI releases, BSD licenses | Installed separately; library code not copied into the bundle |
| h5py 3.11.0, psutil 7.2.2 | Official PyPI releases, BSD licenses | Installed separately; their licenses accompany upstream packages |
| LLVM-MinGW measurement toolchain | Historical pinned build record | Provenance only; no toolchain distribution or new native build |
| IEEEtran class and bibliography style in manuscript source | Existing template, retained original notices | Template license/copyright remain in the supplied files |
| Six figure PDFs and manuscript text | Project-authored frozen presentation and current working manuscript | Figure identities retained; author placeholders remain visible |

`PROVENANCE.json` in the ZIP maps each exported scientific code and input to its source hash. Metadata redaction replaces personal paths with relative references; it never changes numerical arrays, role identities, optimizers or learning rules. Nested original response archives preserve their previous public-release identities and licenses. Software licenses are not used to assert rights over original datasets.
