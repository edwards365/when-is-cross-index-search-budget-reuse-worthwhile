from pathlib import Path
import subprocess, shutil, json, time
root=Path('/home/wlk/projects/navigation-aware-resistance-hnsw')
out=root/'results/icba_cals_seal'; exe=root/'build/cals_fixed_portal_runner'
datasets={
 'sift':(root/'results/icba_cals_oracle/design_queries_100k.fbin',root/'results/icba_cals_oracle/design_truth_100k.ibin','sift_100k-original'),
 'arxiv':(root/'results/icba_cals_oracle/design_queries_arxiv100k.fbin',root/'results/icba_cals_oracle/design_truth_arxiv100k.ibin','arxiv_nomic_100k-original')}
records=[]
for ds,(queries,truth,prefix) in datasets.items():
 for seed in (7,17,29):
  key=f'{ds}_b{seed}'; index=root/f'results/gate_a/raw/{prefix}-b{seed}/index.bin'; registry=out/f'portal_registry_{key}.csv'
  for role,idfile in [('selection','portal_selection_ids.csv'),('holdout','attainability_holdout_ids.csv')]:
   if shutil.disk_usage(root).free < 5*1024**3: raise SystemExit('INSUFFICIENT_STORAGE_FOR_CALS_SEAL')
   dest=out/f'lanes_{key}_{role}.csv'; cmd=[str(exe),str(index),str(queries),str(truth),str(out/idfile),'8,16,32,64',str(registry),key,str(dest)]
   started=time.time(); subprocess.run(cmd,cwd=root,check=True); records.append({'dataset':ds,'build':key,'role':role,'output':str(dest.relative_to(root)),'seconds':time.time()-started,'command':' '.join(cmd)})
(out/'lane_run_manifest.json').write_text(json.dumps(records,indent=2))
print(json.dumps(records,indent=2))
