import numpy as np
import struct
def matrix(p,a):
 a=np.asarray(a,dtype='<f4',order='C')
 with open(p,'wb') as f:f.write(struct.pack('<QQ',*a.shape));a.tofile(f)

def truthbin(p,a):
 a=np.asarray(a,dtype='<u4',order='C')
 with open(p,'wb') as f:f.write(struct.pack('<QQ',*a.shape));a.tofile(f)

def orderbin(p,a):
 with open(p,'wb') as f:f.write(struct.pack('<Q',len(a)));np.asarray(a,dtype='<u4').tofile(f)

def exact(base,q,k=10,batch=16):
 out=np.empty((len(q),k),dtype=np.uint32);bn=np.einsum('ij,ij->i',base,base)
 for s in range(0,len(q),batch):
  z=q[s:s+batch];d=np.einsum('ij,ij->i',z,z)[:,None]+bn[None,:]-2*z@base.T;np.maximum(d,0,out=d)
  ix=np.argpartition(d,k-1,axis=1)[:,:k]
  for i in range(len(z)):out[s+i]=ix[i][np.lexsort((ix[i],d[i,ix[i]]))]
 return out
