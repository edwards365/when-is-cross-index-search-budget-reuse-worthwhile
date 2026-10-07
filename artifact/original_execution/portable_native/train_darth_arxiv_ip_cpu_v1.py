#!/usr/bin/env python3
"""Train a new DARTH model in native predictor order; never rewrite old models.

Native CSV qids are offsets into the supplied ordered query-row mapping. This
checks that mapping against source_design, not the contents of the query fvecs;
the adapter must verify those contents before generating observations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path

FEATURES = (
    "step", "dists", "inserts", "first_nn_dist", "nn_dist",
    "avg_dist", "furthest_dist", "variance", "percentile_50",
    "percentile_25", "percentile_75",
)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_rows(registry, dataset, query_rows):
    matches = [d for d in registry["datasets"] if d["name"] == dataset]
    if len(matches) != 1:
        raise ValueError("dataset must have exactly one role registration")
    rows = matches[0]["roles"]["source_design"]
    if not rows or any(type(v) is not int or v < 0 for v in rows):
        raise ValueError("source_design row IDs must be nonnegative integers")
    if (not isinstance(query_rows, list) or
            any(type(v) is not int for v in query_rows) or
            len(set(rows)) != len(rows) or query_rows != rows):
        raise ValueError("query-row mapping must equal ordered source_design IDs")
    for name, other in matches[0]["roles"].items():
        if name != "source_design" and set(rows).intersection(other):
            raise ValueError("source_design overlaps another registered role")
    return rows


def validate_records(records, query_count):
    seen = set()
    count = 0
    for record in records:
        count += 1
        values = [float(record[k]) for k in ("qid", *FEATURES, "r")]
        if not all(math.isfinite(v) for v in values):
            raise ValueError("observations contain nonfinite numeric values")
        qid = values[0]
        if qid != int(qid) or not 0 <= qid < query_count:
            raise ValueError("qid is not a local source_design query offset")
        if not 0 <= values[-1] <= 1:
            raise ValueError("recall target outside [0, 1]")
        seen.add(int(qid))
    if not count or seen != set(range(query_count)):
        raise ValueError("observations must cover every source_design query")
    return count


def publish_training(model_path, metadata_path, train):
    """Reserve both new destinations before training; preserve partial failures."""
    if model_path.resolve() == metadata_path.resolve():
        raise ValueError("model and metadata destinations must differ")
    with model_path.open("x", encoding="utf-8") as model_stream:
        with metadata_path.open("x", encoding="utf-8") as metadata_stream:
            model_text, metadata = train()
            model_stream.write(model_text)
            model_stream.flush()
            metadata["model_sha256"] = hashlib.sha256(model_text.encode("utf-8")).hexdigest()
            metadata_stream.write(json.dumps(metadata, indent=2, allow_nan=False) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("input", "model", "metadata", "roles", "query-row-ids"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()
    roles_sha, mapping_sha = sha256(args.roles), sha256(args.query_row_ids)
    rows = source_rows(json.loads(args.roles.read_text()), args.dataset,
                       json.loads(args.query_row_ids.read_text()))
    if sha256(args.roles) != roles_sha or sha256(args.query_row_ids) != mapping_sha:
        raise ValueError("role inputs changed while read")
    # Lazy imports permit schema tests without loading training libraries.
    import pandas as pd
    import lightgbm as lgb
    input_sha = sha256(args.input)
    frame = pd.read_csv(args.input, usecols=["qid", *FEATURES, "r"])
    count = validate_records((dict(zip(frame.columns, values)) for values in
                              frame.itertuples(index=False, name=None)), len(rows))
    if sha256(args.input) != input_sha:
        raise ValueError("observation input changed while read")

    def train():
        model = lgb.LGBMRegressor(objective="regression", random_state=42,
                                 n_estimators=100, verbose=-1, n_jobs=8)
        started = time.monotonic()
        model.fit(frame[list(FEATURES)], frame["r"])
        return model.booster_.model_to_string(), {
            "status": "NEW_MODEL_TRAINED_NATIVE_FEATURE_ORDER",
            "dataset": args.dataset, "features": list(FEATURES),
            "input_sha256": input_sha, "roles_sha256": roles_sha,
            "query_row_ids_sha256": mapping_sha,
            "query_content_verified_by_this_trainer": False,
            "qid_semantics": "offset_into_ordered_source_design_query_row_ids",
            "rows": count, "queries": len(rows),
            "training_seconds": time.monotonic() - started,
            "n_estimators": 100, "random_state": 42, "n_jobs": 8,
        }
    publish_training(args.model, args.metadata, train)


if __name__ == "__main__":
    main()
