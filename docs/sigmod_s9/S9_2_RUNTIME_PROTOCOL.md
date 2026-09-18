# S9-2 deployment-runtime and lifecycle protocol

Status: frozen before S9-2 timing output access.

## Question and estimands

S9-2 asks whether already-qualified recovery policies reduce real serving time, and whether that reduction amortizes the cost of obtaining target information. It does not refit policies or reopen the scientific safety decisions.

Primary serving estimand: paired relative reduction in summed single-query wall time versus the registered target endpoint on the evaluation role. Secondary endpoints are process-CPU time, p50/p95/p99 latency, throughput, and fallback/non-fallback tails. Lifecycle estimands add source-history acquisition, target selection, exact-truth construction, certification search, policy-control, and fallback costs under cached-history and cold-history accounting.

The independent outer unit is the target build. Queries and repeated timings are nested repeated measurements, not independent builds.

## Frozen Stage A: Faiss-HNSW 100K

- Inputs: the 48 registered Faiss indexes and the two disjoint 500-query target certification/evaluation roles from the sealed target-certified experiment.
- Datasets: SIFT-100K and Arxiv-Nomic-100K.
- Native grid: 16, 32, 64, 128, 256, 512.
- Compared procedures: fixed target endpoint, equal-information target-global calibration, frozen TCP, and frozen one-rung fixed-slack where defined.
- No action, shift, fallback rule, risk threshold, or dataset-specific hyperparameter may change after this protocol.

Each index is loaded once per timing pass. Search uses one Faiss/OpenMP thread and one pinned physical CPU. Before measurement, every grid action receives 50 deterministic warm-up queries. Evaluation-query order and action order are independently shuffled within build and repetition using seed 991-derived hashes. Each query-action cell receives seven repeated measurements. The timer surrounds only `index.search`; process-CPU time is recorded alongside monotonic wall time. Index load, truth construction, selection, certification, control, and serialization are timed separately for lifecycle accounting rather than hidden inside serving time.

## Frozen Stage B: hnswlib Deep1M

Stage B is authorized only if Stage A instrumentation passes native-equivalence and timing-stability checks. It reuses the eight registered Deep1M target-certified builds, the frozen grid 200, 300, 400, 600, 800, 1,200, and the three disjoint 500-query roles. It uses the same thread, affinity, blocking, repetition, and statistical rules. The candidate remains the preregistered one-rung action; no 100K result may alter it.

## Machine and nuisance controls

- Host CPU: AMD EPYC 7542; primary CPU affinity is logical CPU 2 on NUMA node 0.
- `FAISS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`.
- GPU is unused.
- Record kernel, compiler/library versions, CPU governor/frequency availability, memory availability, load average, process list, and thermals if exposed.
- Abort a timing block if another user process materially occupies the pinned CPU, if system load changes beyond the preregistered validity band, or if memory/disk safety is threatened. Do not silently discard individual slow measurements.

Build order is a seeded permutation per pass. Action order is randomized within query and repetition, blocking action comparisons against drift and query difficulty. Repeated measurements estimate timing noise; they do not increase the target-build sample size.

## Integrity and analysis

For every timed search, query ID, target build, role, action, repetition, order, top-k hash, recall, NDC, wall time, process-CPU time, and fallback state are recorded. Native equivalence requires exact equality of query ID, action, top-k, recall, and NDC with the frozen response record.

Primary uncertainty uses a crossed target-build by query-ID bootstrap with 5,000 replicates and seed 991, retaining repeated measurements inside each cell. Per-build results, leave-one-target-out minima, and deletion of the largest-gain 1% of queries are reported. Timing samples are never treated as independent builds.

## Gates and stopping rules

1. **Instrumentation:** zero native-response mismatches; otherwise stop with `INVALID_RUNTIME_INSTRUMENTATION`.
2. **Timing validity:** at least 99% complete cells; median within-cell wall-time CV at most 10% and p95 CV at most 25%; otherwise label the affected block `RUNTIME_NOISE_NOT_CONTROLLED` without changing the protocol.
3. **Safety:** the frozen certification/evaluation decision remains unchanged.
4. **Serving mean:** a positive claim requires the 95% crossed-bootstrap lower bound on relative latency reduction to exceed zero.
5. **Tail:** pooled p95 latency ratio must have an upper confidence bound at most 1.05 for a tail-noninferior claim; p99 is reported without serving as a hidden substitute.
6. **Lifecycle:** every included and missing cost component is listed. Break-even must be positive under the stated cached/cold ledger; unmeasured components force a conditional rather than end-to-end economic claim.
7. **Robustness:** direction must survive leave-one-target-out analysis for a robust claim.

Stage A negative or mixed results are retained. Stage B is skipped if Stage A reveals invalid instrumentation, uncontrolled timing noise, or no interpretable mapping from frozen actions to native searches.
