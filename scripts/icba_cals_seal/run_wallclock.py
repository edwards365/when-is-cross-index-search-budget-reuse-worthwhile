from pathlib import Path
import subprocess, random, shutil, json, time, pandas as pd
root=Path('/home/wlk/projects/navigation-aware-resistance-hnsw');out=root/'results/icba_cals_seal';exe=root/'build/cals_fixed_portal_runner'
datasets={'sift':(root/'results/icba_cals_oracle/design_queries_100k.fbin',root/'results/icba_cals_oracle/design_truth_100k.ibin','sift_100k-original'),'arxiv':(root/'results/icba_cals_oracle/design_queries_arxiv100k.fbin',root/'results/icba_cals_oracle/design_truth_arxiv100k.ibin','arxiv_nomic_100k-original')}
tasks=[]
for rep in range(5):
 for ds,(queries,truth,prefix) in datasets.items():
  for seed in (7,17,29):
   key=f'{ds}_b{seed}'
   for role,idfile in [('selection','portal_selection_ids.csv'),('holdout','attainability_holdout_ids.csv')]:tasks.append((rep,ds,key,role,queries,truth,root/f'results/gate_a/raw/{prefix}-b{seed}/index.bin',out/f'portal_registry_{key}.csv',out/idfile))
random.Random(991).shuffle(tasks);rows=[]
for rep,ds,key,role,queries,truth,index,registry,idfile in tasks:
 if shutil.disk_usage(root).free<5*1024**3:raise SystemExit('INSUFFICIENT_STORAGE_FOR_CALS_SEAL')
 dest=out/f'wallclock_{key}_{role}_r{rep}.csv';cmd=['taskset','-c','0',str(exe),str(index),str(queries),str(truth),str(idfile),'8,16,32,64',str(registry),key,str(dest)];t=time.time();subprocess.run(cmd,cwd=root,check=True);rows.append({'repeat':rep,'dataset':ds,'build':key,'role':role,'elapsed_s':time.time()-t,'output':dest.name})
pd.DataFrame(rows).to_csv(out/'wallclock_run_manifest.csv',index=False)
print(len(rows))
