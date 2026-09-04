#!/usr/bin/env python3
"""Validate the pre-certification GSC proposal registry."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def validate(path: Path) -> dict[str, object]:
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    ids = [row["config_id"] for row in rows]
    operators = {row["operator"] for row in rows}
    forbidden = ("evaluation", "certification", "future_confirm")
    bad_tokens = [
        row["config_id"]
        for row in rows
        if any(token in (row["parameters"] + row["allowed_inputs"]).lower() for token in forbidden)
    ]
    conservative = {row["operator"] for row in rows if row["profile"] == "conservative"}
    return {
        "rows": len(rows),
        "max_configs_ok": len(rows) <= 24,
        "unique_ids_ok": len(ids) == len(set(ids)),
        "operators": sorted(operators),
        "o4_conservative_ok": "O4" in conservative,
        "o6_conservative_ok": "O6" in conservative,
        "forbidden_tokens": bad_tokens,
        "status": "PASS"
        if len(rows) <= 24
        and len(ids) == len(set(ids))
        and {"O4", "O6"} <= conservative
        and not bad_tokens
        else "FAIL",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("registry", type=Path)
    args = parser.parse_args()
    result = validate(args.registry)
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
