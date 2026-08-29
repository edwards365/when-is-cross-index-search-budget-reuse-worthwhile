#!/usr/bin/env python3
import argparse, glob, gzip, json, math, os
import numpy as np
import pandas as pd
from scipy.stats import beta
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEED = 991
TAU = 0.90
ALPHA = 0.05
DATASETS = ("sift_100k", "arxiv_nomic_100k")

def stable_budget(group, budgets):
    recall = dict(zip(group["ef_search"].astype(int), group["recall_at_10"].astype(float)))
    for i, b in enumerate(budgets):
        if all(recall.get(x, -1.0) >= TAU for x in budgets[i:]):
            return i, False
    return len(budgets) - 1, True

def first_features(row):
    ds = [float(x) for x in str(row.returned_top10_distances).split(";") if x != ""]
    d1 = ds[0] if ds else 0.0
    d2 = ds[1] if len(ds) > 1 else d1
    dk = ds[-1] if ds else 0.0
    return [
        math.log1p(float(row.exact_ndc)),
        math.log1p(max(float(row.query_latency_ns), 0.0)),
        math.log1p(max(dk, 0.0)),
        (d2 - d1) / max(abs(d1), 1.0),
        float(row.max_level),
    ]

def cp_upper(k, n, alpha=ALPHA):
    if n <= 0:
        return float("nan")
    if k >= n:
        return 1.0
    return float(beta.ppf(1.0 - alpha, k + 1, n - k))

def load_build(path):
    df = pd.read_csv(path, compression="gzip")
    assert bool(df.success.all())
    budgets = sorted(int(x) for x in df.ef_search.unique())
    if len(budgets) != 12:
        raise RuntimeError(f"{path}: expected 12 budgets, got {budgets}")
    first = df[df.ef_search.astype(int) == budgets[0]].sort_values("query_id")
    labels, censored = [], []
    for _, g in df.groupby("query_id", sort=True):
        y, c = stable_budget(g, budgets)
        labels.append(y); censored.append(c)
    if len(first) != len(labels):
        raise RuntimeError(f"{path}: query alignment mismatch")
    X = np.asarray([first_features(r) for r in first.itertuples()], dtype=float)
    y = np.asarray(labels, dtype=int)
    cens = np.asarray(censored, dtype=bool)
    return df, first, X, y, cens, budgets

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="results/rebuild_portability_recovery")
    args = ap.parse_args()
    base = os.path.join(args.root, "results/cross_index/g1/main/hnswlib")
    os.makedirs(os.path.join(args.root, args.out), exist_ok=True)
    rows = []
    inventory = []
    for dataset in DATASETS:
        paths = sorted(glob.glob(os.path.join(base, f"{dataset}__*.csv.gz")))
        if len(paths) != 9:
            raise RuntimeError(f"{dataset}: expected 9 builds, got {len(paths)}")
        for path in paths:
            df, first, X, y, cens, budgets = load_build(path)
            model = make_pipeline(
                StandardScaler(),
                LogisticRegression(C=1.0, penalty="l2", solver="lbfgs",
                                   max_iter=1000, random_state=SEED)
            )
            split = first.query_split.to_numpy()
            train = split == "cross_index_design"
            cal = split == "cross_index_confirm"
            model.fit(X[train], y[train])
            raw = model.predict(X[cal]).astype(int)
            residual = y[cal] - raw
            shift = int(max(0, residual.max()))
            calibrated = np.minimum(raw + shift, len(budgets) - 1)
            raw_fail = int(np.sum((raw < y[cal]) | cens[cal]))
            calibrated_fail = int(np.sum((calibrated < y[cal]) | cens[cal]))
            n = int(cal.sum())
            name = os.path.basename(path).replace(".csv.gz", "")
            row = {
                "dataset": dataset,
                "implementation": "hnswlib",
                "build": name,
                "n_queries": n,
                "budget_grid": ";".join(map(str, budgets)),
                "censored_queries": int(cens[cal].sum()),
                "censor_rate": float(cens[cal].mean()),
                "raw_underbudget": raw_fail,
                "raw_cp95_upper": cp_upper(raw_fail, n),
                "source_calibration_shift_levels": shift,
                "calibrated_underbudget": calibrated_fail,
                "calibrated_cp95_upper": cp_upper(calibrated_fail, n),
                "mean_raw_budget": float(np.mean([budgets[i] for i in raw])),
                "mean_calibrated_budget": float(np.mean([budgets[i] for i in calibrated])),
                "endpoint_fraction": float(np.mean(calibrated == len(budgets)-1)),
                "source_policy_gate": "PASS" if cp_upper(calibrated_fail, n) <= 0.05 else "FAIL",
                "evidence_label": "EXPLORATORY_DESIGN_SIMULATION",
            }
            rows.append(row)
            inventory.append({"path": os.path.relpath(path, args.root), "rows": int(len(df)),
                              "queries": n, "budgets": budgets})
    out = pd.DataFrame(rows)
    csv_path = os.path.join(args.root, args.out, "source_policy_audit.csv")
    out.to_csv(csv_path, index=False)
    summary = {
        "schema_version": "1.0",
        "seed": SEED,
        "C": 1.0,
        "penalty": "L2",
        "quality_target": TAU,
        "alpha": ALPHA,
        "features": ["log1p_first_exact_ndc", "log1p_first_latency_ns",
                     "log1p_first_kth_distance", "first_second_relative_gap", "max_level"],
        "label": "source minimal stable sufficient budget; censored clipped to endpoint and counted unsafe",
        "source_calibration": "per-source-build maximum observed positive residual; no target labels",
        "builds": len(rows),
        "all_source_gates_pass": bool((out.source_policy_gate == "PASS").all()),
        "failed_builds": out.loc[out.source_policy_gate != "PASS", "build"].tolist(),
        "inventory": inventory,
        "evidence_label": "EXPLORATORY_DESIGN_SIMULATION",
        "validation_dev_accessed": False,
        "formal_test_accessed": False,
    }
    with open(os.path.join(args.root, args.out, "source_policy_summary.json"), "w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
    print(json.dumps(summary, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
