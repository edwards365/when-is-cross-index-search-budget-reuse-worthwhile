# Project status

Last updated: 2026-08-22

Milestone completed: Tier-0 infrastructure, executable baseline, and first independent theory batch.

Completed locally: workspace/Git/GitHub audit; hardware and toolchain audit; repository scaffold; exact Python and C++ resistance references; deterministic synthetic data generator; manifest-driven downloader; HNSW smoke runner; query-level result schema; baseline analysis; theory boundary documents; initial tests and CI definition. Python tests pass 8/8; CTest passes 1/1; Ruff passes. A 2,000-base/200-query/16-D narrow-bridge dataset was generated with exact top-10 ground truth and SHA-256 `7e0ff23c9a4a0a172aba068bebc0f973f9137668200cee02298bac56fda4ffcc`.

Executed smoke run `5c814131-a03b-4264-9f36-852f06a5b5c4`: Recall@10 rose from 0.914 at ef=10 to 0.983 at ef=20, 0.997 at ef=40, and 1.0 at ef>=80. These timings are non-affinity-controlled pipeline checks, not H1/H2 evidence. The 256-node union-symmetrized Gaussian k-NN mechanism check scored 1,532 edges; leverage range was 0.0726786 to 1.0000000000000133 with zero violations above `1+1e-8`.

Instrumentation milestone started: a C++ harness now reads real hnswlib layer-0 adjacency, validates duplicate/self/ID/degree invariants, and counts every actual distance-function call with a wrapped metric. On a deterministic 512×8 fixture it achieved Recall@10=1 with exact mean NDC=199, mean high-layer hops=3.3125, 5,487 directed bottom-layer edges, and maximum bottom degree 32. This audit also found that upstream `metric_distance_computations` reports only 24.4375 on the same queries because default base-layer collection is off; it is explicitly banned as total NDC in this project.

Literature milestone started: 18 required/adjacent search strings and 13 verified primary works are recorded. Within this recorded scope, no identical effective-resistance/leverage modification of HNSW/NSG/Vamana/DiskANN neighbor selection was found. This is not a first-work claim; dynamic random-walk rewiring and pseudoinverse-preserving graph reduction require full-text collision review.

Degree-preserving repair milestone started: all six required variants run on an exported real hnswlib layer-0 graph while preserving each node's outgoing degree and the total 5,487-edge budget. The first aggressive full-reselection result is negative: Original reaches Recall@10=.995 at ef=10 with mean NDC=98.05, while Resistance+Direction first clears .95 at ef=20 with mean NDC=135.94, and Resistance-only needs ef=40 with mean NDC=182.05. See `reports/repair_smoke_report.md`; this result is retained and does not decide H2.

Theory milestone completed: the HNSW primary paper's Algorithms 1--5 and complexity sections were audited, including the exact Algorithm 4 pairwise diversity condition. A normative notation contract, verified-results ledger, 16-claim status registry, six reading cards, local/global model split, theorem-candidate audit, complexity ledger, first report, and paper-section draft now exist. Dense numerical tests cover known graph families, projection/Foster identities, Rayleigh monotonicity, weighted spanning-tree marginals, log-det and frozen-objective submodularity, and navigation counterexamples. The explicit dynamic objective `sum(selected current leverages)` is disproved as submodular by a five-vertex enumeration. Spectral approximation is also shown insufficient for adjacency-based greedy navigation. Python tests pass 28/28, Ruff passes, and Release CTest passes 2/2.

Next milestones: finish the queued full-text reading cards; add insertion-candidate logging and a frozen small-fraction controlled-swap intervention that preserves most HNSW heuristic edges; instrument selector margins and exact query traces to measure the new theorem premises. Random and Geometry controls must be matched by replacement count. Verified public-data manifests proceed in parallel.

Current tier: Tier 0 (16 GiB RAM is the limiting resource). Do not schedule complete 1M sweeps.

Open constraints: native Windows lacks global CMake/PATH configuration, but the isolated environment supplies CMake and Visual Studio supplies MSVC. No Slurm or WSL distribution is installed. The private GitHub repository, milestone, eight issues, and `main`/`develop`/`exp/resistance-validation` branches now exist remotely. Initial push required retries because connections to `github.com:443` were temporarily reset/timed out; no force push was used.
