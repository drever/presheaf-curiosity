"""E3 Teil 2b: Groessenfamilie eigener Array-Multiplizierer (k=8 Training; k=16, 24 Test). Pipeline wie bei c6288: Fenster -> Muster -> Verklebungsrunden -> Zellen -> Quotient -> Gitterregel."""
import sys, os, json, time, random, pickle
from collections import Counter
import netlist; netlist.HB = '/tmp/claude-0/genbench/'; netlist.HB += ''
import und
from und import *
from und3 import learn_h
from netlist import *
from cells import whole_comp
import cells3
und.SYMS = set(); R = 64; NN = 31; maxn = NN + 1
def comp_of(name, L):
    E = load_bench(name); nodes = sorted({x for u, v, _ in E for x in (u, v)}); ix = {x: i for i, x in enumerate(nodes)}
    return Comp(len(nodes), [(ix[u], L(l), ix[v]) for u, v, l in E])
if __name__ == '__main__':
    k0 = int(sys.argv[1]); L = Labeler()
    for k in (k0, 16, 24): comp_of(f'mul{k}', L)      # gleiche Label-IDs
    comps = {k: comp_of(f'mul{k}', L) for k in (k0, 16, 24)}
    rng = random.Random(100); t0 = time.time()
    wins = [to_comp(x, rng, NN) for x in windows_from(load_bench(f'mul{k0}'), rng, 40, nmax=20, labeler=L)]
    D = learn_h(wins, R, 40, maxn, False, mode='hier', topc=30, maxe=12, objective='hier')
    print('D sizes', sorted([len(p) for p in D], reverse=True), round(time.time() - t0), 's', flush=True)
    for k, c in ([] if os.environ.get('SKIP') else comps.items()):
        inst, raw = cover_u(c, D); print('k', k, 'nodes', c.n, 'edges', len(c.E), 'instances', len(inst), 'raw', len(raw), Counter(len(D[pi]) for pi, _, _ in inst).most_common(5), flush=True)
    comp = comps[k0]
    for rd in range(int(os.environ.get("RDS", 6))):
        t0 = time.time(); p, n_, gain = cells3.merge_round(comp, D, 24, int(os.environ.get("MINC", 4)))
        if p is None: print('no more candidates'); break
        D.append(p); print('round', rd, 'new pattern edges', len(p), 'count', n_, 'gain', round(gain), round(time.time() - t0), 's', flush=True)
    for k, c in comps.items():
        inst, raw = cover_u(c, D); print('final k', k, 'instances', len(inst), 'raw', len(raw), Counter(len(D[pi]) for pi, _, _ in inst).most_common(6), flush=True)
    json.dump({'D': [list(p) for p in D], 'labels': L.ids.__repr__()}, open(f'../results/e34_D{k0}.json', 'w'))
