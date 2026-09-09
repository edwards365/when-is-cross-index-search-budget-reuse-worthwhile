# Official DiskANN code audit

## Frozen implementation

- Repository: <https://github.com/microsoft/DiskANN>
- Commit: `8fb4d42e6a8bff0cff4db976a55c5fb99faaf475`
- License: MIT
- Branch state: the default branch is DiskANN3, a Rust rewrite; legacy C++ remains on `cpp_main` and is described as not actively maintained.

## Located interfaces

| Requirement | Evidence at frozen commit | Audit result |
|---|---|---|
| Search entry | `diskann/src/graph/search/knn_search.rs` | found |
| Native budget | `Knn { l_value, beam_width }`; documentation calls `l_value` search-list size | found; freeze beam separately |
| Search statistics | `SearchStats`, including distance computations, hops and timing | found; field-level export must be verified in preflight |
| Trace | `RecordedKnn` accepts a search recorder | found |
| Build entry | in-memory and disk builder modules | found |
| Build controls | max degree, `l_build`, alpha/config, threads, start-point strategy | found |
| Random seed | `IndexConfiguration.random_seed`; used in PQ sampling/medoid routines | exposed |
| Processing order | dataset iterator enumerates records; concurrency may affect insertion schedule | partially controlled; determinism not proved |
| Robust pruning | builder/pruning modules | found at code level |
| Medoid/entry | medoid routine receives configured seed | found |
| Serialization | graph save/load interfaces | found |
| SSD I/O | disk provider/build/search path | found but excluded from Stage-I primary mode |

## Replay limitation and preflight

The presence of a seed is not proof of bitwise reproducibility under parallel insertion. Before Stage I, build the same tiny public/non-held-out corpus twice with identical config, serialize both graphs, and compare hashes plus adjacency summaries. Then repeat with a different preregistered seed or input permutation and require a reproducible, nonzero graph difference. This is an implementation audit, not the scientific pilot.

If identical-config replay differs beyond declared deterministic-replay noise, stop with `NO_REPRODUCIBLE_VAMANA_BUILD_ENVIRONMENT`. If changing the sole registered environment variable does not change any serialized artifact across the preflight, choose another documented build variable before accessing pilot queries.

## Provenance limitation

The requested private source commits were verified through the connected GitHub repository, but the local clone could not fetch them via unauthenticated HTTPS. The local staging branch therefore has a different physical parent; the manifest records both the intended and actual parent.
