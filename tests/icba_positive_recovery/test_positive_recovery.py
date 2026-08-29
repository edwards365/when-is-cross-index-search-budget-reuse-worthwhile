import csv,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];RES=ROOT/'results/icba_positive_recovery'
def rows(name):
 with (RES/name).open(newline='') as f:return list(csv.DictReader(f))

def run():
 audit=rows('m0_m1_semantic_audit.csv');assert len(audit)==576;assert all(r['target_shift_zero']=='True' and r['semantic_equal_tolerance_1e_9']=='True' for r in audit)
 b2=rows('b2_true_target_only.csv');assert len(b2)==576;assert {int(r['k']) for r in b2}=={32,64,128,256};assert all(int(r['seed'])==991 for r in b2)
 assert all(r['used_source_shift']=='False' and r['used_history_donors']=='False' and r['used_target_evaluation_for_calibration']=='False' for r in b2)
 assert sum(r['gate_s']=='PASS' for r in b2 if int(r['k'])==256)==144
 b3=rows('b3_history_assisted.csv');assert all(r['looh']=='True' and r['used_history_donors']=='True' and r['used_target_evaluation_for_calibration']=='False' for r in b3)
 top=rows('top1_deletion.csv');assert len(top)==144 and all(r['gate_s']=='PASS' for r in top)
 overlap=rows('query_split_overlap.csv');assert next(r for r in overlap if r['row_set']=='target_sentinel' and r['column_set']=='target_evaluation')['intersection_count']=='0'
 manifest=json.loads((ROOT/'manifests/icba_positive_recovery_decision.json').read_text());assert manifest['decision']=='POSITIVE_MECHANISM_STANDARD_BASELINE_ONLY';assert not manifest['validation_dev_accessed'] and not manifest['formal_test_accessed'];assert not manifest['outer_build_certified']
 required=['query_split_overlap.csv','m0_m1_semantic_audit.csv','b0_raw.csv','b1_source_robust.csv','b2_true_target_only.csv','b3_history_assisted.csv','b5_target_retrain.csv','paired_method_comparison.csv','calibration_cost.csv','break_even.csv','build_cluster_bootstrap.csv','top1_deletion.csv','unified_gate_table.csv']
 assert all((RES/x).stat().st_size>0 for x in required)
 print('POSITIVE_RECOVERY_TEST_PASS')
if __name__=='__main__':run()
