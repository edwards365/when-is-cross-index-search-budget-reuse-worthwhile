"""Validate every new timing row, preserving seven-repetition arithmetic means."""
import csv
import hashlib
import json
import struct
from pathlib import Path

FIELDS = ['query_id','query_position','repetition','ef','action_order','wall_ns','cpu_ns','ordered_top10','stop_or_error']

def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''): h.update(block)
    return h.hexdigest()

def pin(p,sha,size=None):
    if digest(p)!=sha or (size is not None and Path(p).stat().st_size!=size):
        raise ValueError('Pinned identity differs: '+Path(p).name)

def write_json(p,value):
    with Path(p).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n')

def query_ids(path):
    data=Path(path).read_bytes()
    if len(data)<24 or data[:8]!=b'E1AQ0001': raise ValueError('Query format')
    n,d=struct.unpack_from('<QQ',data,8)
    if n!=1000 or not 0<d<=4096 or len(data)!=24+n*(8+4*d): raise ValueError('Evaluation query shape/EOF')
    ids=[struct.unpack_from('<q',data,24+i*(8+4*d))[0] for i in range(n)]
    if len(set(ids))!=n: raise ValueError('Duplicate query ID')
    return ids

def reference(path,ids,actions):
    result={}
    with Path(path).open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=['query_id','ef','ndc','topk']: raise ValueError('Reference header')
        for ef in actions:
            for i,q in enumerate(ids):
                row=next(reader,None)
                if row is None or int(row['query_id'])!=q or int(row['ef'])!=ef: raise ValueError('Reference role/action order')
                top=tuple(map(int,row['topk'].split(';')))
                if len(top)!=10 or len(set(top))!=10 or int(row['ndc'])<=0: raise ValueError('Reference top-k/NDC')
                result[(ef,i)]=top
        if next(reader,None) is not None: raise ValueError('Reference trailing rows')
    return result

def validate(path,ids,actions,expected,reps=7):
    import numpy as np
    if len(set(ids))!=len(ids) or list(actions)!=sorted(set(actions)) or reps!=7: raise ValueError('Declared matrix axes')
    shape=(reps,len(actions),len(ids));wall=np.zeros(shape,dtype=np.uint64);cpu=np.zeros_like(wall)
    seen=np.zeros(shape,dtype=bool);order_seen=np.zeros(shape,dtype=bool);position={e:a for a,e in enumerate(actions)}
    rows=0;zero_cpu=0
    with Path(path).open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=FIELDS: raise ValueError('Timing schema')
        for row in reader:
            i=int(row['query_position']);r=int(row['repetition']);ef=int(row['ef']);order=int(row['action_order'])
            if not 0<=i<len(ids) or int(row['query_id'])!=ids[i] or not 0<=r<reps or ef not in position or not 0<=order<len(actions):
                raise ValueError('Timing role/action/repetition')
            a=position[ef]
            if seen[r,a,i] or order_seen[r,order,i] or row['stop_or_error']!='OK': raise ValueError('Duplicate cell/order or stopped row')
            top=tuple(map(int,row['ordered_top10'].split(';')))
            if top!=expected[(ef,i)]: raise ValueError('Ordered IDs differ from pinned profile')
            w=int(row['wall_ns']);c=int(row['cpu_ns'])
            if not 0<w<2**64 or not 0<=c<2**64: raise ValueError('Invalid clock duration')
            wall[r,a,i]=w;cpu[r,a,i]=c;seen[r,a,i]=True;order_seen[r,order,i]=True
            rows+=1;zero_cpu+=int(c==0)
    if rows!=reps*len(actions)*len(ids) or not seen.all() or not order_seen.all(): raise ValueError('Incomplete timing matrix')
    return wall,cpu,{'rows':rows,'zero_process_cpu_cells':zero_cpu,'all_ordered_ids_match':True}

def save_arrays(path,ids,actions,wall,cpu):
    import numpy as np
    with Path(path).open('xb') as f:
        np.savez_compressed(f,query_ids=np.asarray(ids,dtype=np.int64),action_grid=np.asarray(actions,dtype=np.int32),wall_ns=wall,cpu_ns=cpu)

def mean_service(wall,action_indices):
    """One selected action per query; same arithmetic mean over seven repetitions."""
    import numpy as np
    if wall.ndim!=3 or wall.shape[0]!=7: raise ValueError('Seven repetition matrix required')
    actions=np.asarray(action_indices)
    if actions.shape!=(wall.shape[2],) or actions.dtype.kind not in 'iu' or (actions<0).any() or (actions>=wall.shape[1]).any():
        raise ValueError('One valid action index per query required')
    return wall.mean(axis=0)[actions,np.arange(wall.shape[2])]
