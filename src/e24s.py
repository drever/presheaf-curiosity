import os, sys, json, time, random
os.environ['SYM'] = '1'
import und4, und, und3
from und import *
from und3 import learn_h
from streets import *
from e19 import load, R, NN, maxn, MAXE
from iface import total_iface, total_old
def main(n, seed, K=40):
    und.SYMS = set(range(NLAB)); und4.UND = True; rng = random.Random(11 + seed)
    tr_all = load('barcelona', rng, n + 100); train, te = tr_all[:n], tr_all[n:]
    tests = {'in': te}
    for c in ('madrid', 'zaragoza', 'sevilla'): tests[c] = load(c, rng, 100)
    res = {}
    def ev(nm, D, tm):
        r = {'k': len(D), 'time': round(tm)}
        for t, c in tests.items():
            r[t + '_old'] = total_old(c, D, R, maxn, False) / len(c); r[t + '_if'] = total_iface(c, D, R, maxn, False) / len(c)
        res[nm] = r; print(seed, nm, {a: round(b, 1) for a, b in r.items()}, flush=True)
    for mode in ('hier', 'grow'):
        t0 = time.time(); D = learn_h(train, R, K, maxn, True, mode=mode, topc=30, maxe=MAXE, objective='hier'); ev({'hier': 'glue', 'grow': 'grow'}[mode], D, time.time() - t0)
    json.dump({'n': n, 'seed': seed, 'm': res}, open(f'../results/e24s_{n}_{seed}.json', 'w'))
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]))
