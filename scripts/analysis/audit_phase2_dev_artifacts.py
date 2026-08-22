#!/usr/bin/env python
"""Validate immutable raw artifacts referenced by the Phase II development manifest."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import yaml


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    repository = args.manifest.resolve().parents[1]
    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    artifacts = [artifact for run in manifest["runs"] for artifact in run["artifacts"]]
    failures = []
    for artifact in artifacts:
        path = repository / artifact["path"]
        if not path.is_file():
            failures.append(f"missing: {artifact['path']}")
        elif sha256(path) != artifact["sha256"]:
            failures.append(f"hash mismatch: {artifact['path']}")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"validated {len(artifacts)} Phase II development artifacts")


if __name__ == "__main__":
    main()
