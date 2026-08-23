#!/usr/bin/env python3
"""Export normalized construction prefixes for the native R0 candidate recorder."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import h5py
import numpy as np
import yaml


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=Path("preregistration/gb_mpcc_r0.yaml"))
    parser.add_argument("--output", type=Path, default=Path("results/gb_mpcc/r0_inputs"))
    args = parser.parse_args()
    protocol = yaml.safe_load(args.protocol.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for dataset in protocol["datasets"]:
        manifest = yaml.safe_load(Path(dataset["manifest"]).read_text(encoding="utf-8"))
        source = Path(manifest["local_path"])
        if sha256(source) != manifest["sha256"]:
            raise ValueError(f"{dataset['id']}: source checksum mismatch")
        with h5py.File(source, "r") as handle:
            vectors = np.asarray(handle["train"][: dataset["vectors"]], dtype=np.float32)
        if dataset["normalized"]:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            if np.any(norms == 0):
                raise ValueError(f"{dataset['id']}: zero vector cannot be normalized")
            vectors /= norms
        output = args.output / f"{dataset['id']}.fbin"
        vectors.tofile(output)
        rows.append(
            {
                "dataset": dataset["id"],
                "path": output.as_posix(),
                "points": int(vectors.shape[0]),
                "dimensions": int(vectors.shape[1]),
                "dtype": "float32_little_endian_native",
                "normalized": bool(dataset["normalized"]),
                "source_sha256": manifest["sha256"],
                "fbin_sha256": sha256(output),
                "accessed_hdf5_members": ["train"],
                "formal_test_members_accessed": False,
            }
        )
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {"schema_version": 1, "formal_test_members_accessed": False, "inputs": rows},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(manifest_path)


if __name__ == "__main__":
    main()
