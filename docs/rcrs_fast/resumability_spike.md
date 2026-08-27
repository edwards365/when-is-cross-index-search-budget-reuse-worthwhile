# hnswlib resumability spike

A frozen SIFT-100K Original index and 500 previously used train-side Cross-Index queries were evaluated at fixed `ef=256`. The spike allocates the full fixed-search candidate/result capacity from the start and inserts three read-only checkpoints after 16, 48 and 128 base expansions. It never performs a smaller independent search.

For all 500 queries, checkpoint-enabled and checkpoint-disabled spike paths had identical top-k labels, exact distance counts and visited expansion order; both were also exactly equal to native `searchKnn` top-k and exact distance counts. The checkpoint callback only reads heaps/counters. Continuing after a checkpoint uses the same candidate queue, result heap and visited set, so fixed fallback does not restart or repeat distance computations. The 1,500 aggregate checkpoint rows contain churn, kth-distance improvement, frontier gap, queue sizes, newly visited count and NDC; no node trace or queue snapshot is stored.

This establishes an implementation path for a feature-flagged RCRS prototype, not an early-stop safety or performance result. No stopping model or threshold was trained.
