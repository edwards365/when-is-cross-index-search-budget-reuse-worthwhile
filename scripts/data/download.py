#!/usr/bin/env python
"""Manifest-driven resumable downloader with space and SHA-256 checks."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import time
import urllib.request
from pathlib import Path

import yaml


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(4 * 1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()
    manifest = yaml.safe_load(args.manifest.read_text(encoding="utf-8"))
    repo = Path(__file__).resolve().parents[2]
    target = repo / manifest["local_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    expected_size = int(manifest.get("size_bytes", 0))
    if shutil.disk_usage(target.parent).free < max(expected_size * 2, 100 * 1024**2):
        raise RuntimeError("insufficient free disk space")
    if target.exists() and digest(target) == manifest["sha256"]:
        print(f"verified existing {target}")
        return
    partial = target.with_suffix(target.suffix + ".part")
    for attempt in range(1, args.retries + 1):
        try:
            offset = partial.stat().st_size if partial.exists() else 0
            request = urllib.request.Request(manifest["download_url"])
            if offset:
                request.add_header("Range", f"bytes={offset}-")
            with (
                urllib.request.urlopen(request, timeout=60) as response,
                partial.open("ab" if offset and response.status == 206 else "wb") as output,
            ):
                shutil.copyfileobj(response, output, length=4 * 1024 * 1024)
            if digest(partial) != manifest["sha256"]:
                raise ValueError("checksum mismatch")
            partial.replace(target)
            print(f"downloaded and verified {target}")
            return
        except Exception:
            if attempt == args.retries:
                raise
            time.sleep(2**attempt)


if __name__ == "__main__":
    main()
