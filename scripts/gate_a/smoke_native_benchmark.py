#!/usr/bin/env python
"""Local synthetic smoke for the Gate-A native query schema and exact-NDC path."""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "python"))

from narhnsw.ground_truth import exact_top_k  # noqa: E402


def write_matrix(path: Path, values: np.ndarray, dtype: np.dtype) -> None:
    values = np.ascontiguousarray(values, dtype=dtype)
    with path.open("wb") as handle:
        handle.write(struct.pack("<QQ", *values.shape))
        values.tofile(handle)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(7)
    points = rng.normal(size=(128, 8)).astype(np.float32)
    queries = rng.normal(size=(16, 8)).astype(np.float32)
    truth, _ = exact_top_k(points, queries, 10, metric="l2")
    order = np.random.default_rng(7).permutation(len(points)).astype(np.uint32)
    with tempfile.TemporaryDirectory(prefix="narhnsw-native-smoke-") as temporary:
        root = Path(temporary)
        write_matrix(root / "points.bin", points, np.dtype(np.float32))
        write_matrix(root / "queries.bin", queries, np.dtype(np.float32))
        write_matrix(root / "truth.bin", truth, np.dtype(np.uint32))
        with (root / "order.bin").open("wb") as handle:
            handle.write(struct.pack("<Q", len(order)))
            order.tofile(handle)
        output = root / "output"
        subprocess.run(
            [
                str(args.executable.resolve()),
                str(root / "points.bin"),
                str(root / "order.bin"),
                str(root / "queries.bin"),
                str(root / "truth.bin"),
                "-",
                "l2",
                "16",
                "100",
                "7",
                "synthetic",
                "original",
                "-",
                "10,20",
                "4",
                "2",
                "synthetic-config-hash",
                "synthetic-hardware",
                "native-smoke",
                str(output),
            ],
            check=True,
            cwd=REPO,
        )
        frame = pd.read_csv(output / "queries.csv")
        metadata = json.loads((output / "metadata.json").read_text(encoding="utf-8"))
        if len(frame) != 16 * 2 * 2:
            raise AssertionError("native smoke query schema has the wrong row count")
        if frame["ndc"].dtype.kind not in "iu" or (frame["ndc"] <= 0).any():
            raise AssertionError("native smoke NDC is not a positive exact integer")
        if frame.duplicated(
            ["dataset", "method", "build_seed", "ef_search", "query_id", "latency_round"]
        ).any():
            raise AssertionError("native smoke contains duplicate pairing keys")
        if metadata["formal_test_members_accessed"]:
            raise AssertionError("native smoke marked formal access")
        print(
            json.dumps(
                {
                    "rows": len(frame),
                    "mean_recall": float(frame["recall_at_10"].mean()),
                    "mean_ndc": float(frame["ndc"].mean()),
                    "metadata": metadata,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
