import numpy as np

def exact_top10(base, queries, metric, block=25):
    result = np.empty((len(queries), 10), dtype=np.int32)
    base_norm = np.sum(base * base, axis=1) if metric == "l2" else None
    for start in range(0, len(queries), block):
        query = queries[start : start + block]
        products = query @ base.T
        if metric == "l2":
            values = np.sum(query * query, axis=1)[:, None] + base_norm[None, :] - 2 * products
            ids = np.argpartition(values, 10, axis=1)[:, :10]
            local = np.take_along_axis(values, ids, axis=1)
            order = np.argsort(local, axis=1)
        else:
            ids = np.argpartition(-products, 10, axis=1)[:, :10]
            local = np.take_along_axis(products, ids, axis=1)
            order = np.argsort(-local, axis=1)
        result[start : start + len(query)] = np.take_along_axis(ids, order, axis=1)
    return result
