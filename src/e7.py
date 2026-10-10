import sys, json, time, random
import und
from und import *
from und2 import learn_w
from kg_final import load, sample
def main(seed):
    und.SYMS = set(); k = 5; maxn = 6; tr, R = load('kinships'); comps = sample(tr, 300, k, random.Random(seed)); cut = int(.7 * len(comps)); train_all, test = comps[:cut], comps[cut:]
    out = {'seed': seed, 'res': {}}
    for n in (20, 60, 210):
        res = {}
        for nm, kw in (('sub4', dict(maxs=4, use_glue=False)), ('sub4glue', dict(maxs=4, use_glue=True)), ('sub5glue', dict(maxs=5, use_glue=True))):
            if n == 210 and nm == 'sub5glue': continue
            t0 = time.time(); D = learn_w(train_all[:n], R, 20, maxn, False, topc=30, patience=2, **kw)
            res[nm] = {'k': len(D), 'test': total_u(test, D, R, maxn, False) / len(test), 'time': time.time() - t0}
        out['res'][n] = res; print(seed, n, {a: (round(b['test'], 1), b['k'], round(b['time'])) for a, b in res.items()}, flush=True)
        json.dump(out, open(f'e7_{seed}.json', 'w'))
if __name__ == '__main__': main(int(sys.argv[1]))
