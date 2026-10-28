import sys, time, random, json, logging
logging.Logger.__call__ = lambda self: self
import und
from und import *
from kg_final import load, sample
from gm_kg import to_nx, pat_edges
from skmine.graph.graphmdl.graph_mdl import GraphMDL
from core import order_pattern, normalize
from mol_big import gspan_mol
from mol_sel import greedy_select
from mol_subdue import run_subdue
name, seed, n, tout = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
und.SYMS=set(); k=5; maxn=6
tr,R=load(name); comps=sample(tr,300,k,random.Random(seed)); cut=int(.7*len(comps)); test=comps[cut:]; train=comps[:n]
out={'name':name,'seed':seed,'n':n,'m':{}}
def ev(nm,D,tm=0):
    out['m'][nm]={'k':len(D),'dict':total_u([],D,R,maxn),'train':total_u(train,D,R,maxn,False)/n,'test':total_u(test,D,R,maxn,False)/len(test),'time':tm}
    print(nm,len(D),round(out['m'][nm]['test'],1),flush=True)
def uniq(ps):
    D=[];s=set()
    for p in ps:
        kk=canon_u(p,True)
        if kk not in s: s.add(kk); D.append(p)
    return D
ev('none',[])
for tc in (30,100):
    t=time.time(); ev(f'hier{tc}',learn_u(train,R,20,maxn,True,mode='hier',topc=tc,maxe=10),time.time()-t)
t=time.time(); ev('grow30',learn_u(train,R,20,maxn,True,mode='grow',topc=30,maxe=10),time.time()-t)
t=time.time(); C,nf=gspan_mol(train,None,max(2,int(.10*n)),8,f'{__import__("tempfile").gettempdir()}/gm_{name}_{seed}_{n}.gsp'); ev('gspan_mdl30',greedy_select(train,C,R,maxn,20,30),time.time()-t)
t=time.time(); pats,_=run_subdue(train,20,500,10,4); tm=time.time()-t; D=uniq(pats)[:20]
trn=[total_u(train,D[:m],R,maxn) for m in range(len(D)+1)]; ns=min(range(len(trn)),key=lambda m:trn[m]); ev('subdue20_mdl',D[:ns],tm)
t=time.time(); g=GraphMDL().fit(to_nx(train)[0],timeout=tout); tm=time.time()-t
D=uniq([tuple(order_pattern(normalize(pat_edges(P)))) for P in g.patterns() if P.number_of_edges()>=2])
out['gm_dl']=[g.initial_description_length(),g.description_length()]; ev('graphmdl',D,tm)
json.dump(out,open(f'gmm_{name}_{seed}_{n}.json','w'))
