import sys, json, time, random
import und, und3
from und import *
from und3 import learn_h
from netlist import *
from iface import total_iface, total_old
NN = 31; maxn = NN + 1; NMAX = 20
def main(train_circ, n, seed, maxe=12, R=64, K=40):
    kind = 'bench'
    und.SYMS = set(); rng = random.Random(100 + seed)
    L = Labeler()
    def win(nm, k): return [to_comp(x, rng, NN) for x in windows_from(load_bench(nm), rng, k, nmax=NMAX, labeler=L)]
    train = win(train_circ, n)
    tests = {'in': win(train_circ, 100)}
    for c in ['c1355', 'c499', 'c880', 'c1908']: tests[c] = win(c, 100)
    res = {}
    def ev(nm, D, tm):
        r = {'k': len(D), 'time': round(tm)}
        for t, c in tests.items():
            st = []
            r[t + '_old'] = total_old(c, D, R, maxn, False) / len(c); r[t + '_if'] = total_iface(c, D, R, maxn, False, st) / len(c)
            if t == 'in' and st: r['meanV'] = sum(x[0] for x in st) / len(st); r['meank'] = sum(x[1] for x in st) / len(st)
        res[nm] = r; print(seed, nm, {a: round(b, 1) for a, b in r.items()}, flush=True)
    # (1) bisherige Woerterbuecher, nur anders umkodiert
    t0 = time.time(); D0 = learn_h(train, R, K, maxn, False, mode='hier', topc=30, maxe=maxe, objective='hier'); ev('glue', D0, time.time() - t0)
    t0 = time.time(); Dg = learn_h(train, R, K, maxn, False, mode='grow', topc=30, maxe=maxe, objective='hier'); ev('grow', Dg, time.time() - t0)
    # (2) Lerner mit Interface-Ziel
    orig = und3.total_h
    und3.total_h = total_iface
    try:
        t0 = time.time(); D1 = learn_h(train, R, K, maxn, False, mode='hier', topc=30, maxe=maxe, objective='hier'); ev('glue_if', D1, time.time() - t0)
        t0 = time.time(); D2 = learn_h(train, R, K, maxn, False, mode='grow', topc=30, maxe=maxe, objective='hier'); ev('grow_if', D2, time.time() - t0)
    finally: und3.total_h = orig
    json.dump({'train': train_circ, 'n': n, 'seed': seed, 'm': res}, open(f'../results/e24_{train_circ}_{n}_{seed}.json', 'w'))
if __name__ == '__main__': main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
