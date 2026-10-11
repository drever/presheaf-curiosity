import sys, json, time, random
from collections import Counter
import und
from und import *
from und3 import learn_h
from netlist import *
from cells import whole_comp
und.SYMS = set(); R = 64; NN = 31; maxn = NN + 1
comp, nodes, L = whole_comp()
rng = random.Random(100)
Lw = Labeler(); Lw.ids = dict(L.ids)    # gleiche Label-IDs wie beim Gesamtgraph
wins = [to_comp(x, rng, NN) for x in windows_from(load_bench("c6288"), rng, 40, nmax=20, labeler=Lw)]
D = learn_h(wins, R, 40, maxn, False, mode='hier', topc=30, maxe=12, objective='hier')
print('D sizes', sorted([len(p) for p in D], reverse=True), flush=True)
inst, raw = cover_u(comp, D)
print('instances', Counter((pi, len(D[pi])) for pi, _, _ in inst).most_common(12), 'raw edges', len(raw), 'of', len(comp.E), flush=True)
json.dump({'D': [list(p) for p in D]}, open('cells_D1.json', 'w'))
