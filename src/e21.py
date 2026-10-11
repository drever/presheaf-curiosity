import sys, json, time, random
import und
from und import *
from und3 import learn_h, dict_bits_h
from und4 import *
from netlist import *

NN = 31; maxn = NN + 1; NMAX = 20
def main(kind, train_circ, tests_circ, n, seed, maxe=12, R=64):
    und.SYMS = set(); rng = random.Random(100 + seed)
    L = Labeler(); load = load_bench if kind == 'bench' else load_blif
    def win(nm, k): return [to_comp(x, rng, NN) for x in windows_from(load(nm), rng, k, nmax=NMAX, labeler=L)]
    train = win(train_circ, n)
    tests = {'in:' + train_circ: win(train_circ, 100)}
    for c in tests_circ: tests[c] = win(c, 100)
    assert len(L.ids) <= R, len(L.ids)
    res = {}
    def ev(nm, D, extra=None, tm=0):
        r = {'k': len(D), 'maxe': max([len(p) for p in D] or [0]), 'train': total_u(train, D, R, maxn, False) / len(train), 'time': tm}
        for t, c in tests.items(): r[t] = total_u(c, D, R, maxn, False) / len(c)
        if extra: r.update(extra)
        res[nm] = r; print(seed, nm, {a: round(b, 1) for a, b in r.items()}, flush=True)
    ev('none', [])
    t0 = time.time(); D0 = learn_h(train, R, 40, maxn, False, mode='hier', topc=30, maxe=maxe, objective='hier'); ev('glue_hier', D0, tm=time.time() - t0)
    t0 = time.time(); Dg = learn_h(train, R, 40, maxn, False, mode='grow', topc=30, maxe=maxe, objective='hier'); ev('grow_hier', Dg, tm=time.time() - t0)
    t0 = time.time(); _, F, Dp, Deff = learn_prod_data(train, R, 40, maxn, maxe, cross=None, pure=lambda p: len({r for _, r, _ in p}) == 1, topk=8, maxf=4)
    ev('prod_closure', Deff, {'nfactors': len(F)}, time.time() - t0)
    json.dump({'kind': kind, 'train': train_circ, 'n': n, 'seed': seed, 'm': res}, open(f'e21_{train_circ}_{n}_{seed}.json', 'w'))
if __name__ == '__main__':
    kind, tr, n, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    tests = ['c1355', 'c499', 'c880', 'c1908'] if kind == 'bench' else ['adder', 'max', 'sin', 'square']
    tests = [t for t in tests if t != tr]
    main(kind, tr, tests, n, seed)
