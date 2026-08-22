#!/usr/bin/env python3
"""Validate committed Phase I artifact hashes without modifying raw results."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import yaml


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    repository = args.manifest.resolve().parents[1]
    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    failures: list[str] = []
    for artifact in manifest["artifacts"]:
        path = repository / artifact["path"]
        if not path.is_file():
            failures.append(f"missing: {artifact['path']}")
            continue
        observed = sha256(path)
        if observed != artifact["sha256"]:
            failures.append(
                f"hash mismatch: {artifact['path']} expected={artifact['sha256']} "
                f"observed={observed}"
            )
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"validated {len(manifest['artifacts'])} Phase I artifacts")


if __name__ == "__main__":
    main()
