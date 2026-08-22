#!/usr/bin/env python3
"""Validate and summarize construction-time HNSW candidate instrumentation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from narhnsw.candidate_logs import summarize_candidate_log


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_directory", type=Path)
    args = parser.parse_args()
    summary = summarize_candidate_log(args.result_directory)
    output = args.result_directory / "candidate_log_summary.json"
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
