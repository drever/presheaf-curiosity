import sys, json, time, random, pickle
import und
from und import *
from und3 import learn_h, dict_bits_h
from und4 import *
from netlist import *
NN = 31; maxn = NN + 1; R = 96

def main(n, seed, nmax=16, maxe=16, nte=100):
    und.SYMS = set(); rng = random.Random(500 + seed)
    E, nsup = pickle.load(open('quotient.pkl', 'rb')); L = Labeler()
    # Zeit-/Raumtrennung: Zellen nach Knoten-ID in Trainings- und Testhaelfte? Hier: Fenster zufaellig (ueberlappend), wie bei c6288 -> Einschraenkung dokumentiert
    allw = [to_comp(x, rng, NN) for x in windows_from(E, rng, n + nte, nmax=nmax, emin=6, labeler=L)]
    train, test = allw[:n], allw[n:]
    res = {}
    def ev(nm, D, extra=None, tm=0):
        r = {'k': len(D), 'maxe': max([len(p) for p in D] or [0]), 'train': total_u(train, D, R, maxn, False) / n, 'test': total_u(test, D, R, maxn, False) / len(test), 'time': tm}
        if extra: r.update(extra)
        res[nm] = r; print(seed, nm, {a: (round(b, 1) if not isinstance(b, list) else b) for a, b in r.items()}, flush=True)
    ev('none', [])
    t0 = time.time(); D0 = learn_h(train, R, 40, maxn, False, mode='hier', topc=30, maxe=maxe, objective='hier'); ev('glue_hier', D0, tm=time.time() - t0)
    t0 = time.time(); Dg = learn_h(train, R, 40, maxn, False, mode='grow', topc=30, maxe=maxe, objective='hier'); ev('grow_hier', Dg, tm=time.time() - t0)
    t0 = time.time(); _, F, Dp, Deff, col = learn_prod_auto(train, R, 40, maxn, maxe, D0=D0, minsq=1, fib_maxe=9)
    ev('prod_auto', Deff, {'nfactors': len(F), 'ncolored': len(col), 'factor_edges': sorted(len(f) for f in F)}, time.time() - t0)
    t0 = time.time(); _, F2, Dp2, Deff2, col2 = learn_prod_auto(train, R, 40, maxn, 32, D0=D0, minsq=1, fib_maxe=9, topk=12)
    ev('prod_auto_maxe32', Deff2, {'nfactors': len(F2), 'factor_edges': sorted(len(f) for f in F2), 'k_explicit': len(Dp2)}, time.time() - t0)
    json.dump({'n': n, 'seed': seed, 'nmax': nmax, 'maxe': maxe, 'm': res, 'nlabels': len(L.ids)}, open(f'e23_{n}_{seed}.json', 'w'))
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]))
