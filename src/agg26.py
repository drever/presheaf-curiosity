import json, statistics as st, random, os
os.environ['SYM'] = '1'
import und, und4
from streets import *
from e19 import load, R, NN
from core import LOG
import numpy as np
und.SYMS = set(range(NLAB)); und4.UND = True
M = {s: json.load(open(f'../results/e26_{s}.json')) for s in range(5)}
none = []
for s in range(5):
    rng = random.Random(500 + s); allw = load('barcelona', rng, 180); te = allw[80:]
    ts = [te] + [load(c, rng, 100) for c in ('madrid', 'zaragoza', 'sevilla')]
    none.append(np.mean([np.mean([len(c.E) * (2 * LOG(c.n) + LOG(R)) for c in t]) for t in ts]))
print('none mean', round(st.mean(none), 1))
names = ['glue', 'grow', 'rp_full', 'rp_prune', 'rp_val', 'rp_prune_val']
for nm in names:
    v = [M[s][nm]['mean'] for s in range(5)]; a = [M[s][nm]['amortised'] for s in range(5)]
    print(f"{nm:13s} k {st.mean(M[s][nm]['k'] for s in range(5)):5.1f} dict {st.mean(M[s][nm]['dict'] for s in range(5)):6.0f}  heldout {st.mean(v):6.1f} (sd {st.stdev(v):4.1f})  amortised100 {st.mean(a):6.1f}")
for base in ['rp_full', 'rp_prune', 'rp_val', 'rp_prune_val']:
    for key in ['mean', 'amortised']:
        d = [M[s][base][key] - M[s]['glue'][key] for s in range(5)]
        print(f"{base} - glue [{key}]: mean {st.mean(d):5.1f} sd {st.stdev(d):4.1f} min {min(d):5.1f} max {max(d):5.1f}")
d = [M[s]['grow']['mean'] - M[s]['glue']['mean'] for s in range(5)]; print('grow-glue heldout', [round(x,1) for x in d], round(st.mean(d),2))
for t in ['barcelona','madrid','zaragoza','sevilla']:
    d=[M[s]['rp_val'][t]-M[s]['glue'][t] for s in range(5)]; print('rp_val-glue',t,round(st.mean(d),1),'min',round(min(d),1))
