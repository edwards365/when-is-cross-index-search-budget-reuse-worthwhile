import csv, math
from collections import defaultdict
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT=Path("generated_figures"); OUT.mkdir(exist_ok=True)
FONT=ImageFont.load_default(); W,H=960,600; M=(90,55,35,75)

def rows(name): return list(csv.DictReader(open(name,newline="",encoding="utf-8")))
syn=rows("synthetic_grid.csv"); bounds=rows("synthetic_bounds.csv"); endpoints=rows("endpoint_audit.csv"); replay=rows("graph_replay.csv"); costs=rows("cost_break_even.csv"); gates=rows("unified_gate_table.csv")

def save(name,title,xlabel,ylabel,series,kind="line",yrange=None):
    im=Image.new("RGB",(W,H),"white"); d=ImageDraw.Draw(im); l,t,r,b=M; x0,y0=l,H-b; x1,y1=W-r,t
    d.text((l,15),title,fill="black",font=FONT); d.line((x0,y0,x1,y0),fill="black",width=2); d.line((x0,y0,x0,y1),fill="black",width=2)
    allx=[x for _,pts,_ in series for x,y in pts]; ally=[y for _,pts,_ in series for x,y in pts]
    xmin,xmax=min(allx),max(allx); ymin,ymax=(yrange if yrange else (min(ally),max(ally)))
    if xmax==xmin:xmax=xmin+1
    if ymax==ymin:ymax=ymin+1
    sx=lambda x:x0+(x-xmin)/(xmax-xmin)*(x1-x0); sy=lambda y:y0-(y-ymin)/(ymax-ymin)*(y0-y1)
    for i in range(6):
        xv=xmin+(xmax-xmin)*i/5; yv=ymin+(ymax-ymin)*i/5
        d.line((sx(xv),y0,sx(xv),y0+5),fill="black"); d.text((sx(xv)-15,y0+8),f"{xv:.2g}",fill="black",font=FONT)
        d.line((x0-5,sy(yv),x0,sy(yv)),fill="black"); d.text((8,sy(yv)-6),f"{yv:.3g}",fill="black",font=FONT)
    colors=["#2457a7","#b9473f","#2d8557","#8a4ca3","#c17a13","#555555"]
    for idx,(label,pts,shape) in enumerate(series):
        col=colors[idx%len(colors)]; xy=[(sx(x),sy(y)) for x,y in pts]
        if kind=="bar":
            bw=max(5,(x1-x0)/(max(1,len(pts))*len(series)+2)*.7)
            for x,y in xy:d.rectangle((x-bw/2,y,x+bw/2,y0),fill=col)
        else:
            if len(xy)>1:d.line(xy,fill=col,width=3)
            for x,y in xy:d.ellipse((x-4,y-4,x+4,y+4),fill=col)
        d.rectangle((x1-190,t+18*idx,x1-178,t+12+18*idx),fill=col); d.text((x1-172,t+18*idx),label,fill="black",font=FONT)
    d.text(((x0+x1)//2-40,H-25),xlabel,fill="black",font=FONT); d.text((5,25),ylabel,fill="black",font=FONT)
    png=OUT/f"{name}.png"; pdf=OUT/f"{name}.pdf"; im.save(png); im.save(pdf,"PDF",resolution=150)

def mean_by(data,keyx,keyy,flt=lambda x:True):
    z=defaultdict(list)
    for x in data:
        if flt(x):z[float(x[keyx])].append(float(x[keyy]))
    return sorted((k,sum(v)/len(v)) for k,v in z.items())

save("synthetic_tax_vs_tv","Source-only minimax tax vs sentinel separation","Bernoulli separation","Normalized minimax tax",[("exact minimax",mean_by(bounds,"separation","exact_source_minimax",lambda x:x["delta_q"]=="0.05" and x["alpha"]=="0.05"),"o"),("lower bound",mean_by(bounds,"separation","source_lower_bound",lambda x:x["delta_q"]=="0.05" and x["alpha"]=="0.05"),"o")])
save("synthetic_tax_vs_probes","ECSE cost vs sentinel count","Sentinel k","Normalized over-budget cost",[("over-budget",mean_by(syn,"k","over_budget_cost",lambda x:x["delta_q"]=="0.05" and x["alpha"]=="0.05"),"o")])
pts=[(float(x["exact_source_minimax"]),float(x["source_lower_bound"])) for x in bounds if float(x["exact_source_minimax"])>0 and x["delta_q"]=="0.05" and x["alpha"]=="0.05"]
save("lower_bound_vs_exact_minimax","Lower bound vs exact source minimax","Exact minimax","Lower bound",[("cells",pts,"o"),("equality",[(0,0),(max(x for x,y in pts),max(x for x,y in pts))],"-")])
main=[x for x in syn if x["delta_q"]=="0.05" and x["alpha"]=="0.05" and x["k"]=="0"]
pts2=[(float(x["exact_source_minimax"]),float(x["over_budget_cost"])) for x in main]
save("ecse_upper_vs_exact_minimax","Robust-envelope upper cost vs exact minimax","Exact minimax","ECSE over-budget cost",[("cells",pts2,"o")])
save("ambiguity_set_shrinkage","Ambiguity-set shrinkage","Sentinel k","Mean set size",[("all settings",mean_by(syn,"k","ambiguity_size",lambda x:x["delta_q"]=="0.05" and x["alpha"]=="0.05"),"o")])
impls=["hnswlib","faiss","vamana"]; ds=["sift_100k","glove100_100k","arxiv_nomic_100k"]
ser=[]
for j,imp in enumerate(impls):
    pts=[]
    for i,name in enumerate(ds):pts.append((i+0.2*j,sum(x["endpoint_status"]=="CURRENT_ENDPOINT_CERTIFIABLY_SAFE" for x in endpoints if x["implementation"]==imp and x["dataset"]==name)))
    ser.append((imp,pts,"bar"))
save("endpoint_safety_heatmap","Certifiably safe graphs by dataset","Dataset index: 0=SIFT,1=GloVe,2=Arxiv","Safe graphs (of 9)",ser,"bar",(0,9))
ser=[]
for lane in ("CLOSED_WORLD_DESIGN_REPLAY","OPEN_WORLD_DESIGN_SIMULATION"):
    pts=[]
    for i,name in enumerate(ds):
        z=[float(x["under_rate_conservative"]) for x in replay if x["implementation"]=="hnswlib" and x["dataset"]==name and x["lane"]==lane]
        pts.append((i,sum(z)/len(z)))
    ser.append(("closed" if lane.startswith("CLOSED") else "open",pts,"o"))
save("closed_world_vs_open_world","hnswlib closed vs open-world safety","Dataset index","Under-budget rate",ser,yrange=(0,.25))
pts=[]
for i,name in enumerate(ds):
    z=[float(x["break_even_N_search_only"]) for x in costs if x["implementation"]=="hnswlib" and x["dataset"]==name and x["lane"]=="CLOSED_WORLD_DESIGN_REPLAY"]
    pts.append((i,sum(z)/len(z)))
save("cost_break_even","Closed-world hnswlib search-only break-even","Dataset index","Queries N*",[("N*",pts,"bar")],"bar")
status_value={"PASS_WITH_DATASET_BOUNDARY":1,"PASS_RESTRICTED_ALIGNED_RESPONSE_CLASS":1,"PASS_FINITE_CLOSED_WORLD_CLASS":1,"CLOSED_WORLD_PASS_OPEN_WORLD_FAIL":.5,"FAIL":0}
pts=[(i,status_value[x["status"]]) for i,x in enumerate(gates)]
save("unified_gate_heatmap","Unified Gate outcomes","Gate index G0..G4","Pass score",[("status",pts,"bar")],"bar",(0,1))
