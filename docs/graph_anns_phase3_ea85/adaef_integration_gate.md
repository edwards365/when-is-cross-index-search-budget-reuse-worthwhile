# Ada-ef Integration Gate

## Source and isolation

- Official repository: `https://github.com/chaozhang-cs/hnsw-ada-ef.git`
- Frozen commit: `ed463f9993868f7ecc7c103920644e7f94abb377`
- Official checkout policy: clean and unmodified.
- Environment: isolated conda prefix under the data500 experiment directory.
- Compiler: isolated GCC 12 toolchain; Eigen 3.4, HDF5 1.14, and Boost 1.85.

The upstream CMake file pins local placeholder dependency paths. In addition, the frozen upstream `experiments_driver/util.h` declares `avg_latency` twice in one function and therefore does not compile as written. The project-side bridge is a source snapshot with exactly two integration-only changes: the adaptive-ef include is made include-root-relative, and the duplicate declaration is removed. No algorithmic code, estimator, search logic, target, or action rule is changed.

## Core executable smoke

The core smoke compiles and executes the official estimator, `EfAdapter`, `Sketch`, and adaptive HNSW search on deterministic synthetic cosine data. It uses disjoint design and evaluation rows and writes a machine-readable result. This smoke is only an integration test; it is not scientific evidence about Ada-ef, ICBA, or portability.

Observed integration-only output:

- target recall: 0.95;
- design queries: 30;
- evaluation queries: 20;
- weighted-average ef: 25.266668;
- evaluation mean recall: 0.895;
- evaluation failures: 9/20.

The nonzero failures are expected to be possible in a tiny synthetic smoke and are not used for any claim. The result confirms that the official core classes run end to end in the isolated environment.

## Scientific-run gate

The official estimator supports cosine distance and inner product but does not implement an L2 estimator. Therefore:

- Arxiv-Nomic can proceed using its registered normalized cosine semantics;
- the frozen Euclidean SIFT comparison cannot be silently converted to cosine;
- SIFT must be marked `NOT_IMPLEMENTATION_SUPPORTED_UNDER_REGISTERED_METRIC` unless an official, semantics-preserving L2 path is found before evaluation is accessed.

The next step is an Arxiv one-build smoke with frozen query-role IDs. Only after finite per-query action, risk, and cost output is produced without overlap may the three-build registered main comparison begin.
