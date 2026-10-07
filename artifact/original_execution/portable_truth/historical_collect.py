"""Historical train-only collection used by the independent score check."""
import numpy as np

def collect_vectors(train, wanted):
    ordered = np.asarray(sorted(wanted), dtype=np.int64)
    values = np.empty((len(ordered), train.shape[1]), dtype=np.float32)
    cursor = 0
    for begin in range(0, train.shape[0], 8192):
        end = min(begin + 8192, train.shape[0])
        right = int(np.searchsorted(ordered, end, side="left"))
        if right > cursor:
            block = train[begin:end]
            values[cursor:right] = block[ordered[cursor:right] - begin]
            cursor = right
    if cursor != len(ordered):
        raise ValueError("Uncollected vectors")
    return ordered, values
