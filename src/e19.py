import os
SYM = os.environ.get('SYM') == '1'
import und4
import sys, json, time, random
import und
from und import *
from core import Comp
from und3 import learn_h, dict_bits_h
from streets import *
R = NLAB; NN = 40; maxn = NN + 1; MAXE = 24

def load(city, rng, k):
    E = city_graph(city); w = windows(E); rng.shuffle(w); return [to_comp(x, rng, NN) for x in w[:k]]

def main(n, seed, train_city='barcelona', other=('madrid', 'zaragoza', 'sevilla'), K=40):
    und.SYMS = set(range(NLAB)) if SYM else set(); und4.UND = SYM; rng = random.Random(11 + seed)
    tr_all = load(train_city, rng, n + 100); train, te_in = tr_all[:n], tr_all[n:]
    tests = {'in:' + train_city: te_in}
    for c in other: tests[c] = load(c, rng, 100)
    out = {'n': n, 'seed': seed, 'm': {}}
    def ev(nm, D, tm, extra=None):
        r = {'k': len(D), 'time': tm, 'train': total_u(train, D, R, maxn, False) / n}
        for t, comps in tests.items(): r[t] = total_u(comps, D, R, maxn, False) / len(comps)
        if extra: r.update(extra)
        out['m'][nm] = r; print(n, seed, nm, {a: round(b, 1) for a, b in r.items()}, flush=True)
    ev('none', [], 0)
    t0 = time.time(); D0 = learn_h(train, R, K, maxn, SYM, mode='hier', topc=30, maxe=MAXE, objective='hier'); ev('glue_hier', D0, time.time() - t0, {'maxe': max([len(p) for p in D0] or [0])})
    t0 = time.time(); Dg = learn_h(train, R, K, maxn, SYM, mode='grow', topc=30, maxe=MAXE, objective='hier'); ev('grow_hier', Dg, time.time() - t0, {'maxe': max([len(p) for p in Dg] or [0])})
    json.dump(out, open(f'e19_{n}_{seed}' + ('_sym' if SYM else '') + '.json', 'w'))
    return train, D0, tests
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]))
