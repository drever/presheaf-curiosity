import sys, random, statistics as st
import und
from kg_final import load, sample
from mol_subdue import run_subdue
name=sys.argv[1]; und.SYMS=set()
tr,R=load(name); comps=sample(tr,300,5,random.Random(0)); train=comps[:int(.7*len(comps))]
pats,info=run_subdue(train,20,500,10,4)
ag=[x['agree'] for x in info]; ne=[x['edges'] for x in info]; ni=[x['ninst'] for x in info]
print(name,'Iterationen',len(info),'| Anteil identischer Vorkommen im Mittel %.2f'%st.mean(ag),'| Iterationen mit <1: %d/%d'%(sum(a<0.999 for a in ag),len(ag)),'| Kanten des gew. Musters:',ne,'| Vorkommen:',ni)
print('  Muster-Kanten (nach Normalisierung):',[len(p) for p in pats])
