# HNSW–Vamana semantic crosswalk

The common object is an implementation-native finite action, not a common scalar budget.

| Object | hnswlib HNSW | Faiss HNSW | DiskANN3/Vamana | Unified status |
|---|---|---|---|---|
| Construction operator | incremental multilayer HNSW | incremental multilayer HNSW | single-layer directed Vamana/RobustPrune-style graph build | abstract operator only |
| Build environment | level RNG, insertion order, concurrency | insertion permutation and implementation state | registered seed/order/concurrency/config | yes, as opaque `xi` |
| Hierarchy | randomized layers | randomized layers | no HNSW hierarchy | no raw mapping |
| Direction | implementation-managed near-symmetric links | implementation-managed links | directed bounded out-neighborhood | abstract graph only |
| Entry | HNSW top entry point | HNSW entry point | registered start-point strategy, e.g. medoid | semantic role only |
| Native query action | `ef`/`efSearch` | `efSearch` | `Knn::l_value`; `beam_width` separate | finite ordered sets, not numerically equivalent |
| Termination | HNSW frontier rule | HNSW frontier rule | frontier/list convergence under `l_value` and beam | implementation specific |
| Endpoint | largest registered raw action | largest registered raw action | largest registered `l_value` at fixed beam | grid-relative only |
| Right censoring | no registered action succeeds | same | same | yes |
| Recall failure | exact-truth Recall@k below target | same | same | yes |
| NDC | implementation distance computations | Faiss implementation counter/proxy | exact distance computations if exposed; otherwise `UNKNOWN` | no cross-implementation equality |
| Visited nodes | trace/counter if exposed | trace/counter if exposed | recorded search path or stats if exposed | report implementation-local |
| I/O | normally in-memory | normally in-memory | zero for in-memory; explicit for SSD | must separate |
| Wall-clock | implementation/hardware local | implementation/hardware local | mode/hardware local | never compare raw across families without normalization |
| Fallback | preregistered fixed-safe action | same | max registered action or exact search only if separately validated | conditional, not automatically safe |
| Replay | serialized index + config/hash | serialized index + config/hash | saved graph + full config/seed/binary hash | preflight required |

## Native action lock

For Stage I, use DiskANN3 in-memory graph search and register six `l_value` values. Fix `beam_width=1`, start-point strategy, degree, build `L`, prune alpha, thread count, data ordering, compiler, features, metric, and floating-point mode. Changing beam width creates a different action family and invalidates the preregistration.

`efSearch` and `l_value` both control candidate exploration, but their state transitions, termination, graph topology, counters and latency are different. There is no deterministic universal conversion preserving recall risk and cost.
