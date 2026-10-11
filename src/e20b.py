import os
SYM = os.environ.get('SYM') == '1'
import und4
import sys, json, math, random, time
import und
from und import total_u
from e19 import *
from e19c import uni
from e20 import Model
from und4 import *

def main(n, seed):
    und.SYMS = set(range(NLAB)) if SYM else set(); und4.UND = SYM; rng = random.Random(11 + seed)
    tr_all = load('barcelona', rng, n + 100); train, te_in = tr_all[:n], tr_all[n:]
    tests = {'in:barcelona': te_in}
    for c in ('madrid', 'zaragoza', 'sevilla'): tests[c] = load(c, rng, 100)
    ne = sum(len(c.E) for c in train)
    res = {}
    # A: markiertes Kleben (R=NLAB)
    t0 = time.time(); DA = learn_h(train, R, 40, maxn, SYM, mode='hier', topc=30, maxe=16, objective='hier')
    res['labeled_glue'] = {'dict': dict_bits_h(DA, R, maxn), 'train': total_u(train, DA, R, maxn, False) / n, **{t: total_u(c, DA, R, maxn, False) / len(c) for t, c in tests.items()}}
    # B: Form (R=1) + Beschriftungsmodell
    utr = [uni(c) for c in train]; ute = {t: [uni(c) for c in cs] for t, cs in tests.items()}
    DB = learn_h(utr, 1, 40, maxn, SYM, mode='hier', topc=30, maxe=16, objective='hier')
    for mode in ('iid', 'first'):
        m = Model(mode); m.fit(train)
        pc = m.nparams() * 0.5 * math.log2(ne)
        r = {'dict': dict_bits_h(DB, 1, maxn) + pc, 'label_param_bits': pc, 'train': total_u(utr, DB, 1, maxn, False) / n + m.cost(train)}
        for t in tests: r[t] = total_u(ute[t], DB, 1, maxn, False) / len(ute[t]) + m.cost(tests[t])
        res['shape+label_' + mode] = r
    res['n'] = n; res['seed'] = seed
    for k, v in res.items():
        if isinstance(v, dict): print(seed, k, {a: round(b, 1) for a, b in v.items()}, flush=True)
    json.dump(res, open(f'e20b_{n}_{seed}' + ('_sym' if SYM else '') + '.json', 'w'))
if __name__ == '__main__': main(int(sys.argv[1]), int(sys.argv[2]))
