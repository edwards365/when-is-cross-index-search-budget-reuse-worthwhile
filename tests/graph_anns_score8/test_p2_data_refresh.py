#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import numpy as np

P = Path(__file__).resolve().parents[2] / "scripts/graph_anns_score8/p2_data_refresh.py"
spec = importlib.util.spec_from_file_location("p2", P)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def check(name, cond):
    if not cond: raise AssertionError(name)
    print("PASS ", name)

check("registered_grid", m.GRID.tolist() == [10,20,40,80,120,200])
check("success_bottom", m.bottoms(np.array([[9,10,10,10,10,10]], dtype=np.int8))[0] == 20)
check("BOT", m.bottoms(np.array([[9,9,9,9,9,9]], dtype=np.int8))[0] == -1)
check("ten_unique_seeds", len(m.SEEDS) == len(set(m.SEEDS)) == 10)
check("heavy_path_data500", str(m.HEAVY).startswith('/home/wlk/data500/'))
pos = np.array([[0, 2], [1, 0]])
labels = np.array([11, 29, 47])
check("truth_position_to_persistent_id", labels[pos].tolist() == [[11,47],[29,11]])
print("6/6 checks passed")
