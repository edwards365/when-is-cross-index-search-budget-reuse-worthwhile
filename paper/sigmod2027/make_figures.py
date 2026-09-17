"""W5.5: deterministic vector figures from frozen W0 summaries, not experiments.

Figure 1: schematic of the versioned-policy question + observed risk/cost tradeoff.
Figure 2: exact primary replay topology, with target roles and conditional fallback.
Figure 3: one cell per completed target decision + descriptive build-level risks.
Final sizes: 7.0 inches wide. PDF embeds fonts; SVG retains editable text.
"""
from pathlib import Path
import csv
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib import font_manager
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'figures'
OUT.mkdir(exist_ok=True)
font_manager.findfont('Times New Roman', fallback_to_default=False)
plt.rcParams.update({'font.family':'Times New Roman', 'font.size':9,
    'axes.titlesize':10, 'axes.labelsize':9, 'xtick.labelsize':8, 'ytick.labelsize':8,
    'pdf.fonttype':42, 'ps.fonttype':42, 'svg.fonttype':'none',
    'axes.spines.top':False, 'axes.spines.right':False, 'savefig.facecolor':'white'})
INK='#203246'; BLUE='#246A91'; TEAL='#227D6C'; ORANGE='#A85421'; GRAY='#68727B'
raw=(ROOT/'evidence/refresh95_per_build.csv').read_bytes()
rows=list(csv.DictReader(raw.decode().splitlines()))
summary=list(csv.DictReader((ROOT/'evidence/refresh95_summary.csv').open()))
datasets=['sift100k','arxiv_nomic_100k']
names=['SIFT-100K','Arxiv-Nomic-100K']
SOURCE='SOURCE_TCP_POOL_REUSE'; TARGET='TARGET_SELECTION_TCP_RECALIBRATION'
END='FIXED_SAFE_NATIVE_ENDPOINT'
seeds=sorted({int(r['seed']) for r in rows})
assert len(rows)==80 and len(seeds)==10

def row(ds,method,seed=None):
    collection=summary if seed is None else rows
    found=[r for r in collection if r['dataset']==ds and r['method']==method
           and (seed is None or int(r['seed'])==seed)]
    assert len(found)==1
    return found[0]

def save(fig,name):
    # Fixed-size canvas: no differing automatic crops across formats.
    for ext in ['pdf','svg','png']:
        fig.savefig(OUT/f'{name}.{ext}',dpi=240,
                    metadata={'Creator':'Reproducible manuscript figure generator'} if ext=='pdf' else None)
        if ext=='svg':
            p=OUT/f'{name}.{ext}'
            p.write_text('\n'.join(line.rstrip() for line in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
    plt.close(fig)

def box(ax,xy,w,h,text,color=BLUE,fill='#F1F6F8',size=9):
    ax.add_patch(FancyBboxPatch(xy,w,h,boxstyle='round,pad=0.008,rounding_size=0.018',
                              facecolor=fill,edgecolor=color,linewidth=.9))
    ax.text(xy[0]+w/2,xy[1]+h/2,text,ha='center',va='center',fontsize=size,color=INK)

def arrow(ax,a,b,color=GRAY,style='-',rad=0):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=9,
                               linewidth=1,color=color,linestyle=style,
                               connectionstyle=f'arc3,rad={rad}'))

def overview():
    fig=plt.figure(figsize=(7,2.5))
    left=fig.add_axes([.015,.10,.44,.79]);left.set(xlim=(0,1),ylim=(0,1));left.axis('off')
    left.text(0,1.03,'(a) A budget policy is tied to an index version',fontweight='bold',fontsize=10)
    points=np.array([[.03,.15],[.18,.02],[.33,.16],[.29,.38],[.08,.41],[.18,.23]])
    for ox,edges,label in [(0,[(0,1),(1,2),(2,3),(3,4),(4,0),(0,5),(3,5)],'Source build'),
                           (.64,[(0,2),(0,4),(4,5),(5,2),(2,3),(3,1),(1,5)],'Target build')]:
        p=points*np.array([.85,.75])+[ox,.45]
        for u,v in edges:left.plot(p[[u,v],0],p[[u,v],1],color=GRAY,lw=1,zorder=1)
        left.scatter(p[:,0],p[:,1],s=18,color=BLUE,zorder=2)
        left.text(ox+.145,.87,label,ha='center',fontsize=10)
    arrow(left,(.34,.67),(.61,.67));left.text(.475,.73,'Refresh +\nrebuild',ha='center',fontsize=8)
    box(left,(.01,.16),.29,.14,'Old query profiles')
    box(left,(.65,.16),.32,.14,'Target execution',TEAL,'#EDF5F1')
    arrow(left,(.30,.23),(.64,.23),ORANGE)
    left.text(.475,.30,'Reuse budget?',ha='center',color=ORANGE,fontsize=9)
    arrow(left,(.14,.46),(.14,.31));arrow(left,(.80,.46),(.80,.31))
    left.text(.49,.02,'Measure risk, certify decisions, account for cost.',ha='center',fontsize=9)
    ax=fig.add_axes([.56,.23,.42,.64])
    ax.set_title('(b) Observed risk–cost tradeoff',loc='left',fontweight='bold',pad=9)
    for ds,color,marker in zip(datasets,[BLUE,ORANGE],['o','s']):
        end=float(row(ds,END)['mean_dists'])
        for method in [END,TARGET,SOURCE]:
            r=row(ds,method);x=100*float(r['evaluation_risk']);y=100*(1-float(r['mean_dists'])/end)
            ax.scatter(x,y,s=34,marker=marker,color=color,edgecolor='white',linewidth=.4,zorder=3)
    ax.axvline(5,color=GRAY,linestyle='--',linewidth=.8)
    ax.text(5.12,8,'5% risk target',rotation=90,fontsize=8,color=GRAY)
    ax.text(.6,7,'Endpoint',fontsize=8)
    ax.text(2.24,40,'Recalibrated',fontsize=8)
    ax.text(5.8,53,'Direct reuse',fontsize=8)
    ax.set(xlim=(0,8.4),ylim=(-4,70),xlabel='Empirical query failure (%)',ylabel='Mean NDC gain (%)')
    ax.set_xticks([0,2,4,6,8]);ax.set_yticks([0,20,40,60]);ax.grid(axis='y',alpha=.18)
    from matplotlib.lines import Line2D
    handles=[Line2D([],[],marker=m,color=c,linestyle='',label=n,markersize=5)
             for m,c,n in zip(['o','s'],[BLUE,ORANGE],names)]
    fig.legend(handles=handles,loc='lower right',bbox_to_anchor=(.995,.0),ncol=2,frameon=False,fontsize=8)
    save(fig,'overview')

def workflow():
    fig,ax=plt.subplots(figsize=(7,2.7));fig.subplots_adjust(left=.01,right=.99,top=.98,bottom=.02)
    ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
    box(ax,(.015,.60),.20,.24,'Nine old-build profiles\n(same query IDs)')
    box(ax,(.28,.60),.20,.24,'History maximum\n+ global grid shift')
    box(ax,(.545,.60),.19,.24,'Frozen candidate\nCP upper bound')
    box(ax,(.80,.60),.18,.24,'Candidate action',TEAL,'#EDF5F1')
    arrow(ax,(.217,.72),(.278,.72));arrow(ax,(.482,.72),(.543,.72))
    arrow(ax,(.736,.72),(.798,.72),TEAL);ax.text(.765,.77,'≤ 5%',ha='center',fontsize=8,color=TEAL)
    box(ax,(.28,.14),.20,.21,'Selection\n500 target queries')
    box(ax,(.545,.14),.19,.21,'Certification\n500 disjoint queries')
    arrow(ax,(.38,.36),(.38,.59));arrow(ax,(.64,.36),(.64,.59))
    box(ax,(.80,.14),.18,.21,'Endpoint fallback\n+ deployment flag',ORANGE,'#FBF2EC',size=8.5)
    arrow(ax,(.74,.59),(.80,.36),ORANGE);ax.text(.79,.46,'> 5%',ha='left',fontsize=8,color=ORANGE)
    ax.text(.105,.30,'Target responses:\nroles stay disjoint',ha='center',va='center',fontsize=9)
    ax.text(.105,.08,'Native search unchanged',ha='center',fontsize=8,color=GRAY)
    # Both completed actions are evaluated, never used to choose the shift.
    ax.text(.89,.95,'Evaluation: 1,000 held-out queries',ha='right',fontsize=9,fontweight='bold')
    arrow(ax,(.89,.85),(.89,.915),TEAL)
    arrow(ax,(.982,.25),(.99,.915),ORANGE)
    ax.text(.50,.015,'Separate endpoint CP check sets the fallback flag; evaluation has no feedback path.',
            ha='center',fontsize=8,color=GRAY)
    save(fig,'workflow')

def decisions():
    fig=plt.figure(figsize=(7,3.45))
    grid=fig.add_axes([.235,.72,.735,.18]);grid.set(xlim=(-.5,9.5),ylim=(1.5,-.5))
    grid.set_yticks([0,1],names);grid.set_xticks(range(10),[str(s) for s in seeds])
    grid.tick_params(length=0,pad=5);grid.spines[:].set_visible(False)
    accepted=0
    for y,ds in enumerate(datasets):
        for x,seed in enumerate(seeds):
            r=row(ds,TARGET,seed);ok=int(r['fallback'])==0 and int(r['certified_deployment'])==1
            accepted+=ok
            grid.add_patch(Rectangle((x-.43,y-.42),.86,.84,facecolor=TEAL if ok else ORANGE,edgecolor='white',lw=.7))
            grid.text(x,y,'A' if ok else 'F',ha='center',va='center',fontsize=9,fontweight='bold',color='white')
    assert accepted==19
    fig.text(.025,.958,'(a) Completed target decisions: 19 accepted candidates, 1 endpoint fallback',fontsize=10,fontweight='bold')
    fig.text(.235,.632,'A = accepted candidate     F = fallback     Columns: registered target-build seeds',fontsize=8.5)
    fig.text(.025,.559,'(b) Direct-reuse failures are spread across builds; recalibration reduces risk',fontsize=10,fontweight='bold')
    for i,(ds,name) in enumerate(zip(datasets,names)):
        ax=fig.add_axes([.09+i*.49,.135,.39,.31])
        for method,col,marker,label in [(SOURCE,ORANGE,'o','Direct reuse'),(TARGET,TEAL,'s','Completed recalibration')]:
            yy=[100*float(row(ds,method,s)['evaluation_risk']) for s in seeds]
            ax.plot(range(10),yy,marker=marker,color=col,ms=3.5,lw=.8,label=label)
        ax.axhline(5,color=GRAY,lw=.8,ls='--')
        ax.set(ylim=(0,9),xlim=(-.4,9.4));ax.set_yticks([0,2,4,6,8])
        ax.set_xticks(range(10),[str(s) for s in seeds],rotation=45,ha='right',fontsize=7)
        ax.set_title(name,fontsize=9,pad=4)
        if i==0:ax.set_ylabel('Empirical failure (%)')
        ax.grid(axis='y',alpha=.15)
    fig.legend(*ax.get_legend_handles_labels(),loc='lower center',bbox_to_anchor=(.53,-.01),ncol=2,frameon=False,fontsize=8)
    save(fig,'target_decisions')

def diagnostics():
    result={'source_baseline':'d0ceb9bafa12480d04d4ae473b4c669e0e5b6ff5',
      'source_path':'results/graph_anns_phase3_ea85/refresh95/per_build.csv',
      'source_canonical_lf_sha256':hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest(),
      'scope':'Descriptive aggregation of frozen rows only; no search, selection or new statistical inference.',
      'datasets':{}}
    macros=[]
    for ds,prefix in zip(datasets,['Sift','Arxiv']):
        ss=[row(ds,SOURCE,s) for s in seeds]
        failures=[int(r['evaluation_failures']) for r in ss]
        assert all(int(r['evaluation_n'])==1000 for r in ss)
        values={'min_risk_percent':min(failures)/10,'max_risk_percent':max(failures)/10,
          'builds_above_5pct':sum(v>50 for v in failures),'total_failures':sum(failures),
          'max_failure_share_percent':100*max(failures)/sum(failures),
          'delete_max_failure_risk_percent':100*(sum(failures)-max(failures))/9000,
          'fallback_seeds':[s for s in seeds if int(row(ds,TARGET,s)['fallback'])]}
        result['datasets'][ds]=values
        for suffix,key in [('MinRisk','min_risk_percent'),('MaxRisk','max_risk_percent'),
                           ('MaxShare','max_failure_share_percent'),('DeleteRisk','delete_max_failure_risk_percent')]:
            macros.append('\\newcommand{\\WFiftyFive'+prefix+suffix+'}{'+f'{values[key]:.2f}'+'}')
    (ROOT/'evidence/w55_diagnostics.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    (ROOT/'evidence/w55_macros.tex').write_text('\n'.join(macros)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    diagnostics();overview();workflow();decisions()
    print('PASS: three source-bound figures, PDF/SVG/PNG; 20 target decisions, 19 acceptances.')
