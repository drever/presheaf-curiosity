import sys, os, json, time, random, pickle
from collections import Counter
import netlist; netlist.HB = '/tmp/claude-0/genbench/'
import und
from und import *
from und3 import learn_h
from netlist import *
import merge as M
from e34 import comp_of
und.SYMS = set(); R = 64; NN = 31; maxn = NN + 1
K0 = int(sys.argv[1]) if len(sys.argv) > 1 else 8
L = Labeler(); TESTS = [k for k in (16, 24, 32) if k > K0]; comps = {k: comp_of(f'mul{k}', L) for k in [K0] + TESTS}
cache = f'../results/e35_D0_{K0}.pkl'
if os.path.exists(cache): D0, Lids = pickle.load(open(cache, 'rb')); L.ids = Lids
else:
    rng = random.Random(100); t0 = time.time(); wins = [to_comp(x, rng, NN) for x in windows_from(load_bench(f'mul{K0}'), rng, 40, nmax=20, labeler=L)]
    D0 = learn_h(wins, R, 40, maxn, False, mode='hier', topc=30, maxe=12, objective='hier'); print('D0', len(D0), round(time.time() - t0), 's', flush=True)
    pickle.dump((D0, L.ids), open(cache, 'wb'))
t0 = time.time(); Dfull, recs, P = M.learn_merges(comps[K0], D0, maxe=int(os.environ.get("MAXE", 26)), rounds=8); print('merges', len(recs), round(time.time() - t0, 1), 's', flush=True)
res = {'K0': K0, 'nmerge': len(recs), 'D_edges': [len(p) for p in Dfull]}
for k in [K0] + TESTS:
    t0 = time.time(); inst, raw = cover_u(comps[k], Dfull)
    c = Counter(pi for pi, _, _ in inst)
    res[k] = {'nodes': comps[k].n, 'edges': len(comps[k].E), 'instances': len(inst), 'raw': len(raw), 'by_pattern': {str(pi): [len(Dfull[pi]), n] for pi, n in c.most_common(8)}, 'time': round(time.time() - t0, 1)}
    print(k, res[k], flush=True)
json.dump(res, open(f'../results/e35_{K0}.json', 'w'), default=str)
pickle.dump((Dfull, recs, D0), open(f'../results/e35_cells_{K0}.pkl', 'wb'))
