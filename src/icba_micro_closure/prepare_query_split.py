#!/usr/bin/env python3
"""Freeze mutually exclusive sentinel/evaluation query IDs for replay."""
import hashlib
import json
from pathlib import Path

DATASETS = ("sift_100k", "glove100_100k", "arxiv_nomic_100k")
SEED = 991


def score(dataset, query_id):
    return hashlib.sha256(f"{SEED}:{dataset}:{query_id}".encode()).hexdigest()


manifest = {"schema_version": 1, "seed": SEED, "source": "frozen cross_index_design query ids",
            "sentinel_count": 256, "evaluation_count": 744, "datasets": {},
            "firewall": {"validation_dev": "SEALED", "formal_test": "SEALED"}}
for dataset in DATASETS:
    ordered = sorted(range(1000), key=lambda q: (score(dataset, q), q))
    sentinel = sorted(ordered[:256]); evaluation = sorted(ordered[256:])
    assert not set(sentinel) & set(evaluation) and len(sentinel)+len(evaluation) == 1000
    manifest["datasets"][dataset] = {"sentinel_query_ids": sentinel,
                                      "evaluation_query_ids": evaluation,
                                      "membership_sha256": hashlib.sha256(
                                          json.dumps({"sentinel": sentinel, "evaluation": evaluation},
                                                     sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
path = Path("manifests/icba_micro_closure_query_split.json")
tmp = path.with_suffix(".json.tmp"); tmp.write_text(json.dumps(manifest, indent=2)+"\n"); tmp.replace(path)
