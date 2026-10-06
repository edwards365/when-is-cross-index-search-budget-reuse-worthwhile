"""Reconstruct first-passing labels and Figure 2 clusters from recorded hits."""
import argparse,csv,gzip,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np
from reproduce_paper import need,close,read_csv,write_csv,check_inputs
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    need(not args.output.exists() and not args.output.resolve().is_relative_to(ROOT),'New external output required')
    spec=json.loads((ROOT/'narrative/grid_manifest.json').read_text());raw=args.archive.read_bytes()
    need(len(raw)==spec['bytes'] and hashlib.sha256(raw).hexdigest()==spec['sha256'],'Grid archive identity')
    z=zipfile.ZipFile(io.BytesIO(raw));need(set(z.namelist())==set(spec['members'])|{'source_manifest.json'},'Grid members')
    check_inputs();expected=read_csv(ROOT/'paper/inputs/graph_only_query_clusters.csv');output=[];labels=[]
    args.output.mkdir(parents=True)
    try:
        for impl,display,grid in [('faiss','Faiss HNSW',[16,32,64,128,256,512]),('hnswlib','hnswlib HNSW',[10,20,40,80,120,200])]:
            for ds in ('sift_100k','arxiv_nomic_100k'):
                files=sorted(n for n in spec['members'] if n.startswith(impl+'/'+ds+'__'));need(len(files)==24,'Build count')
                hits=np.full((24,750,6),-1,dtype=np.int8)
                for b,name in enumerate(files):
                    raw=z.read(name);pin=spec['members'][name]
                    need(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'Grid member identity')
                    seen=set()
                    for r in csv.DictReader(io.StringIO(gzip.decompress(raw).decode('utf-8-sig'))):
                        q=int(r['query_id'])
                        if impl=='hnswlib' and (int(r.get('latency_round',0))!=0 or q>=750):continue
                        action=int(r['ef'] if impl=='faiss' else r['ef_search']);a=grid.index(action)
                        need(0<=q<750 and (q,a) not in seen,'Grid duplicate or query range');seen.add((q,a))
                        hit=int(r['hit_count']) if impl=='faiss' else round(float(r['recall_at_10'])*10)
                        need(0<=hit<=10,'Hit count');hits[b,q,a]=hit
                    need(len(seen)==4500,'Complete query-action grid')
                good=hits==10;finite=good.any(axis=2);first=good.argmax(axis=2);action=np.where(finite,first,5)
                absolute=np.zeros(750);reference=np.zeros(750)
                for s in range(24):
                    for t in range(24):
                        if s==t:continue
                        absolute+=~good[t,np.arange(750),action[s]];reference+=~finite[t]
                absolute/=552;reference/=552
                e=sorted((r for r in expected if r['implementation']==display and r['dataset']==ds),key=lambda r:int(r['query_id']))
                need(len(e)==750,'Expected query clusters')
                for q in range(750):
                    for value,key in [(absolute[q],'absolute_pair_mean'),(reference[q],'reference_pair_mean'),(absolute[q]-reference[q],'increment_pair_mean')]:close(float(value),float(e[q][key]),'Raw-to-cluster '+key)
                    distinct=len(set(first[finite[:,q],q].tolist()))
                    labels.append({'implementation':display,'dataset':ds,'query_id':q,'finite_builds':int(finite[:,q].sum()),'distinct_finite_labels':distinct,'finite_variation':distinct>=2})
                group=labels[-750:];count=sum(r['finite_variation'] for r in group)
                output.append({'implementation':display,'dataset':ds,'builds':24,'queries':750,'finite_label_variation_count':count,'finite_label_variation_fraction':count/750,'absolute_risk':float(absolute.mean()),'reference_risk':float(reference.mean()),'incremental_risk':float((absolute-reference).mean())})
        # The two Faiss values delimit the reported 75.87--91.07 percent range.
        faiss={r['dataset']:r for r in output if r['implementation']=='Faiss HNSW'}
        need(faiss['sift_100k']['finite_label_variation_count']==683 and faiss['arxiv_nomic_100k']['finite_label_variation_count']==569,'Reported finite-label endpoints')
        write_csv(args.output/'finite_variation.csv',output);write_csv(args.output/'query_labels.csv',labels)
        (args.output/'verification.json').write_text(json.dumps({'status':'PASS_RAW_RECORD_TO_CLUSTER','groups':4,'query_rows':3000,'raw_build_records':96,'ANN_runs':0,'scope':'First-passing action on finite grid; all 750 queries in denominator; recorded hits not independently recomputed top-k truth'})+'\n')
        print('PASS 96 saved CSVs -> 3000 query clusters and finite-label statistics')
    except Exception as e:
        (args.output/'failure.json').write_text(json.dumps({'error':str(e)})+'\n');raise

if __name__=='__main__':main()
