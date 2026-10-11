import sys, json, time, random
import und
from und import *
from core import Comp, order_pattern, normalize
from und3 import learn_h, dict_bits_h
from netlist import *

def whole_comp(name='c6288'):
    E = load_bench(name); L = Labeler(); nodes = sorted({x for u, v, _ in E for x in (u, v)}); ix = {x: i for i, x in enumerate(nodes)}
    comp = Comp(len(nodes), [(ix[u], L(l), ix[v]) for u, v, l in E])
    return comp, nodes, L

if __name__ == '__main__':
    und.SYMS = set(); comp, nodes, L = whole_comp(); R = 64; maxn = comp.n + 1
    print('nodes', comp.n, 'edges', len(comp.E), 'labels', L.ids, flush=True)
    t0 = time.time(); D = learn_h([comp], R, int(sys.argv[2]), maxn, False, mode='hier', topc=8, maxe=int(sys.argv[1]), objective='hier')
    print('learned', [len(p) for p in D], round(time.time() - t0), 's', flush=True)
    inst, raw = cover_u(comp, D); from collections import Counter
    print('instances per pattern', Counter(pi for pi, _, _ in inst), 'raw edges', len(raw), flush=True)
    json.dump({'D': [list(p) for p in D]}, open('cells_D.json', 'w'))
