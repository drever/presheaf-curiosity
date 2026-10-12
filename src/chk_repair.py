import random, itertools, networkx as nx
from networkx.algorithms.isomorphism import categorical_edge_match
from netlist import *
import und
from repair import *
und.SYMS=set(); rng=random.Random(100); L=Labeler()
ws=[to_comp(x,rng,31) for x in windows_from(load_bench('c6288'),rng,60,nmax=20,labeler=L)]
rules=learn(ws[:40],64,set())
def expand(g):
    fresh=itertools.count(10**6); out=[]
    stack=list(g)
    while stack:
        lab,ns=stack.pop()
        if lab[0]=='t': out.append((lab[1],ns)); continue
        (enc,ext)=rules[lab[1]]; l1,i1,l2,i2=enc
        nv=max(max(i1),max(i2))+1; ei=[i for i,f in enumerate(ext) if f]
        mp={}
        for t,i in enumerate(ei): mp[i]=ns[t]
        for i in range(nv):
            if i not in mp: mp[i]=next(fresh)
        stack.append((l1,tuple(mp[i] for i in i1))); stack.append((l2,tuple(mp[i] for i in i2)))
    return out
def dg(es):
    G=nx.MultiDiGraph()
    for r,(u,v) in es: G.add_edge(u,v,r=r)
    return G
bad=0
for c in ws[40:]:
    a=dg([(r,(u,v)) for _,u,r,v in c.E]); b=dg(expand(compress(c,rules,64,set())))
    if not nx.is_isomorphic(a,b,edge_match=lambda x,y:sorted(d['r'] for d in x.values())==sorted(d['r'] for d in y.values())): bad+=1
print('rules',len(rules),'non-isomorphic after expansion:',bad,'of 20')
