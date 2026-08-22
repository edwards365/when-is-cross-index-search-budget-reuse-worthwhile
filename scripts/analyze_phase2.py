#!/usr/bin/env python
"""Validate a Phase II result table before hierarchical analysis is enabled."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {
    "dataset",
    "method",
    "seed",
    "order",
    "query_id",
    "ef_search",
    "recall",
    "ndc",
    "latency_seconds",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    args = parser.parse_args()
    frame = pd.read_csv(args.results)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"missing Phase II result columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("cannot analyze an empty Phase II result table")
    print(
        f"validated {len(frame)} query rows across "
        f"{frame[['seed', 'order']].drop_duplicates().shape[0]} build clusters"
    )


if __name__ == "__main__":
    main()
