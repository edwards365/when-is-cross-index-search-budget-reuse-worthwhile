from pathlib import Path
import numpy as np
def native_ids(raw_ids, order, neighbors):
    """Map raw truth IDs into the exact exported base order."""
    raw_ids = np.asarray(raw_ids)
    order = np.asarray(order)
    neighbors = np.asarray(neighbors)
    for value in (raw_ids, order, neighbors):
        if value.dtype.kind not in "iu":
            raise ValueError("IDs/permutation must be integers")
    n = len(raw_ids)
    if (raw_ids.ndim != 1 or not n or np.any(raw_ids < 0)
            or np.any(raw_ids[1:] <= raw_ids[:-1])):
        raise ValueError("prepared raw IDs must be strictly increasing")
    if order.shape != (n,) or not np.array_equal(np.sort(order), np.arange(n)):
        raise ValueError("base order must be a full permutation")
    positions = np.searchsorted(raw_ids, neighbors)
    if np.any(positions >= n) or not np.array_equal(raw_ids[positions], neighbors):
        raise ValueError("truth ID absent from this base")
    inverse = np.empty(n, dtype=np.int64)
    inverse[order] = np.arange(n)
    mapped = inverse[positions]
    if n > np.iinfo(np.int32).max:
        raise ValueError("native ivecs ID capacity exceeded")
    return mapped.astype("<i4")

def write_vecs(path, blocks, width, kind):
    dtype = "<f4" if kind == "float" else "<i4"
    with path.open("xb") as stream:
        for block in blocks:
            block = np.asarray(block)
            if block.ndim != 2 or block.shape[1] != width:
                raise ValueError("vector width mismatch")
            if not np.all(np.isfinite(block)):
                raise ValueError("nonfinite vector value")
            packed = np.empty((len(block), width + 1), dtype="<i4")
            packed[:, 0] = width
            values = np.asarray(block, dtype=dtype)
            if not np.all(np.isfinite(values)):
                raise ValueError("float32 conversion overflow")
            packed[:, 1:] = values.view("<i4") if kind == "float" else values
            stream.write(packed.tobytes())

def ordered_blocks(train, order, chunk=8192):
    # h5py requires increasing fancy-index coordinates; restore requested order.
    for start in range(0, len(order), chunk):
        rows = np.asarray(order[start:start + chunk], dtype=np.int64)
        sort = np.argsort(rows)
        yield np.asarray(train[rows[sort]])[np.argsort(sort)]
