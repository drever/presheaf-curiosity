import sys, time, random, logging
logging.Logger.__call__ = lambda self: self
import und
from und import *
from kg_final import load, sample
from gm_kg import to_nx, pat_edges
from skmine.graph.graphmdl.graph_mdl import GraphMDL
from core import order_pattern, normalize
und.SYMS=set(); k=5; maxn=6
tr,R=load('kinships'); comps=sample(tr,300,k,random.Random(0)); cut=int(.7*len(comps)); test=comps[cut:]
n=int(sys.argv[1]); train=comps[:n]
def ev(nm,D): print(nm,len(D),'test',round(total_u(test,D,R,maxn,False)/len(test),1),'train',round(total_u(train,D,R,maxn,False)/n,1),'dict',round(total_u([],D,R,maxn)),flush=True)
ev('none',[])
for tc in (30,100):
    t=time.time(); D=learn_u(train,R,20,maxn,True,mode='hier',topc=tc,maxe=10); ev(f'hier{tc} ({round(time.time()-t)}s)',D)
t=time.time(); g=GraphMDL().fit(to_nx(train)[0],timeout=float(sys.argv[2])); tm=time.time()-t
D=[];seen=set()
for P in g.patterns():
    E=pat_edges(P)
    if len(E)<2: continue
    pe=tuple(order_pattern(normalize(E))); kk=canon_u(pe,True)
    if kk not in seen: seen.add(kk); D.append(pe)
print('GraphMDL own DL',round(g.initial_description_length()),'->',round(g.description_length()),'time',round(tm))
ev('GraphMDL',D)
