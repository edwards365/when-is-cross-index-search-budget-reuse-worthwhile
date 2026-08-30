#!/usr/bin/env python3
"""Verify the committed theory-closure checksum manifest."""

from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "results" / "icba_oracle_observable" / "checksums.sha256"


def main() -> None:
    seen = 0
    for line in MANIFEST.read_text(encoding="utf-8").splitlines():
        expected, rel = line.split("  ", 1)
        assert "__pycache__" not in rel and not rel.endswith("checksums.sha256")
        actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        assert actual == expected, rel
        seen += 1
    assert seen >= 40
    print(f"CHECKSUM_PASS: {seen} tracked theory artifacts")


if __name__ == "__main__":
    main()
