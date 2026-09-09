# Data-by-operator interaction framework

Let datasets be `D={SIFT30K, ArxivNomic30K}` and operators be `O={hnswlib, FaissHNSW, DiskANN3Vamana}`. For a registered statistic `T`, define

\[
\theta_{d,o}=E[T\mid d,o,\text{registered build/query protocol}].
\]

No additive model is assumed. Report the full table, uncertainty at the correct sampling unit, and an interaction contrast only if its weighting was preregistered. A Vamana result need not match the HNSW magnitude to count as external replication.

Interpretation:

- both Vamana datasets pass detection and materiality: strong cross-family replication;
- one passes and one is weak/null: data-operator conditional replication;
- budget heterogeneity passes but operational consequence misses: mechanism-only replication;
- structural change without material transport: registered regime boundary;
- both datasets precisely exclude the minimum registered effect: nonreplication in registered Vamana;
- wide intervals: inconclusive;
- semantic/replay failure: invalid bridge, not scientific nonreplication.

The existential non-HNSW claim is supported by one valid non-HNSW unit. Graph-ANNS universality would require a declared operator population and a sampling/coverage argument not supplied here.
