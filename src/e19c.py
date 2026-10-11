import os
SYM = os.environ.get('SYM') == '1'
import und4
import sys, json, time, random
import e19
from e19 import *
from und4 import *
def uni(c): return Comp(NN, [(a, 0, b) for _, a, r, b in c.E])
def main(n, seed, maxe=16, maxpath=4):
    und.SYMS = set(range(NLAB)) if SYM else set(); und4.UND = SYM; rng = random.Random(11 + seed)
    tr_all = [uni(c) for c in load('barcelona', rng, n + 100)]; train, te_in = tr_all[:n], tr_all[n:]
    tests = {'in:barcelona': te_in}
    for c in ('madrid', 'zaragoza', 'sevilla'): tests[c] = [uni(x) for x in load(c, rng, 100)]
    Rr = 1
    D0 = learn_h(train, Rr, 40, maxn, SYM, mode='hier', topc=30, maxe=maxe, objective='hier'); print('D0', len(D0), max(len(p) for p in D0), flush=True)
    t0 = time.time(); _, F, Dp, Deff = learn_prod_data(train, Rr, 40, maxn, maxe, cross=None, pure=None, topk=maxpath, maxf=maxpath)
    print('factors', [len(f) for f in F], round(time.time() - t0), 's', flush=True)
    res = {}
    for nm, D in (('none', []), ('glue', D0), ('prod', Deff)):
        res[nm] = {t: round(total_u(c, D, Rr, maxn, False) / len(c), 1) for t, c in tests.items()}; res[nm]['train'] = round(total_u(train, D, Rr, maxn, False) / n, 1); res[nm]['k'] = len(D)
        print(nm, res[nm], flush=True)
    json.dump({'n': n, 'seed': seed, 'maxe': maxe, 'factors': [len(f) for f in F], 'm': res}, open(f'e19c_{n}_{seed}' + ('_sym' if SYM else '') + '.json', 'w'))
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]))
