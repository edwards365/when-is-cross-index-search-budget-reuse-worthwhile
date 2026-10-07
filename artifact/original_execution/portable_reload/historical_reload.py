"""Unchanged historical graph reload clock boundary; no query access."""
from types import SimpleNamespace

def measure(index, metric, dim, count, hnswlib, time):
    args=SimpleNamespace(dataset="input")
    config={"datasets":{"input":{"metric":metric,"dim":dim}}}
    receipt={"effective_base_count":count}
    t0 = time.perf_counter_ns()
    graph = hnswlib.Index(space=config["datasets"][args.dataset]["metric"],
                          dim=config["datasets"][args.dataset]["dim"])
    graph.load_index(str(index), max_elements=receipt["effective_base_count"])
    graph.set_num_threads(1)
    load_ns = time.perf_counter_ns() - t0
    if graph.get_current_count() != receipt["effective_base_count"]:
        raise ValueError("Loaded count")
    return load_ns, graph.get_current_count()
