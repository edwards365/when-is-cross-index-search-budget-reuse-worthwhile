"""Regenerate the paper's six vector figures and evidence-driven TeX tables.

Sources: evidence/w6_audit CSV/NPZ, derived from existing frozen responses.
All quantitative panels retain estimator, unit, and uncertainty in captions.
7-inch figures: overview/workflow/decisions. 3.35-inch figures: tradeoff/tails/cost.
Uses the established W5.5 Matplotlib palette and native vector workflow.
"""
from pathlib import Path
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch,FancyArrowPatch,Rectangle

ROOT=Path(__file__).resolve().parent;E=ROOT/'evidence';D=E/'w6_audit';OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
try:
    font_manager.findfont('Times New Roman',fallback_to_default=False)
    FIGURE_FONT='Times New Roman'
except ValueError:
    FIGURE_FONT='DejaVu Serif'
    print('Times New Roman unavailable: using DejaVu Serif; recheck figure layout.')
plt.rcParams.update({'font.family':FIGURE_FONT,'font.size':9,'axes.titlesize':10,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white'})
BLUE='#246A91';TEAL='#227D6C';ORANGE='#A85421';GRAY='#68727B';INK='#203246'
DS=['sift100k','arxiv_nomic_100k'];NAMES=['SIFT','Arxiv'];COLORS=[BLUE,ORANGE]
def read(n):return list(csv.DictReader((D/n).open(encoding='utf-8')))
S=read('crossed_summary.csv');B=read('certification_per_build.csv');C=read('cost_horizons.csv');G=[r for r in read('graph_only_registry.csv') if r['operator']!='Vamana-style']
def row(ds,lane):return next(r for r in S if r['dataset']==ds and r['lane']==lane)
def val(r,k):return float(r[k])
def interval(r,k,scale=100):return f"{scale*val(r,k):.2f} [{scale*val(r,k+'_ci_low'):.2f}, {scale*val(r,k+'_ci_high'):.2f}]"
def save(fig,name):
    for ext in ['pdf','svg','png']:fig.savefig(OUT/f'{name}.{ext}',dpi=220)
    plt.close(fig)
def box(ax,x,y,w,h,t,fill='#F1F6F8',color=BLUE):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.007,rounding_size=0.02',facecolor=fill,edgecolor=color,lw=.8));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=9,color=INK)
def arrow(ax,a,b):ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=9,color=GRAY,lw=.9))

# Tables are generated from the same numeric records as figures.
rows=[]
for r in G:
    name='SIFT' if r['dataset'].startswith('sift') else 'Arxiv'
    rows.append(f"{r['operator']} & {name} & {100*val(r,'absolute_risk'):.2f} & {100*val(r,'reference_risk'):.2f} & {100*val(r,'incremental_risk'):.2f} [{100*val(r,'ci_low'):.2f}, {100*val(r,'ci_high'):.2f}] & {100*val(r,'finite_variation'):.2f} \\\\")
(E/'graph_only_rows.tex').write_text('\n'.join(rows)+'\n',encoding='utf-8')
rows=[]
for ds,name in zip(DS,NAMES):
    for lane,label in [('end','Endpoint'),('source','Direct reuse'),('legacy','Original recalibration'),('joint','Joint-error replay')]:
        r=row(ds,lane);rows.append(f"{name} & {label} & {interval(r,'risk')} & {interval(r,'gain')} & {val(r,'mean_ndc'):,.0f} & {val(r,'p95_ndc'):,.0f} & {val(r,'p99_ndc'):,.0f} \\\\")
    rows.append('\\addlinespace')
(E/'recovery_rows.tex').write_text('\n'.join(rows)+'\n',encoding='utf-8')
rows=[]
for ds,name in zip(DS,NAMES):
    for scenario,label in [('cached_history','Cached'),('cold_complete_history','Cold')]:
        r=next(r for r in C if r['dataset']==ds and r['lane']=='joint' and r['scenario']==scenario and int(r['N'])==1000000)
        rows.append(f"{name} & {label} & {val(r,'break_even_ratio_of_means')/1000:.0f} [{val(r,'break_even_ci_low')/1000:.0f}, {val(r,'break_even_ci_high')/1000:.0f}] & {r['nonamortizing_builds']}/10 \\\\")
(E/'cost_rows.tex').write_text('\n'.join(rows)+'\n',encoding='utf-8')
rows=[]
for r in B:
    name='S' if r['dataset']==DS[0] else 'A'
    action='C' if int(r['joint_accept']) else 'E'
    rows.append(f"{name} & {r['seed']} & {r['shift']} & {r['candidate_cert_failures']} & {100*val(r,'candidate_ucb_05'):.2f} & {100*val(r,'candidate_ucb_025'):.2f} & {r['endpoint_cert_failures']} & {100*val(r,'endpoint_ucb_025'):.2f} & {action} & {100*val(r,'joint_risk'):.2f} & {100*val(r,'joint_gain'):.2f} \\\\")
(E/'certificate_rows.tex').write_text('\n'.join(rows)+'\n',encoding='utf-8')
rows=[]
for ds,name in zip(DS,NAMES):
    for lane,label in [('legacy','Original'),('joint','Joint')]:
        r=row(ds,lane);rows.append(f"{name} & {label} & [{100*val(r,'gain_ci_low'):.2f}, {100*val(r,'gain_ci_high'):.2f}] & [{100*val(r,'build_only_gain_ci_low'):.2f}, {100*val(r,'build_only_gain_ci_high'):.2f}] & [{100*val(r,'query_only_gain_ci_low'):.2f}, {100*val(r,'query_only_gain_ci_high'):.2f}] \\\\")
(E/'sensitivity_rows.tex').write_text('\n'.join(rows)+'\n',encoding='utf-8')
(E/'w6_macros.tex').write_text('% Derived tables and figures use w6_audit; W0 macros are retained only for historical provenance.\n',encoding='utf-8')
table_macros=[]
for stem,macro in [('graph_only_rows','GraphOnlyRows'),('recovery_rows','RecoveryRows'),('cost_rows','CostRows'),('certificate_rows','CertificateRows'),('sensitivity_rows','SensitivityRows')]:
    table_macros.append('\\newcommand{\\'+macro+'}{%\n'+(E/(stem+'.tex')).read_text(encoding='utf-8')+'}\n')
(E/'generated_tables.tex').write_text(''.join(table_macros),encoding='utf-8')

fig,axs=plt.subplots(1,2,figsize=(7,2.75));fig.subplots_adjust(left=.22,right=.98,bottom=.20,top=.90,wspace=.72)
labels=[]
for i,r in enumerate(G):
    v=100*val(r,'incremental_risk');lo=100*val(r,'ci_low');hi=100*val(r,'ci_high')
    axs[0].errorbar(v,i,xerr=[[v-lo],[hi-v]],fmt='o',color=BLUE if 'hnswlib' in r['operator'] else TEAL,capsize=3)
    labels.append(r['operator'].replace(' HNSW','')+' / '+('SIFT' if r['dataset'].startswith('sift') else 'Arxiv'))
axs[0].set_yticks(range(4),labels);axs[0].invert_yaxis();axs[0].set_xlim(0,27);axs[0].set_xlabel('Additional query failure (pp)');axs[0].set_title('(a) Graph-only responses')
for i,ds in enumerate(DS):
    z=np.load(D/(ds+'_paired_arrays.npz'));rng=np.random.default_rng(991);b,q=z['old_source_risk'].shape
    bw=rng.multinomial(b,np.ones(b)/b,5000)/b;qw=rng.multinomial(q,np.ones(q)/q,5000)/q
    arr=z['old_source_risk'];v=100*arr.mean();dr=np.einsum('ij,ij->i',bw@arr,qw);lo,hi=100*np.quantile(dr,[.025,.975]);x=i-.10
    axs[1].errorbar(x,v,yerr=[[v-lo],[hi-v]],fmt='o',color=COLORS[i],mfc='white',capsize=3)
    r=row(ds,'source');v=100*val(r,'risk');axs[1].errorbar(i+.10,v,yerr=[[v-100*val(r,'risk_ci_low')],[100*val(r,'risk_ci_high')-v]],fmt='s',color=COLORS[i],capsize=3)
axs[1].axhline(5,color=GRAY,ls='--',lw=.8);axs[1].set_xticks([0,1],NAMES);axs[1].set_xlim(-.45,1.45);axs[1].set_ylim(0,10);axs[1].set_ylabel('Query failure (%)');axs[1].set_title('(b) Same policy, changed snapshot');axs[1].text(.5,9.2,'○ Old    ■ Refreshed',ha='center',fontsize=8)
save(fig,'overview')

fig,ax=plt.subplots(figsize=(7,2.55));fig.subplots_adjust(left=.025,right=.98,bottom=.025,top=.98);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
box(ax,.015,.61,.22,.27,'Nine old builds\nSame-query profiles\nMaximum index pool')
box(ax,.315,.61,.24,.27,'500 selection queries\nFirst qualifying global shift')
box(ax,.635,.61,.34,.27,'500 certification queries\nFrozen candidate + endpoint\nUCB checks, fixed action order')
box(ax,.635,.08,.34,.28,'Candidate / endpoint / abstain\n1,000 evaluation queries\nRisk, NDC, tails, cost',color=TEAL)
arrow(ax,(.24,.745),(.31,.745));arrow(ax,(.56,.745),(.63,.745));arrow(ax,(.805,.60),(.805,.37))
ax.text(.02,.43,'Same source-history contract for every role',color=INK,fontsize=9)
ax.text(.02,.22,'Original: αc = αe = 0.05\nJoint-error sensitivity: αc = αe = 0.025\nTarget evaluation never chooses the shift',fontsize=9,color=INK,va='center')
save(fig,'workflow')

fig,axs=plt.subplots(1,2,figsize=(7,1.95));fig.subplots_adjust(left=.08,right=.98,bottom=.31,top=.80,wspace=.22)
seeds=sorted({int(r['seed']) for r in B})
for ax,lane,title in zip(axs,['legacy','joint'],['Original checks','Joint-error sensitivity']):
    for yi,ds in enumerate(DS):
        for xi,s in enumerate(seeds):
            r=next(r for r in B if r['dataset']==ds and int(r['seed'])==s);yes=int(r[lane+'_accept'])
            ax.add_patch(Rectangle((xi-.46,yi-.38),.92,.76,facecolor=TEAL if yes else ORANGE))
            ax.text(xi,yi,'C' if yes else 'E',ha='center',va='center',color='white',fontsize=9)
    ax.set_xlim(-.5,9.5);ax.set_ylim(1.5,-.5);ax.set_xticks(range(10),[str(s) for s in seeds],rotation=55);ax.set_yticks([0,1],NAMES);ax.set_title(title);ax.tick_params(length=0)
    for spine in ax.spines.values():spine.set_visible(False)
save(fig,'decisions')

fig,ax=plt.subplots(figsize=(3.35,2.9));fig.subplots_adjust(left=.17,right=.97,bottom=.17,top=.90)
for ds,col in zip(DS,COLORS):
    for lane,marker in [('source','x'),('legacy','o'),('joint','s')]:
        r=row(ds,lane);x=100*val(r,'gain');y=100*val(r,'risk')
        ax.errorbar(x,y,xerr=[[x-100*val(r,'gain_ci_low')],[100*val(r,'gain_ci_high')-x]],yerr=[[y-100*val(r,'risk_ci_low')],[100*val(r,'risk_ci_high')-y]],fmt=marker,ms=5,mfc='white' if lane=='joint' else col,color=col,elinewidth=.65,capsize=2,alpha=.95)
ax.axhline(5,color=GRAY,ls='--',lw=.8);ax.set(xlim=(0,70),ylim=(0,10),xlabel='Relative mean-NDC reduction (%)',ylabel='Query failure (%)');ax.text(3,9,'SIFT',color=BLUE);ax.text(3,8.1,'Arxiv',color=ORANGE)
save(fig,'tradeoff')

fig,ax=plt.subplots(figsize=(3.35,2.55));fig.subplots_adjust(left=.18,right=.97,bottom=.24,top=.94)
for i,(ds,metric) in enumerate([(d,m) for d in DS for m in ['p95','p99']]):
    rows=[r for r in B if r['dataset']==ds];yy=np.array([val(r,'joint_'+metric)/val(r,'endpoint_'+metric) for r in rows]);xx=np.linspace(i-.14,i+.14,10)
    ax.scatter(xx,yy,s=17,c=BLUE if ds==DS[0] else ORANGE,alpha=.85,edgecolors='white',linewidths=.35)
ax.axhline(1,color=GRAY,ls='--',lw=.8);ax.set_xticks(range(4),['SIFT\np95','SIFT\np99','Arxiv\np95','Arxiv\np99']);ax.set_ylabel('Joint / endpoint tail NDC');ax.set_ylim(.86,1.015);save(fig,'tails')

fig,ax=plt.subplots(figsize=(3.35,2.9));fig.subplots_adjust(left=.20,right=.97,bottom=.20,top=.94)
for ds,col in zip(DS,COLORS):
    for scenario,ls in [('cold_complete_history','-'),('cached_history','--')]:
        rr=[r for r in C if r['dataset']==ds and r['lane']=='joint' and r['scenario']==scenario and int(r['N'])<=1000000]
        xx=np.array([int(r['N']) for r in rr]);yy=np.array([val(r,'net_ndc')/1e6 for r in rr]);ax.plot(xx,yy,ls=ls,c=col,lw=1,marker='o',ms=3)
ax.set_xscale('log');ax.axhline(0,color=GRAY,lw=.8);ax.set_xlabel('Serving query executions');ax.set_ylabel('Net NDC saving (millions)');ax.text(1200,630,'SIFT',color=BLUE);ax.text(1200,530,'Arxiv',color=ORANGE);save(fig,'cost')
print('Generated 6 PDF/SVG/PNG figures and 5 data-linked TeX tables.')
