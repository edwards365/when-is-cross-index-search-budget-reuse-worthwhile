import csv,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[2]
R=P/"results/icba_cibs_joint_closure"
class TestClosure(unittest.TestCase):
 def rows(self,n): return list(csv.DictReader(open(R/n)))
 def test_actions(self): self.assertEqual(len(self.rows("all_action_geometry.csv")),72)
 def test_datasets(self): self.assertEqual(len({r["dataset"] for r in self.rows("all_action_geometry.csv")}),2)
 def test_bootstrap(self): self.assertTrue(all(r["bootstrap_replicates"]=="5000" for r in self.rows("all_action_geometry.csv")))
 def test_seed(self): self.assertTrue(all(r["bootstrap_seed"]=="991" for r in self.rows("all_action_geometry.csv")))
 def test_p95_upper_gate(self): self.assertTrue(all((r["p95_ci_supported_pass"]=="True")== (float(r["p95_delta_ci_high"])<=0) for r in self.rows("all_action_geometry.csv")))
 def test_crossing_p95_fails(self): self.assertTrue(all(r["p95_ci_supported_pass"]!="True" for r in self.rows("all_action_geometry.csv") if float(r["p95_delta_ci_low"])<0<float(r["p95_delta_ci_high"])))
 def test_eval_ucb_semantics(self): self.assertTrue(all((r["evaluation_risk_wording"]=="INDEPENDENT_RISK_UCB_PASS")== (float(r["evaluation_risk_ucb"])<=.05) for r in self.rows("all_action_geometry.csv")))
 def test_finite(self): self.assertTrue(json.load(open(R/"finite_pool_audit.json"))["cp_ucb_ge_hypergeom_ucb_for_all_x"])
 def test_sift_ci_empty(self): self.assertEqual(sum(r["ci_joint_pass"]=="True" for r in self.rows("joint_feasible_sets.csv") if r["dataset"]=="sift_100k"),0)
 def test_arxiv_ci_empty(self): self.assertEqual(sum(r["ci_joint_pass"]=="True" for r in self.rows("joint_feasible_sets.csv") if r["dataset"]=="arxiv_nomic_100k"),0)
 def test_top1(self): self.assertTrue(all(int(r["drop_top1pct_n"])==5 for r in self.rows("all_action_geometry.csv")))
 def test_qni_closed(self): self.assertTrue(all(r["sentinel_deployable_ci_actions"]=="0" for r in self.rows("cibs_qni_counterfactual.csv")))
 def test_label(self): self.assertEqual(json.load(open(P/"manifests/icba_cibs_joint_closure_decision.json"))["decision_label"],"CIBS_ROUTE_CLOSED_NO_TWO_DATASET_JOINT_FEASIBILITY")
 def test_race(self): self.assertFalse(json.load(open(P/"manifests/icba_cibs_joint_closure_decision.json"))["race_authorized"])
if __name__=="__main__": unittest.main()
