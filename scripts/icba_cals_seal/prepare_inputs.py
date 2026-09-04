from pathlib import Path
import csv, json, hashlib
root=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
out=root/'results/icba_cals_seal'; out.mkdir(parents=True,exist_ok=True)
selection=list(range(200)); holdout=list(range(200,500))
for name,ids in [('portal_selection_ids.csv',selection),('attainability_holdout_ids.csv',holdout)]:
    with (out/name).open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['query_id']); w.writerows([[x] for x in ids])
with (out/'query_role_ids.csv').open('w',newline='') as f:
    w=csv.writer(f); w.writerow(['query_id','role']); w.writerows([[x,'portal_selection'] for x in selection]); w.writerows([[x,'attainability_holdout'] for x in holdout])
sealed={'portal_selection':selection,'attainability_holdout':holdout,'certification':'SEALED','evaluation':'SEALED','future_confirm':'SEALED','intersection':sorted(set(selection)&set(holdout))}
(out/'sealed_roles.json').write_text(json.dumps(sealed,indent=2))
rules={2266:'native_top_layer',3732:'dataset_medoid',4815:'farthest_from_medoid',991:'fixed_label_991',4177:'fixed_label_4177',46:'high_out_degree',7001:'fixed_label_7001',8888:'fixed_label_8888'}
rows=[]
for p in sorted((root/'results/icba_cals_reaudit').glob('icba_cals_reaudit_registry_*.csv')):
    build_key=p.stem.replace('icba_cals_reaudit_registry_','')
    with p.open() as f:
        for r in csv.DictReader(f):
            internal=int(r['internal_tableint']); rows.append({'portal_rule_id':rules[internal],'portal_external_label':r['external_label'],'portal_internal_tableint':internal,'build_id':build_key})
with (out/'portal_rule_registry.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
for build in sorted({r['build_id'] for r in rows}):
    rr=[r for r in rows if r['build_id']==build]
    with (out/f'portal_registry_{build}.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]); w.writeheader(); w.writerows(rr)
print(len(selection),len(holdout),len(rows))
