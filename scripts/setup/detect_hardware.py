#!/usr/bin/env python
from __future__ import annotations

import json
import platform
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import psutil
import yaml


def command(args: list[str]) -> str | None:
    try:
        result = subprocess.run(args, text=True, capture_output=True, timeout=10, check=False)
        return (result.stdout or result.stderr).strip() or None
    except (OSError, subprocess.TimeoutExpired):
        return None


def classify_tier(physical_cores: int, memory_gib: float, free_disk_gib: float) -> int:
    if physical_cores >= 64 and memory_gib >= 256 and free_disk_gib >= 1024:
        return 3
    if physical_cores >= 32 and memory_gib >= 128 and free_disk_gib >= 500:
        return 2
    if physical_cores >= 8 and memory_gib >= 32 and free_disk_gib >= 100:
        return 1
    return 0


def main() -> None:
    repo = Path(__file__).resolve().parents[2]
    memory = psutil.virtual_memory()
    disk = shutil.disk_usage(repo)
    physical = psutil.cpu_count(logical=False) or 1
    logical = psutil.cpu_count(logical=True) or physical
    nvidia = command(
        ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]
    )
    profile = {
        "hardware_id": f"{platform.node()}-{platform.machine()}",
        "detected_at_utc": datetime.now(UTC).isoformat(),
        "os": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "kernel": platform.platform(),
        },
        "cpu": {
            "model": platform.processor(),
            "physical_cores": physical,
            "logical_cores": logical,
            "smt_active": logical > physical,
            "affinity_logical_cpus": len(psutil.Process().cpu_affinity())
            if hasattr(psutil.Process(), "cpu_affinity")
            else None,
        },
        "memory": {
            "total_gib": round(memory.total / 1024**3, 3),
            "available_gib": round(memory.available / 1024**3, 3),
        },
        "disk": {
            "path": str(repo.drive),
            "total_gib": round(disk.total / 1024**3, 3),
            "free_gib": round(disk.free / 1024**3, 3),
        },
        "gpu": {"nvidia_smi": nvidia, "cuda_compiler": command(["nvcc", "--version"])},
        "numa": {"available": shutil.which("numactl") is not None, "nodes": None},
        "toolchain": {
            "python": platform.python_version(),
            "compiler": platform.python_compiler(),
            "cmake": command(["cmake", "--version"]),
            "git": command(["git", "--version"]),
        },
        "scheduler": {"slurm": shutil.which("sbatch") is not None},
        "containers": {
            "docker": command(["docker", "--version"]),
            "apptainer": command(["apptainer", "--version"]),
            "singularity": command(["singularity", "--version"]),
        },
        "system_tuning": {
            "cpu_governor": None,
            "transparent_huge_pages": None,
            "note": "Not applicable or not exposed by native Windows APIs; no settings changed.",
        },
        "tier": classify_tier(physical, memory.total / 1024**3, disk.free / 1024**3),
    }
    yaml_path = repo / "configs" / "devices" / "detected_device.yaml"
    yaml_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
    md = [
        "# Detected hardware",
        "",
        f"Detection time (UTC): `{profile['detected_at_utc']}`",
        f"Hardware ID: `{profile['hardware_id']}`",
        f"Experiment tier: **Tier {profile['tier']}**",
        "",
        "```json",
        json.dumps(profile, indent=2),
        "```",
        "",
        "No governor, SMT, NUMA, or huge-page setting was changed.",
    ]
    (repo / "reports" / "hardware.md").write_text("\n".join(md), encoding="utf-8")
    print(yaml.safe_dump(profile, sort_keys=False))


if __name__ == "__main__":
    main()
