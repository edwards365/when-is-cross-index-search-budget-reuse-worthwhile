#!/usr/bin/env python3
import importlib.util, tempfile
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[2]/"scripts/graph_anns_score8/darth_prepare_sift100k.py"
s=importlib.util.spec_from_file_location("prep",P); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
def ck(n,c):
    if not c: raise AssertionError(n)
    print("PASS ",n)
ck("four_roles",set(m.ROLES)=={"training","validation","certification","testing"})
spans=[set(range(a,z)) for a,z,_ in m.ROLES.values()]
ck("roles_disjoint",all(not spans[i]&spans[j] for i in range(4) for j in range(i)))
ck("base_disjoint",all(min(x)>=100000 for x in spans))
ck("top100",m.TOP==100)
with tempfile.TemporaryDirectory() as d:
 x=np.array([[1.,2.],[3.,4.]],np.float32); p=Path(d)/"x.fvecs"; m.fvecs(p,x)
 raw=np.fromfile(p,np.int32); ck("fvecs_dimension_prefix",raw[0]==2 and raw[3]==2)
ck("heavy_output_data500",str(m.OUT).startswith("/home/wlk/data500/"))
print("6/6 checks passed")
