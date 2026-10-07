import numpy as np
import struct
from pathlib import Path
def read_qbin(path: Path):
    with path.open("rb") as handle:
        if handle.read(8) != b"E1AQ0001":
            raise ValueError(f"bad qbin magic: {path}")
        rows, dim = struct.unpack("<QQ", handle.read(16))
        ids = np.empty(rows, dtype=np.int64)
        vectors = np.empty((rows, dim), dtype=np.float32)
        for row in range(rows):
            ids[row] = struct.unpack("<q", handle.read(8))[0]
            vectors[row] = np.frombuffer(handle.read(dim * 4), dtype="<f4")
        if handle.read(1):
            raise ValueError(f"trailing qbin bytes: {path}")
    return ids, np.ascontiguousarray(vectors)
