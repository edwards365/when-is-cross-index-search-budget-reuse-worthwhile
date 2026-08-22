#!/usr/bin/env python
"""Guarded entry point for Phase II development and eventual Core execution."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    required = {"datasets", "methods", "M", "ef_construction", "seeds", "orders"}
    missing = required - set(config)
    if missing:
        raise ValueError(f"missing Phase II config keys: {sorted(missing)}")
    if config.get("formal"):
        if config.get("firewall") != "open" or not config.get("enabled"):
            raise RuntimeError("formal Phase II Core is blocked while the firewall is sealed")
        if config.get("epsilon") is None:
            raise RuntimeError("formal Phase II Core requires a frozen epsilon amendment")
    if not args.dry_run:
        raise RuntimeError(
            "public-data execution backend is not yet integrated; use --dry-run for gate audit"
        )
    print(
        f"validated {config['phase']}: {len(config['datasets'])} datasets, "
        f"{len(config['methods'])} methods, formal={bool(config.get('formal'))}"
    )


if __name__ == "__main__":
    main()
