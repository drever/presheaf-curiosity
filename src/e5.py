import sys, json, time, random
import und
from und import *
from und2 import learn_v
import e2
from e2 import R, maxn, NS, NTEST, P, make_world, gen_comp
variants = {'plain100': lambda tr: learn_u(tr, R, 20, maxn, False, mode='hier', topc=100, maxe=10),
            'plain30': lambda tr: learn_u(tr, R, 20, maxn, False, mode='hier', topc=30, maxe=10),
            'gain30p1': lambda tr: learn_v(tr, R, 20, maxn, False, topc=30, patience=1, prune=False),
            'gain30p3': lambda tr: learn_v(tr, R, 20, maxn, False, topc=30, patience=3, prune=False),
            'gain30p3pr': lambda tr: learn_v(tr, R, 20, maxn, False, topc=30, patience=3, prune=True)}
def main(world, seed):
    und.SYMS = set(); sym = world == 'sym'; rng = random.Random(1000 + seed); perm, motifs, nrel = make_world(rng, sym)
    allc = [gen_comp(rng, perm, motifs, nrel, sym) for _ in range(max(NS) + NTEST)]; test = allc[max(NS):]; out = {'world': world, 'seed': seed, 'res': {}}
    for n in NS:
        res = {}
        for nm, f in variants.items():
            t0 = time.time(); D = f(allc[:n]); res[nm] = {'k': len(D), 'test': total_u(test, D, R, maxn, False) / len(test), 'time': time.time() - t0}
        out['res'][n] = res; print(world, seed, n, {k: (round(v['test'], 1), v['k']) for k, v in res.items()}, flush=True)
    json.dump(out, open(f'e5_{world}_{seed}.json', 'w'))
if __name__ == '__main__': main(sys.argv[1], int(sys.argv[2]))
