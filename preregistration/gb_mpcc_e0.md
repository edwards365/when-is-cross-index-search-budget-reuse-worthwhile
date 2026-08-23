# GB-MPCC Graph Gate E0 preregistration

Status: **frozen before graph construction**. Parent corrected R0 decision:
`7d36ae9` (`PASS_TO_GRAPH_E0`). Formal test remains closed.

## Question and scope

E0 asks whether the query-independent selector signal that transferred to frozen
design-development route states survives insertion-time reciprocal updates and
later reverse pruning in a complete searchable 10K graph. It does not ask whether
GB-MPCC is already a production replacement for HNSW or whether it improves 100K
performance.

The experiment is a fixed-candidate counterfactual construction. For each dataset
and seed, every method receives the same real layer-0 candidate stream recorded
from Original HNSW, the same insertion order and levels, and the same source budget.
The selected source list is applied at insertion time, followed by hnswlib's capacity
check and Algorithm-4 reverse pruning. The completed layer-0 adjacency is installed
under the identically reconstructed Original upper layers. This design isolates the
selector and makes controls genuinely candidate-matched. It deliberately excludes
candidate-pool feedback; a passing result therefore supports a final-graph local
mechanism, not a fully integrated adaptive implementation.

## Data firewall

Only the first 10,000 `train` vectors from SIFT, GloVe-100 and Arxiv-Nomic may be
used for graph construction and query-independent states. Design-dev consists of
the already frozen Gate-A development query vectors at IDs 0–499. Exact top-10
truth is recomputed against the same first-10K base after this protocol is frozen.
HDF5 `test`, `neighbors`, and `distances`, validation-dev, and formal test are
forbidden. Query vectors and truth cannot enter candidate scoring or construction.

## Methods and budgets

Original HNSW/Algorithm 4 is the reference. LengthAware-Angle is an alias only after
its exact per-insertion equality to Algorithm 4 is audited. Geometry, MaxMin-Angle
and GGR-0 are shared strong baselines. GB-MPCC and its backbone-matched Random and
Shuffled controls are run at `R=1,2,4`; `R=4`, already used in R0, is the sole gate
configuration, while `R=1,2` are dose-response ablations and cannot rescue a failed
primary result. For budget `b`, the first `max(0,b-R)` recorded Algorithm-4 choices
are mandatory and exactly `min(R,b)` positions are flexible.

This gives 13 distinct graphs per dataset/seed and 117 total graph runs. Candidate
pools, graph seeds, state samples, flexible-slot counts, and reciprocal handling are
matched within every GB/Random/Shuffled triplet.

## Required audits

Before any treatment result is accepted, the Original replay must reproduce the
recorded final directed layer-0 graph exactly for all nine dataset/seed pairs.
Every graph must satisfy endpoint, self-edge, duplicate, degree, weak-connectivity,
and upper-layer checksum invariants. Immediate and final source/reciprocal retention
are reported separately so later pruning cannot be confused with selector output.

Search uses the frozen ef grid `10,20,40,80,120,200`, 500 design-dev queries, exact
NDC counting, and a trace-vs-upstream result check. Metrics cover strict and 5%
multiplicative progress, beam admissibility, local minima, expansions, NDC, Recall,
latency diagnostics, topology, retention, runtime, and memory.

## Decision

E0 passes only if all graph/reproduction invariants hold and, on at least two
datasets with at least two of three seeds, GB-MPCC R4 improves at least two registered
navigation-chain metrics relative to Original/LengthAware and Geometry. At least one
improvement must also exceed both backbone-matched controls, and mean Recall@10 loss
must not exceed 0.001 at any frozen ef. R1/R2 cannot rescue R4. Failure of exact
Original reproduction, graph validity, connectivity, recall noninferiority, or the
two-dataset navigation chain stops the performance-algorithm path.

A committed E0 pass may authorize E1 preregistration only. It never authorizes formal
test access.
