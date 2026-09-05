# Instrumentation gate

The tracer is implemented on the project side and leaves third-party hnswlib unchanged. Its interface receives only index, query vectors, replay-development query IDs, ef values, and a build identifier; it never receives truth. It records upper traversal length, base expansions, distance evaluations, visited count, duplicate-neighbor ratio, queue operations, candidate yield over windows 4/8/16, kth-distance improvement over windows 4/8/16, frontier and kth distances, their ratio, termination reason, and an expansion-order hash.

Across 12,000 rows, native and traced top-10 outputs agreed exactly. Outcome labels were joined only after trace capture in the analysis stage.
