import os
SYM = os.environ.get('SYM') == '1'
import und4
import sys, json, time, random
from e19 import *
from und4 import *
def main(n, seed):
    und.SYMS = set(range(NLAB)) if SYM else set(); und4.UND = SYM; rng = random.Random(11 + seed)
    tr_all = load('barcelona', rng, n + 100); train, te_in = tr_all[:n], tr_all[n:]
    tests = {'in:barcelona': te_in}
    for c in ('madrid', 'zaragoza', 'sevilla'): tests[c] = load(c, rng, 100)
    D0 = learn_h(train, R, 40, maxn, SYM, mode='hier', topc=30, maxe=12, objective='hier'); print('D0 done', len(D0), flush=True)
    pure = lambda p: len({r for _, r, _ in p}) == 1
    t0 = time.time(); _, F, Dp, Deff = learn_prod_data(train, R, 40, maxn, 12, cross=None, pure=pure, topk=8, maxf=4)
    print('factors', [(len(f), f[0][1]) for f in F], 'time', round(time.time() - t0), flush=True)
    for nm, D in (('glue', D0), ('prod', Deff)):
        print(nm, len(D), {t: round(total_u(c, D, R, maxn, False) / len(c), 1) for t, c in tests.items()}, 'train', round(total_u(train, D, R, maxn, False) / n, 1), flush=True)
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]))
