# Detected hardware

Detection time (UTC): `2026-08-22T03:35:52.394083+00:00`
Hardware ID: `LAPTOP-Q79U6UF3-AMD64`
Experiment tier: **Tier 0**

```json
{
  "hardware_id": "LAPTOP-Q79U6UF3-AMD64",
  "detected_at_utc": "2026-08-22T03:35:52.394083+00:00",
  "os": {
    "system": "Windows",
    "release": "10",
    "version": "10.0.26200",
    "kernel": "Windows-10-10.0.26200-SP0"
  },
  "cpu": {
    "model": "Intel64 Family 6 Model 183 Stepping 1, GenuineIntel",
    "physical_cores": 24,
    "logical_cores": 32,
    "smt_active": true,
    "affinity_logical_cpus": 32
  },
  "memory": {
    "total_gib": 15.627,
    "available_gib": 1.316
  },
  "disk": {
    "path": "C:",
    "total_gib": 924.172,
    "free_gib": 258.35
  },
  "gpu": {
    "nvidia_smi": "NVIDIA GeForce RTX 4070 Laptop GPU, 8188 MiB, 561.00",
    "cuda_compiler": "nvcc: NVIDIA (R) Cuda compiler driver\nCopyright (c) 2005-2024 NVIDIA Corporation\nBuilt on Wed_Aug_14_10:26:51_Pacific_Daylight_Time_2024\nCuda compilation tools, release 12.6, V12.6.68\nBuild cuda_12.6.r12.6/compiler.34714021_0"
  },
  "numa": {
    "available": false,
    "nodes": null
  },
  "toolchain": {
    "python": "3.11.16",
    "compiler": "MSC v.1944 64 bit (AMD64)",
    "cmake": "cmake version 3.30.5\n\nCMake suite maintained and supported by Kitware (kitware.com/cmake).",
    "git": "git version 2.54.0.windows.1"
  },
  "scheduler": {
    "slurm": false
  },
  "containers": {
    "docker": null,
    "apptainer": null,
    "singularity": null
  },
  "system_tuning": {
    "cpu_governor": null,
    "transparent_huge_pages": null,
    "note": "Not applicable or not exposed by native Windows APIs; no settings changed."
  },
  "tier": 0
}
```

No governor, SMT, NUMA, or huge-page setting was changed.