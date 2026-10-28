"""Zweite Zellvariante / Rand: 7-Kanten-Muster aus 4m war der Eingangsbus-Stern (Fan-out eines PI). Hier: PI-Kanten (Bus) entfernen, Zelle neu lernen (erwartet AND+FA = 20 Kanten), Rest analysieren."""
import sys, os, json, time, random, pickle
from collections import Counter, defaultdict
import netlist; import paths; netlist.HB = paths.GEN
import und
from und import *
from und3 import learn_h
from netlist import *
from core import Comp, LOG
import merge as M
und.SYMS = set(); R = 64; NN = 31; maxn = NN + 1; K0 = 16; KS = [16, 24, 32]
def Enopi(name): return [e for e in load_bench(name) if e[2][0] != 'IN']
def comp_np(name, L):
    E = Enopi(name); nodes = sorted({x for u, v, _ in E for x in (u, v)}); ix = {x: i for i, x in enumerate(nodes)}
    return Comp(len(nodes), [(ix[u], L(l), ix[v]) for u, v, l in E])
if __name__ == '__main__':
    L = Labeler(); comps = {k: comp_np(f'mul{k}', L) for k in KS}
    cache = '../results/e38_D0.pkl'
    if os.path.exists(cache): D0 = pickle.load(open(cache, 'rb'))
    else:
        rng = random.Random(100); t0 = time.time(); Esrc = Enopi('mul8')
        wins = [to_comp(x, rng, NN) for x in windows_from(Esrc, rng, 40, nmax=20, labeler=L)]
        D0 = learn_h(wins, R, 40, maxn, False, mode='hier', topc=30, maxe=12, objective='hier'); print('D0', len(D0), round(time.time() - t0), 's', flush=True)
        pickle.dump(D0, open(cache, 'wb'))
    t0 = time.time(); Dfull, recs, P = M.learn_merges(comps[K0], D0, maxe=26, rounds=8); print('merges', len(recs), round(time.time() - t0, 1), 's', flush=True)
    res = {}
    for k in KS:
        t0 = time.time(); inst, raw = cover_u(comps[k], Dfull); c = Counter(pi for pi, _, _ in inst)
        res[k] = {'nodes': comps[k].n, 'edges': len(comps[k].E), 'instances': len(inst), 'raw': len(raw), 'by_pattern': {str(pi): [len(Dfull[pi]), n] for pi, n in c.most_common(10)}, 'time': round(time.time() - t0, 1)}
        print(k, res[k], flush=True)
    json.dump(res, open('../results/e38.json', 'w'), default=str); pickle.dump((Dfull, recs, D0), open('../results/e38_cells.pkl', 'wb'))
