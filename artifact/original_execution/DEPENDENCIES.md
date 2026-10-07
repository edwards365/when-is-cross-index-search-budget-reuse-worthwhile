# Original execution dependencies

This map records the original dependency families. It is not a claim that a single modern environment reproduces all original binaries. The safe delivery inspector uses only Python 3.11+ standard library; it does not import experimental modules.

| Component | Frozen identity / evidence | Use and remaining build boundary |
|---|---|---|
| hnswlib headers | `3f3429661187e4c24a490a0f148fc6bc89042b3d`, `https://github.com/nmslib/hnswlib.git` | Main repository submodule identity read from the pinned commit; Python binding recorded as 0.8.0 in fresh-query protocols. Header/binding native-result equivalence is a separate runtime check. |
| DARTH | `0d9bafcf31d1d79668bc71139fe93fa5e70b5185`, `https://github.com/MChatzakis/DARTH.git` | Original upstream identity; public project modifications and aligned trainers are included in the source view. Arxiv IP reused some old objects: this identity alone does not attest every object/source pairing. |
| Ada-ef | `ed463f9993868f7ecc7c103920644e7f94abb377`, `https://github.com/chaozhang-cs/hnsw-ada-ef.git` | Separate official source family; use its metric-port source and registry, not a substitute HNSW implementation. |
| DiskANN | `8fb4d42e6a8bff0cff4db976a55c5fb99faaf475`, `https://github.com/microsoft/DiskANN.git` | Preserve Rust source patches, Cargo.lock identities and ordered-ID fixes. Dependency correction archives are not equivalent to a new algorithm. |
| Faiss | Historical 100K 1.15.0; S9 DARTH/Faiss 1.8.0; newer exact-counter and AVX2 paths have individual source/binary pins | These are not interchangeable packages. Installing an arbitrary matching version wheel does not reproduce project instrumentation, build options or counter semantics. Use each protocol's source/build map. |
| Python analysis | Historical Python3.11; NumPy1.26.4, SciPy1.13.1, h5py3.11.0; broader environment.yml supplied | Public saved-record analysis separately runs on Python3.12.14. Do not infer original native compatibility from that test. |
| LightGBM | Follow the DARTH model/runtime manifests and library hashes | 11-feature order is fixed. Arxiv model uses regression/100 trees/seed42/n_jobs8. Eight jobs does not mean eight OS threads. |
| Native compiler | C++17 and per-panel compilation flags; Rust for DiskANN | Compiler, SIMD, OpenMP and shared library differences affect both identity and timing. CMakeLists and native sources are inspectable; full portable build closure remains a distinct gate. |

## Header acquisition (not executed by the delivery task)

On a fresh, explicitly selected workspace, the hnswlib dependency can be acquired without changing its revision:

```sh
git clone https://github.com/nmslib/hnswlib.git third_party/hnswlib
git -C third_party/hnswlib checkout --detach 3f3429661187e4c24a490a0f148fc6bc89042b3d
```

The Deep native runner's original compile command is:

```sh
g++ -std=c++17 -O3 -pthread -I third_party/hnswlib cpp/src/deep1m_counting_runner.cpp -o deep1m_counting_runner
```

This command is source-traced, not a compilation result from this delivery task. It requires the original project source layout, not the privacy-transformed inspection view alone.

## Execution isolation and resource policy

Historical launchers sometimes default to `all`, write on import, assume absolute paths, or reuse an existing index. Never import them to inspect a CLI and never run their default phase against sealed outputs. A portable adapter must give explicit phases, fresh exclusive output paths and provenance for regenerated identities; it must not disable SHA assertions to make a run pass.

For any future authorized original-scale execution, retain the current project resource contract: 200GiB projected free-space floor and 128GiB aggregate outstanding growth ceiling; finite stage memory/disk/wall caps; fresh RAM/CPU/I/O checks; no occupation of other projects' assigned resources. Historical smaller floors in archived protocols are historical facts, not current launch authorization.

## Licenses

The project's LICENSE is included. Upstream components retain their own notices: hnswlib Apache-2.0, DARTH/Faiss MIT, Ada-ef Apache-2.0, DiskANN MIT as recorded in the source/license inventory. This package references upstream repositories and does not redistribute their compiled libraries, binary environments, datasets, models or indexes. Dataset acquisition links are in `datasets.json`; a public download URL is not a blanket redistribution grant.
