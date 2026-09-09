import csv, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
RES=ROOT/"results/icba_vamana_preflight"
def test_identical_builds():
 r=list(csv.DictReader((RES/"identical_build_replay.csv").open())); assert len(r)==3 and len({x["index_sha256"] for x in r})==1
def test_id_mapping():
 r=list(csv.DictReader((RES/"id_mapping_audit.csv").open())); assert len(r)==3 and all(x["errors_external_to_internal"]==x["errors_internal_to_external"]=="0" for x in r)
def test_six_budgets(): assert len(list(csv.DictReader((RES/"registered_budget_grid.csv").open())))==6
def test_equivalence():
 r=list(csv.DictReader((RES/"native_save_load_equivalence.csv").open())); assert len(r)==6 and all(all(x[k+"_equal"]=="True" for k in ("recall","mean_cmps","mean_hops","query_recalls","query_cmps","query_hops","result_ids_hash")) for x in r)
def test_environment_nonzero():
 r=list(csv.DictReader((RES/"environment_variable_audit.csv").open())); assert len({x["index_sha256"] for x in r})==3
def test_roles():
 x=json.loads((RES/"query_role_registry.json").read_text()); assert len(x)==4 and sum(v["count"] for v in x.values())==3000
def test_decision():
 x=json.loads((ROOT/"manifests/icba_vamana_preflight_decision.json").read_text()); assert x["decision"]=="READY_FOR_VAMANA_STAGE1" and all(x["gates"].values())
