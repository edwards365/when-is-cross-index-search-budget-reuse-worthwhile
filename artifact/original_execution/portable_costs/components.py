"""Trace paper cost components to delivered original receipts, without timing."""
import argparse,csv,hashlib,json,math
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROLES=('source_design','target_selection','target_certification')
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_records(root):
    manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8'));records={}
    for key,item in manifest['records'].items():
        p=root/item['file']
        if not p.resolve().is_relative_to(root.resolve()) or p.stat().st_size!=item['bytes'] or digest(p)!=item['delivered_sha256']:raise ValueError('Component receipt identity')
        records[key]=json.loads(p.read_text(encoding='utf-8'),parse_float=Decimal)
    return records
def fixed_components(dataset,records):
    prefix='datasets__'+dataset+'__';truth=records[prefix+'truth_receipt']
    if truth['status']!='EXACT_TRUTH_ACQUIRED_NO_ANN_OUTCOME_ACCESSED':raise ValueError('Truth receipt state')
    profiles=[records[prefix+'profile_finals__'+role] for role in ROLES]
    if any(r['status']!='NATIVE_PROFILES_COMPLETE_AUDIT_PENDING' or r['dataset']!=dataset for r in profiles):raise ValueError('Profile identity')
    audit=records['profile_audit']
    if audit['status']!='PASS_FULL_ORDERED_ID_AND_NATIVE_COUNT_AUDIT':raise ValueError('Independent profile closure')
    if records['decision_lock']['status']!='DECISIONS_LOCKED_BEFORE_EVALUATION_ARRAY_READ':raise ValueError('Decision lock')
    if records['roles_receipt']['status']!='PASS_NEW_ROLE_AND_CONTENT_FIREWALL_BEFORE_OUTCOME':raise ValueError('Role receipt')
    for role,p in zip(ROLES,profiles):
        units=p['profiles']
        if len(units)!=8 or len({u['build'] for u in units})!=8 or any(u['actual_exit_code']!=0 for u in units):raise ValueError('Profile coverage/exit')
        if not any(r['dataset']==dataset and r['role']==role for r in audit['rows']):raise ValueError('Role not independently audited')
    values={
        'design_selection_cert_profile_ns':sum(Decimal(r['whole_unit_ns']) for r in profiles),
        'design_selection_cert_truth_ns':sum(Decimal(truth['roles'][r]['query_read_ns'])+Decimal(truth['roles'][r]['exact_search_ns']) for r in ROLES),
        'exact_base_acquisition_ns':Decimal(truth['exact_base_acquisition_ns']),
        'certification_decision_compute_ns_allocated_half':Decimal(records['decision_lock']['decision_compute_ns_including_audited_array_read'])/2,
        'role_firewall_ns_allocated_half':Decimal(records['roles_receipt']['wall_seconds'])*Decimal(10**9)/2,
    }
    if any(not v.is_finite() or v<0 for v in values.values()):raise ValueError('Invalid component')
    return values
def graph_reload_components(dataset,records):
    prefix='datasets__'+dataset+'__';graphs={k[len(prefix+'graphs__'):]:v for k,v in records.items() if k.startswith(prefix+'graphs__')}
    if len(graphs)!=8:raise ValueError('Eight graphs required')
    rows=[]
    for build,g in graphs.items():
        reloads=[records[prefix+'reloads__'+build+'__'+str(i)] for i in range(3)]
        if sorted(r['rep'] for r in reloads)!=[0,1,2] or any(r['status']!='LOADED_NO_QUERY_ACCESSED' or r['index_sha256']!=g['index_sha256'] for r in reloads):raise ValueError('Reload identity')
        rows.append({'dataset':dataset,'build':build,'operational_build_ns':g['whole_unit_ns'],
            'median_reload_ns':sorted(r['load_index_ns'] for r in reloads)[1],
            'boundary':'Build interfered; reload page cache unknown; common terms cancel only in matched eight-target scenario'})
    return rows
def compare_expected(rows,path):
    with path.open(newline='',encoding='utf-8') as f:expected=list(csv.DictReader(f))
    actual={(r['dataset'],r['component']):float(r['seconds']) for r in rows}
    if len(actual)!=len(rows) or len(expected)!=len(rows):raise ValueError('Component coverage')
    for r in expected:
        value=actual[r['dataset'],r['component']]
        if not math.isclose(value,float(r['seconds']),rel_tol=0,abs_tol=1e-10):raise ValueError('Paper component differs')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists() or not a.output.parent.is_dir():p.error('New output directory and existing parent required')
    records=load_records(HERE);rows=[];graphs=[]
    for dataset in ('sift-1m-heldout','arxiv-nomic-1.34m-heldout'):
        values=fixed_components(dataset,records)
        for name,value in values.items():rows.append({'dataset':dataset,'component':name,'seconds':str(value/Decimal(10**9))})
        rows.append({'dataset':dataset,'component':'fixed_net_setup_total','seconds':str(sum(values.values())/Decimal(10**9))})
        graphs+=graph_reload_components(dataset,records)
    compare_expected(rows,HERE/'expected_fixed_components.csv');a.output.mkdir(mode=0o700)
    with (a.output/'fixed_components.csv').open('x',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['dataset','component','seconds']);w.writeheader();w.writerows(rows)
    report={'status':'ORIGINAL_COMPONENT_RECEIPTS_MATCH_PAPER_FIXED_COMPONENTS','component_rows':len(rows),
        'source_receipts':len(records),'common_graph_terms':graphs,'original_measurements_rerun':False,
        'fixed_cost_interpretation':'Original operational allocation, not minimum unavoidable deployment expenditure',
        'new_adapter_timings_substituted':False,'original_e8':'NOT_ESTIMABLE_UNCHANGED'}
    with (a.output/'verification.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(report['status'])
if __name__=='__main__':main()
