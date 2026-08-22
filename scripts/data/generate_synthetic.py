#!/usr/bin/env python
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "python"))

import numpy as np  # noqa: E402
from narhnsw.datasets import GENERATORS  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", choices=sorted(GENERATORS), default="narrow_bridge")
    parser.add_argument("--n", type=int, default=2000)
    parser.add_argument("--dim", type=int, default=16)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    split = GENERATORS[args.name](n=args.n, dim=args.dim, seed=args.seed)
    output = REPO / "data" / "synthetic" / f"{args.name}_n{args.n}_d{args.dim}_s{args.seed}.npz"
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output,
        base=split.base,
        query=split.query,
        ground_truth=split.ground_truth,
        metric=np.array(split.metric),
    )
    manifest = {
        "name": args.name,
        "kind": "deterministic_synthetic",
        "generator": "scripts/data/generate_synthetic.py",
        "n_base": len(split.base),
        "n_query": len(split.query),
        "dimension": split.base.shape[1],
        "metric": split.metric,
        "seed": args.seed,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "file": str(output.relative_to(REPO)),
        "sha256": sha256(output),
    }
    output.with_suffix(".json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
